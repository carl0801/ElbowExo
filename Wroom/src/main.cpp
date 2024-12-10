#include <algorithm>
#include <TMC2209.h>
#include <Wire.h>
#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include "freertos/task.h"
#include <ESP32Encoder.h> 
#include "FastAccelStepper.h"
#include <soc/pcnt_struct.h>
#include <cstring>


#define tmc2209_connected false
#define debug false

FastAccelStepperEngine engine = FastAccelStepperEngine();
FastAccelStepper *stepper = NULL;

//ESP32PWM stepper;
ESP32Encoder encoder_dummy; // dummy encoder which will share pcnt with fastAccelStepper
ESP32Encoder encoder; // real encoder which will be bumped to a different pcnt unit
// watchdog timer for encoder loop
extern bool loopTaskWDTEnabled;
extern TaskHandle_t loopTaskHandle;

// start and end bytes for serial communication packets
#define STARTBYTE 0x8e
#define ENDBYTE 0x0a
// types of payload in packets
#define INFO_TYPE uint8_t
#define VEL_TYPE int16_t 
#define POS_TYPE int64_t



// Binary serial communication struct
struct SerialData {
  INFO_TYPE info = 0;
  VEL_TYPE velocity = 0.0;
  POS_TYPE position = 0.0;
};

//volatile SerialData request;
//volatile SerialData out;


#ifndef tmc2209_connected

HardwareSerial & serial_stream = Serial2;

// TMC2209 variables
const int TX_PIN = 17;
const int RX_PIN = 16;
const int stallGuardPin = 15;
const uint8_t RUN_CURRENT_PERCENT = 100;
uint16_t vel_actual = 0;
uint16_t stallguard_result = 0;
TMC2209 stepper_driver;
volatile bool motor_stall = false;

// IRAM_ATTR interrupt handler
void IRAM_ATTR handleInterrupt() {
  motor_stall = true;
}

#endif

// Stepper motor variables
const int enablePin = 19;
const int stepPin = 5;
const int dirPin = 18;

// Encoder variables
const int Apin = 22;
const int Bpin = 4;
const int Zpin = 21;
//bool home = false; // whether motor is homed
//bool encoder_reset = false;
int64_t max_limit = 1100; // Max position soft limit
int64_t min_limit = 100; // Min position soft limit
int64_t position = 0; // Current position
int64_t new_position = 0; // New position
int64_t max_encoder_count = 4096; // Max encoder count
int8_t encoder_revs = 0; // Number of encoder revolutions

bool encoder_reset = false; // Reset encoder position


// Motor requests variables
volatile bool motor_enable = false;
bool motor_stall = false;
bool trespassing = false;
int max_velocity = 80;

volatile int16_t velocity = 0;
int16_t* vel_ptr = 0;

// Serial communication variables
const int SERIAL_BAUD_RATE = 460800;
bool ack = false; // Acknowledgement flag
bool to_ack = false; // Flag to send ack
bool send = false; // Flag to send data

// in and out packet sizes and indices
uint8_t packet[sizeof(INFO_TYPE) + sizeof(VEL_TYPE) + sizeof(POS_TYPE) + 2]; // packet of size begin+payload+end
uint8_t request[sizeof(INFO_TYPE) + sizeof(VEL_TYPE) + 2]; // size of start+payload+end
uint8_t ack_pack[3] = {STARTBYTE, 0x01, ENDBYTE}; // ack packet
uint8_t velocity_index = 1 + sizeof(INFO_TYPE);
uint8_t position_index = 1 + sizeof(INFO_TYPE) + sizeof(VEL_TYPE);

// serial timeout variables
uint16_t serial_timeout_cycles = 10000;
uint16_t serial_cycles = 0;
bool serial_timeout_flag = false;
uint16_t bad_packets = 0;
uint16_t bad_packet_limit = 10;


// Task handle for the serial communication task
TaskHandle_t serialInTaskHandle = NULL;
TaskHandle_t serialOutTaskHandle = NULL;
TaskHandle_t sendAckTaskHandle = NULL;
TaskHandle_t stopSendTaskHandle = NULL;
TaskHandle_t sendDataTaskHandle = NULL;
TaskHandle_t setVelocityTaskHandle = NULL;
TaskHandle_t motorMoveTaskHandle = NULL;
TaskHandle_t motorMonitorTaskHandle = NULL;

