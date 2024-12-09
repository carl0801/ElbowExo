#include <algorithm>
#include <TMC2209.h>
#include <Wire.h>
#include <Arduino.h>
#include "freertos/task.h"
#include <ESP32Encoder.h> 
#include "FastAccelStepper.h"
#include <soc/pcnt_struct.h>


#define tmc2209_connected false
#define debug false

//ESP32PWM stepper;
ESP32Encoder encoder;
FastAccelStepperEngine engine = FastAccelStepperEngine();
FastAccelStepper *stepper = NULL;


// Binary serial communication struct
struct SerialData {
  // the first 3 bits are used for checking validity: 101 = valid
  bool var0 = 1;
  bool var1 = 0;
  bool var2 = 1;
  bool var3 = 0;
  bool motor_enable = 0;
  bool motor_stall = 0;
  bool home = 0;
  bool encoder_reset = 0;
  int16_t velocity = 0.0;
  int64_t position = 0.0;
};

SerialData control;
SerialData dataOut;


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
// long encoder_time = 0; // Time of last encoder update
// long encoder_time_old = 0; // Time of second last encoder update
// long dt = 0; // Time since last encoder update
// long vel_encoder = 0; // Encoder velocity
// int16_t position_delta = 0; // Change in position
bool encoder_reset = false; // Reset encoder position


// Motor control variables
volatile bool motor_enable = false;
volatile signed int velocity = 0;
volatile signed int velocity_old = 0;
int minMaxVelocity = 80;

// Serial communication variables
const int SERIAL_BAUD_RATE = 460800;
int serial_int = 0;
float serial_timeout = 10000.0; // milliseconds
float serial_timeout_start = 0.0;
float serial_time_elapsed = 0.0;

uint16_t serial_timeout_cycles = 10000;
uint8_t serial_cycles = 0;
bool serial_timeout_flag = false;

// Serial communication receiver task (struct)
void serialCommInTask(void * parameter) {
  for (;;) {
    if (Serial.available() >= 3) {  // Ensure at least 3 bytes are available
      uint8_t packet[3];
      Serial.readBytes(packet, 3);

      // Unpack the first byte into individual booleans
      bool b0 = bitRead(packet[0], 0);
      bool b1 = bitRead(packet[0], 1);
      bool b2 = bitRead(packet[0], 2);
      if (b0 && !b1 && b2) {
        // Valid packet received
        // Unpack the booleans from the first byte
        bool b3 = bitRead(packet[0], 3);
        bool b4 = bitRead(packet[0], 4);
        bool b5 = bitRead(packet[0], 5);
        bool b6 = bitRead(packet[0], 6);
        bool b7 = bitRead(packet[0], 7);

        // Unpack the 16-bit velocity from the second and third bytes
        int16_t velocity = (int16_t)packet[1] | ((int16_t)packet[2] << 8);
        control.velocity = velocity;
        // Use the parsed data (replace with actual logic)
        control.motor_enable = b4;
        //control.motor_stall = b5;
        encoder_reset = b7;

        // Debug output (optional, for verification)
        #ifndef debug
        Serial.printf("Received: {%d, %d, %d}, bools: %d, %d, %d, %d, %d, %d, %d, %d, %d\n", packet[0], packet[1], packet[2], b1, b2, b3, b4, b5, b6, b7, b8);
        #endif

      }
      else {
          // Invalid packet received
          // Debug output (optional, for verification)
          Serial.printf("Invalid packet received. Received: {%d, %d, %d}, checkbools: %d, %d, %d", packet[0], packet[1], packet[2], b0, b1, b2);
      }
      // Reset timeout flag
      serial_cycles = 0;
    } else {
      serial_cycles++;
    }
    // Timeout handling
    if (serial_cycles > serial_timeout_cycles) {
      stepper->stopMove();
      stepper->setEnablePin(enablePin, false);
      motor_enable = false;
      control.motor_enable = false;
      velocity = 0;
      control.velocity = 0;
      serial_timeout_flag = true;
    }

    // Serial communication delay
    vTaskDelay(50 / portTICK_PERIOD_MS);
  }
}

// // serial communication receiver task (struct)
// void serialCommInTask(void * parameter) {
//   for (;;) {
//     if (Serial.available() > 0) {
//       uint8_t stream;
//       Serial.readBytes(&stream, 3);
      
//       // stream now contains 3 bytes of data.
//       // create binary array of the first byte in the byte array
//       bool binary[8];
//       for (int i = 0; i < 8; i++) {
//         binary[i] = bitRead(stream, i);
//       }
//       // create 16-bit integer from the second and third bytes in the 'stream' byte array

          
//       //velocity = control.velocity;
//       //motor_enable = control.motor_enable;
//       //motor_stall = control.motor_stall;
//       //encoder_reset = control.encoder_reset;
//       serial_cycles = 0;
//     }
//     else {
//       serial_cycles++;
//     }
//     if (serial_cycles > serial_timeout) {
//       stepper->stopMove();
//       stepper->setEnablePin(enablePin, false);
//       motor_enable = false;
//       velocity = 0;
//       serial_timeout_flag = true;
//     }
    
