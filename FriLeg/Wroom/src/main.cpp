#include <TMC2209.h>
#include <Wire.h>
#include <Arduino.h>
#include "freertos/task.h"
#include <WiFi.h>
#include <WiFiClient.h>

const char *ssid = "ESP32_Hotspot";
const char *password = "12345678";
IPAddress local_ip(192, 168, 4, 22);
IPAddress gateway(192, 168, 4, 9);
IPAddress subnet(255, 255, 255, 0);

WiFiServer server(80);

HardwareSerial &serial_stream = Serial1;
const int TX_PIN = 1;
const int RX_PIN = 3;
const int stallGuardPin = 5;
const int SERIAL_BAUD_RATE = 115200;
const uint8_t RUN_CURRENT_PERCENT = 50  ;

TMC2209 stepper_driver;
int velocity = 400;

void setupWiFi() {
  WiFi.softAP(ssid, password);
  WiFi.softAPConfig(local_ip, gateway, subnet);
  server.begin();
}

#define MESSAGE_BUFFER_SIZE 10
String messageBuffer[MESSAGE_BUFFER_SIZE];
int messageIndex = 0;

// Function to add messages to the buffer
void addMessageToBuffer(const String& message) {
  messageBuffer[messageIndex] = message;
  messageIndex = (messageIndex + 1) % MESSAGE_BUFFER_SIZE;  // Circular buffer
}


void checkForIncomingMessages(void * parameter) {
  bool clientConnected = false;
  WiFiClient client;

  for (;;) {
    if (!client || !client.connected()) {
      client = server.available();
      if (client) {
        clientConnected = true;
      }
    }

    if (clientConnected && client.connected() && client.available()) {
      // Read the incoming message up to the newline character
      String message = client.readStringUntil('\n');
      message.trim();  // Trim any extra whitespace or newline characters

      // Store the received message for /debug page
      addMessageToBuffer("Received: " + message);

      // Process the message to update the velocity if it’s a valid number
      int newVelocity = message.toInt(); 
      if (newVelocity != NULL) {  // Handle "0" as a valid input
        velocity = newVelocity;
        addMessageToBuffer("Velocity updated to: " + String(velocity));
      }
      client.flush();  // Clear the buffer
    }

    vTaskDelay(100 / portTICK_PERIOD_MS);  // Adjusted delay for message checking
  }
}

bool stallGuardTriggered=false;

void mainLoop(void * parameter) {
  for (;;) {
    if (stallGuardTriggered) {
      stepper_driver.moveAtVelocity(0);
      if (millis() - stallGuardTimer > 1000 && stallGuardTimer != 0) {
        stallGuardTriggered = false;
        //stepper_driver.moveAtVelocity(velocity);
      }
    }
    else {
      stepper_driver.moveAtVelocity(velocity);
    }
    vTaskDelay(10 / portTICK_PERIOD_MS); // Motor control delay
  }
}
float stallGuardTimer = 0;
void interruptHandler() {
  stallGuardTriggered = true;
  stallGuardTimer = millis();
  
  
  // Clear the interrupt
  detachInterrupt(digitalPinToInterrupt(stallGuardPin));
  attachInterrupt(digitalPinToInterrupt(stallGuardPin), interruptHandler, RISING);


}

void setup() {
  setupWiFi();
  
  stepper_driver.setup(serial_stream, SERIAL_BAUD_RATE, TMC2209::SERIAL_ADDRESS_0, RX_PIN, TX_PIN);
  attachInterrupt(digitalPinToInterrupt(stallGuardPin), interruptHandler, RISING);
  stepper_driver.setStallGuardThreshold(2);
  stepper_driver.setMicrostepsPerStep(8);
  stepper_driver.setRunCurrent(RUN_CURRENT_PERCENT);
  stepper_driver.enableCoolStep();
  stepper_driver.enable();

  xTaskCreate(checkForIncomingMessages, "WiFiTask", 4096, NULL, 1, NULL);
  xTaskCreate(mainLoop, "MainLoopTask", 4096, NULL, 1, NULL);
}

void loop() {
  // Empty loop as tasks are running independently
}