// ISR for serial data available
void IRAM_ATTR onSerialData() {
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    vTaskNotifyGiveFromISR(serialInTaskHandle, &xHigherPriorityTaskWoken);
    portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
}



// 1st byte: info (8 bits) - (0?no_ack:ack) (0?nodata:data) (0?motor_enable) (0?encoder_reset) (0?reserved) (0?reserved) (0?reserved) (0?reserved)

// Serial communication receiver task (struct)
void serialCommInTask(void * parameter) {
  for (;;) {
    // Wait for notification from ISR
    ulTaskNotifyTake(pdTRUE, pdMS_TO_TICKS(portMAX_DELAY));
    // wait 2ms for the rest of the packet
    vTaskDelay(2 / portTICK_PERIOD_MS);
    if (Serial.available() >= 3) {
      Serial.readBytesUntil(ENDBYTE, request, sizeof(request));
      if (request[0] == STARTBYTE) {
        if (bitRead(request[1], 0)) {
          // if the packet is an acknowledgement packet
          ack = true;
          send = false;
          xTaskNotifyGive(stopSendTaskHandle);
        }
        else {
          if (bitRead(request[1], 1)) { 
            // if the packet is a data packet
            // use pointer reinterpretation to get the velocity
            vel_ptr = reinterpret_cast<VEL_TYPE*>(&request[0]);

            // notify setVelocityTask to update the velocity
            xTaskNotifyGive(setVelocityTaskHandle);

            // set both ack and send flags to true to indicate we need to send an ack
            ack = true;
            send = true;
          }
          else {
            // if packet is not ack, and not data, then it is asking for data
            ack = false;
            send = true;
          }
         xTaskNotifyGive(serialOutTaskHandle);
        }
        // Debug output (optional, for verification)
        #ifndef debug
        Serial.printf("Received: (%d, %d, %d, %d), velocity: %d\n", request_header[0], request_header[1], request_header[2], request_header[3], velocity);
        #endif
        // Reset timeout flag
        serial_timeout_flag = false;
        serial_cycles = 0;
        bad_packets = 0;
        }
      else {
        bad_packets++;
      }
    }
    else {
        // increment cycle timeout counter
        serial_cycles++;
      }
      // Timeout handling
      if (serial_cycles > serial_timeout_cycles) {
        serial_timeout_flag = true;
      }
      if (bad_packets > bad_packet_limit) {
        // Reset the serial port
        Serial.end();
        Serial.begin(SERIAL_BAUD_RATE);
        bad_packets = 0;
        #ifndef debug
        Serial.println("Serial reset");
        #endif
      }
  }
}

// serial communication sender task (struct)
void serialCommOutTask(void * parameter) {
  for (;;) {
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
    if (send) {
      if (ack) {
        Serial.write(ack_pack, 3);
        ack = false;
      }
      else {
        vTaskResume(sendDataTaskHandle);
      }
    }
  }
}

void stopSendTask(void * parameter) {
  for (;;) {
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
    if (!send && ack) {
      vTaskSuspend(sendDataTaskHandle);
    }
  }
}

void createPacket(uint8_t * packet) {
    packet[0] = STARTBYTE;
    std::memcpy(packet + 1, const_cast<const int16_t*>(&velocity), sizeof(VEL_TYPE));
    std::memcpy(packet + 1 + sizeof(VEL_TYPE), &position, sizeof(POS_TYPE));
    packet[sizeof(VEL_TYPE) + sizeof(POS_TYPE) + 1] = ENDBYTE;
}

void sendDataTask(void * parameter) {
  for (;;) {
    if (send && !ack) {
        createPacket(packet);
        Serial.write(packet, sizeof(packet));
      }
    }
    vTaskDelay(100 / portTICK_PERIOD_MS); // Serial communication delay
  }

