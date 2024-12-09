#include <TMC2209.h>
#include <Wire.h>
#include <Arduino.h>
#include "freertos/task.h"
#include <ESP32Encoder.h> 
#include <ESP32Servo.h>
#include "FastAccelStepper.h"

HardwareSerial & serial_stream = Serial2;
FastAccelStepperEngine engine = FastAccelStepperEngine();
FastAccelStepper *stepper = NULL;


const int TX_PIN = 17;
const int RX_PIN = 16;
const int stallGuardPin = 15;
const int enablePin = 19;
const int SERIAL_BAUD_RATE = 115200;
const uint8_t RUN_CURRENT_PERCENT = 100;
const int Apin = 22;
const int Bpin = 4;
const int Zpin = 2;
const int stepPin = 5;
const int dirPin = 18;
long temp_newPosition = 0;
bool home = true;
bool debug = false;
int minMaxVelocity = 80;
int maxEncoderValue = 1100;
int minEncoderValue = 40;
bool encoder_reset = false;
volatile bool motor_enable = false;
volatile bool motor_stall = false;
volatile signed int velocity = 0;
volatile signed int velocity_old = 0;
uint16_t vel_actual = 0;
uint16_t stallguard_result = 0;
TMC2209 stepper_driver;
int serial_int = 0;
float serial_timeout = 10000.0; // milliseconds
float serial_timeout_start = 0.0;
float serial_time_elapsed = 0.0;

// serial comunication receiver task
void serialCommInTask(void * parameter) {
  for (;;) {
    if (Serial.available() > 0) {
      String receivedData = Serial.readStringUntil('\n');
      int separator1 = receivedData.indexOf(',');
      int separator2 = receivedData.indexOf(',', separator1 + 1);
      int separator3 = receivedData.indexOf(',', separator2 + 1);
      serial_time_elapsed = millis(); // sætter et flag for at holde øje med, hvornår der er sidst blevet modtaget data
      stepper_driver.enable();
      motor_enable = true;
      if (separator1 != -1 && separator2 != -1 && separator3 != -1) {
        // Parse values from the received string
        velocity = receivedData.substring(0, separator1).toInt();
        motor_enable = (receivedData.substring(separator1 + 1, separator2).toInt() == 1);
        motor_stall = (receivedData.substring(separator2 + 1).toInt() == 1);
        encoder_reset = (receivedData.substring(separator3 + 1).toInt() == 1);
        /* if (encoder_reset) {
          encoder.setCount(0);} */
          //temp_newPosition = 0;
      }
      //velocity = constrain(velocity, -2000, 2000); // Limit velocity to -2000 to 2000
    }
    if (millis() - serial_time_elapsed > serial_timeout) {
      motor_enable = false;
      stepper_driver.disable();
      velocity = 0;
    } 
    Serial.read(); // Clear the buffer
    vTaskDelay(50 / portTICK_PERIOD_MS); // Serial communication delay
  }
}

// serial communication sender task
void serialCommOutTask(void * parameter) {
  for (;;) {
    Serial.printf("%d,%d,%u,%d,%d,%d\n", stallguard_result, velocity, vel_actual, motor_enable, motor_stall, temp_newPosition);

    vTaskDelay(2500 / portTICK_PERIOD_MS); // Print delay
  }
}

void updateInfoTask(void * parameter) {
for (;;) {
  vel_actual = stepper_driver.getInterstepDuration();
  stallguard_result = stepper_driver.getStallGuardResult();

  vTaskDelay(1000 / portTICK_PERIOD_MS); // Print delay
  }
}

void moveAtVelocity(int velocity) {
  if (velocity == 0) {
    // Stop the motor by writing zero duty cycle
    stepper->stopMove();
    return;}
  
  else if (velocity > 0) {
    // Move the motor forward
    stepper->setSpeedInHz(abs(velocity));
    stepper->runForward();
    
  }
  else if(velocity < 0) {
    // Move the motor backward
    stepper->setSpeedInHz(abs(velocity));
    stepper->runBackward();
  }
  velocity_old = velocity;
 
}

void mainLoop(void * parameter) {
  for (;;) {

    if (motor_enable && !motor_stall) {
      velocity = (velocity > minMaxVelocity) ? minMaxVelocity : (velocity < -minMaxVelocity) ? -minMaxVelocity : velocity; // Limit velocity to -50 to 50
      if (temp_newPosition < minEncoderValue && velocity > 0) {
        velocity = 0;
        stepper->stopMove();
      }
      else if (temp_newPosition > maxEncoderValue && velocity < 0) {
        velocity = 0;
        stepper->stopMove();
      }
      moveAtVelocity(velocity);
      
    }
    else {
      //stepper_driver.moveAtVelocity(0);
      stepper->setSpeedInHz(0);
      stepper->runForward();
    }
    vTaskDelay(50 / portTICK_PERIOD_MS); // Motor control delay
  }
}

void setup() {
  pinMode(stallGuardPin, INPUT);
  pinMode(Apin, INPUT);
  pinMode(Bpin, INPUT);
  pinMode(Zpin, INPUT);
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);
 
  engine.init();
  stepper = engine.stepperConnectToPin(stepPin);
  if (stepper) {
    stepper->setDirectionPin(dirPin);
    stepper->setEnablePin(enablePin);
    stepper->setAutoEnable(true);

    stepper->setSpeedInHz(100);       // 500 steps/s
    stepper->setAcceleration(4000);    // 100 steps/s²
    //stepper->runForward();
    stepper->setLinearAcceleration(20);
    stepper->attachToPulseCounter(QUEUES_MCPWM_PCNT, 0, 0);
    stepper->clearPulseCounter();
  }

  pinMode(enablePin, OUTPUT);
  Serial.setRxBufferSize(200);
  Serial.begin(115200);

  stepper_driver.setup(serial_stream);
  stepper_driver.setHardwareEnablePin(enablePin);
  stepper_driver.enable();
  motor_enable = true;

  stepper_driver.setMicrostepsPerStep(0);
  stepper_driver.disableStealthChop();
  stepper_driver.setRunCurrent(RUN_CURRENT_PERCENT);
  stepper_driver.setHoldCurrent(50);
  stepper_driver.setMicrostepsPerStep(0);
  stepper_driver.disableCoolStep();
  stepper_driver.setStallGuardThreshold(0);
 

  xTaskCreatePinnedToCore(mainLoop, "MainLoopTask", 4096, NULL, 1, NULL, 0);
  xTaskCreatePinnedToCore(serialCommOutTask, "serialCommOutTaskTask", 4096, NULL, 2, NULL, 1);
  xTaskCreatePinnedToCore(serialCommInTask, "serialCommInTask", 4096, NULL, 1, NULL, 1);
  xTaskCreatePinnedToCore(updateInfoTask, "updateInfoTask", 4096, NULL, 1, NULL, 1);

}



void loop() {
  // Empty loop as tasks are running independently
}