//     vTaskDelay(20 / portTICK_PERIOD_MS); // Serial communication delay
//   }
// }

// serial communication sender task (struct)
void serialCommOutTask(void * parameter) {
  for (;;) {

    dataOut = control;
    // Create a 5-byte array for the packet
    uint8_t packet[8];

    // Pack the booleans into the first byte
    packet[0] = 0b00000101; // Start with validity bits (101)
    packet[0] |= (dataOut.var3 << 3);
    packet[0] |= (dataOut.motor_enable << 4);
    packet[0] |= (dataOut.motor_stall << 5);
    packet[0] |= (dataOut.home << 6);
    packet[0] |= (dataOut.encoder_reset << 7);

    // Pack the velocity (2 bytes)
    packet[1] = dataOut.velocity & 0xFF;       // Lower byte
    packet[2] = (dataOut.velocity >> 8) & 0xFF; // Upper byte


    dataOut.position = control.position;
    // Pack the position (4 bytes)
    packet[3] = dataOut.position & 0xFF;       // 1st byte
    packet[4] = (dataOut.position >> 8) & 0xFF; // 2nd byte
    packet[5] = (dataOut.position >> 16) & 0xFF; // 3rd byte
    packet[6] = (dataOut.position >> 24) & 0xFF; // 4th byte
    Serial.write(packet, sizeof(packet));
    vTaskDelay(50 / portTICK_PERIOD_MS); // Print delay
  }
}

// encoder task
void encoderTask(void * parameter) {
  for (;;) {
    if (encoder_reset) {
      encoder.setCount(0);
      control.position = 0;
      encoder_reset = false;
    }
    else {
      //encoder_time_old = encoder_time;
      //encoder_time = millis();
      new_position = encoder.getCount();
      //dt = encoder_time - encoder_time_old;
      //position_delta = new_position - control.position;
      
      if (new_position != control.position) {
        // compute velocity
        //vel_encoder = position_delta / dt;
        control.position = new_position;
      }
    }
    vTaskDelay(40 / portTICK_PERIOD_MS); // Encoder update delay
  }
}

// motor control task
void motorControlTask(void * parameter) {
  for (;;) {
    if (control.motor_enable && !control.motor_stall) {
      control.velocity = (control.velocity > minMaxVelocity) ? minMaxVelocity : (control.velocity < -minMaxVelocity) ? -minMaxVelocity : control.velocity; // Limit velocity to -50 to 50
      if (control.position < min_limit && control.velocity > 0) {
        control.velocity = 0;
        stepper->stopMove();
      }
      else if (control.position > max_limit && control.velocity < 0) {
        control.velocity = 0;
        stepper->stopMove();
      }
      if (control.velocity != velocity_old) {
        stepper->setSpeedInHz(abs(control.velocity));
        velocity_old = control.velocity;
      }
      if (control.velocity != 0) {
        if (control.velocity > 0) {
          stepper->runForward();
          // use ledcWrite to control the LED
        }
        else if (control.velocity < 0) {
          stepper->runBackward();
        }
      }
    }
    else {
      stepper->setSpeedInHz(0);
      stepper->runForward();
    }
    vTaskDelay(20 / portTICK_PERIOD_MS); // Motor control delay
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
      velocity = (velocity > minMaxVelocity) ? minMaxVelocity : (velocity < -minMaxVelocity) ? -minMaxVelocity : velocity; // Limit velocity to -50 to 50
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
    vTaskDelay(50 / portTICK_PERIOD_MS); // Motor control delay
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
  encoder.attachSingleEdge(Apin, Bpin);
  //encoder.attachHalfQuad(Apin, Bpin);
  encoder.clearCount();
  encoder.setFilter(1023);



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


  xTaskCreatePinnedToCore(serialCommOutTask, "serialCommOutTaskTask", 4096, NULL,2, NULL, 1);
  xTaskCreatePinnedToCore(serialCommInTask, "serialCommInTask", 4096, NULL, 1, NULL, 1);
  xTaskCreatePinnedToCore(encoderTask, "encoderTask", 4096, NULL, 1, NULL, 0);
  xTaskCreatePinnedToCore(motorControlTask, "MainLoopTask", 4096, NULL, 1, NULL, 0);

  //xTaskCreatePinnedToCore(updateInfoTask, "updateInfoTask", 4096, NULL, 1, NULL, 1);
  // xTaskCreate(checkMotorStalled, "CheckMotorStalledTask", 4096, NULL, 1, NULL);
}



void loop() {
  // Empty loop as tasks are running independently
}