void setVelocityTask(void * parameter) {
  for (;;) {
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
    // dereference the pointer to get the velocity
    velocity = *vel_ptr;
    // Limit velocity to -50 to 50
    velocity = (velocity > max_velocity
    ) ? max_velocity
     : (velocity < -max_velocity
    ) ? -max_velocity
     : velocity; 
     // notify the motor move task to update the velocity
    xTaskNotifyGive(motorMoveTaskHandle);
  }
}

// encoder task
void encoderTask(void * parameter) {
  for (;;) {
    if (encoder_reset) {
      encoder.setCount(0);
      position = 0;
      encoder_reset = false;
    }
    else {
      position = encoder.getCount();
    }
    vTaskDelay(20 / portTICK_PERIOD_MS); // Encoder update delay
  }
}

void motorMonitorTask(void * parameter) {
  for (;;) {
    if ((position <= min_limit && velocity > 0) || (position >= max_limit && velocity < 0)) {
      trespassing = true;
    }
    else {
      trespassing = false;
    }
    if ((trespassing || motor_stall || !motor_enable) && velocity != 0) {
      stepper->setEnablePin(enablePin, false);
      motor_enable = false;
      xTaskNotifyGive(motorMoveTaskHandle);
    }
    vTaskDelay(5 / portTICK_PERIOD_MS); // Motor monitor delay
  }
}

// motor requests task
void motorMoveTask(void * parameter) {
  for (;;) {
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
    if (motor_enable && !motor_stall && !trespassing) {
      if (position < min_limit && velocity > 0) {
        velocity = 0;
        stepper->stopMove();
      }
      else if (position > max_limit && velocity < 0) {
        velocity = 0;
        stepper->stopMove();
      }
      else {
        stepper->setSpeedInHz(abs(velocity));
        if (velocity > 0) {
          stepper->runForward();
        }
        else if (velocity < 0) {
          stepper->runBackward();
        }
      }
    }
    else {
      stepper->setSpeedInHz(0);
      stepper->stopMove();
    }
  }
}

#ifndef tmc2209_connected

SerialData serialParseString(String receivedData) {
  int separator1 = receivedData.indexOf(',');
  int separator2 = receivedData.indexOf(',', separator1 + 1);
  int separator3 = receivedData.indexOf(',', separator2 + 1);
  if (separator1 != -1 && separator2 != -1 && separator3 != -1) {
    // Parse values from the received string
    velocity = receivedData.substring(0, separator1).toInt();
    motor_enable = (receivedData.substring(separator1 + 1, separator2).toInt() == 1);
    motor_stall = (receivedData.substring(separator2 + 1).toInt() == 1);
    encoder_reset = (receivedData.substring(separator3 + 1).toInt() == 1);
    
    SerialData parsedData = {1};
    parsedData.velocity = velocity;
    parsedData.motor_enable = motor_enable;
    parsedData.motor_stall = motor_stall;
    parsedData.encoder_reset = encoder_reset;

    return parsedData;
}

// serial comunication receiver task
void serialCommInTask(void * parameter) {
  for (;;) {
    if (Serial.available() > 0) {
      String receivedData = Serial.readStringUntil('\n');
      serial_time_elapsed = millis();
      SerialData parsedData = serialParseString(receivedData);
      stepper_driver.enable();
      motor_enable = true;
        velocity = parsedData.velocity;
        motor_enable = parsedData.motor_enable;
        motor_stall = parsedData.motor_stall;
        encoder_reset = parsedData.encoder_reset;
        /* if (encoder_reset) {
          encoder.setCount(0);} */
          //position = 0;
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
    Serial.printf("z,%d,%d,%d,%d\n", velocity, motor_enable, motor_stall, position);

    vTaskDelay(500 / portTICK_PERIOD_MS); // Print delay
  }
}

void updateInfoTask(void * parameter) {
for (;;) {
  vel_actual = stepper_driver.getInterstepDuration();
  stallguard_result = stepper_driver.getStallGuardResult();

  vTaskDelay(1000 / portTICK_PERIOD_MS); // Print delay
  }
}

void mainLoop(void * parameter) {
  for (;;) {

    if (motor_enable && !motor_stall) {
      velocity = (velocity > max_velocity
    ) ? max_velocity
     : (velocity < -max_velocity
    ) ? -max_velocity
     : velocity; // Limit velocity to -50 to 50
      if (position < min_limit && velocity > 0) {
        velocity = 0;
        stepper->stopMove();
      }
      else if (position > max_limit && velocity < 0) {
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
    vTaskDelay(50 / portTICK_PERIOD_MS); // Motor requests delay
  }
}



void encoderTask(void * parameter) {
  for (;;) {
    new_position = int32_t(encoder.getCount());
    if (new_position != position) {
      //Serial.printf("Position: %ld\n", new_position);
      position = new_position;
    }

    // vi kan nemt tilføje Z-pin her, hvis vi vil have en taeller for hver omdrejning

    vTaskDelay(25 / portTICK_PERIOD_MS); // Encoder update delay
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

#endif

void setup() {

  // CPU frequency
  setCpuFrequencyMhz(240);

  pinMode(Zpin, INPUT);
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);
  pinMode(enablePin, OUTPUT);

  // led pin
  //pinMode(2, OUTPUT);
 
  // Serial communication setup
  Serial.setRxBufferSize(64);
  Serial.setTxBufferSize(64);
  Serial.begin(115200);


  // Stepper setup
  engine.init();
  stepper = engine.stepperConnectToPin(stepPin);
  if (stepper) {
    stepper->attachToPulseCounter(PCNT_UNIT_7, 0, 0);
    stepper->setDirectionPin(dirPin);
    stepper->setEnablePin(enablePin);
    stepper->setAutoEnable(true);

    stepper->setSpeedInHz(100);       // steps/s
    stepper->setAcceleration(1000);    // steps/s²


    stepper->clearPulseCounter();
    //stepper->addQueueEntry(&cmd_step1);
  }
  

  // Encoder Setup
  ESP32Encoder::useInternalWeakPullResistors = puType::up;
  encoder_dummy.attachSingleEdge(32, 33);
  encoder.attachSingleEdge(Apin, Bpin);
  encoder.clearCount();
  encoder.setFilter(1023);
  //loopTaskWDTEnabled = true;
  //esp_task_wdt_add(loopTaskHandle);


  #ifndef tmc2209_connected

  // Set stalled motor flag with function stored in IRAM
  attachInterrupt(digitalPinToInterrupt(stallGuardPin), handleInterrupt, RISING);

  // TMC2209 driver (uart) setup
  pinMode(stallGuardPin, INPUT);
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
  
  xTaskCreatePinnedToCore(updateInfoTask, "updateInfoTask", 4096, NULL, 1, NULL, 1);
  xTaskCreate(checkMotorStalled, "CheckMotorStalledTask", 4096, NULL, 1, NULL);

  #endif

  // Delay to ensure all systems are ready
  delay(200);
  printf("pcnt modules available: %d\n", PCNT_UNIT_MAX);
  printf("encoder pcnt unit: %d\n", encoder.unit);
  printf("stepper pcnt unit: %d\n", stepper->pulseCounterAttached());


  xTaskCreate(serialCommOutTask, "serialCommOutTask", 4096, NULL, 1, &serialOutTaskHandle);
  xTaskCreate(serialCommInTask, "serialCommInTask", 4096, NULL, 1, &serialInTaskHandle);
  xTaskCreate(encoderTask, "encoderTask", 4096, NULL, 2, NULL);
  xTaskCreate(motorMoveTask, "motorMoveTask", 4096, NULL, 2, &motorMoveTaskHandle);
  xTaskCreate(motorMonitorTask, "motorMonitorTask", 4096, NULL, 2, &motorMonitorTaskHandle);
  xTaskCreate(setVelocityTask, "setVelocityTask", 4096, NULL, 1, &setVelocityTaskHandle);
  xTaskCreate(sendDataTask, "sendDataTask", 4096, NULL, 1, &sendDataTaskHandle);
  xTaskCreate(stopSendTask, "stopSendTask", 4096, NULL, 1, &stopSendTaskHandle);
}



void loop() {
  // Empty loop as tasks are running independently
}
