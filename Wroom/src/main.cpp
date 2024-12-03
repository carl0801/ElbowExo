#include <TMC2209.h>
#include <Wire.h>
#include <Arduino.h>
#include "freertos/task.h"
#include <ESP32Encoder.h> 
#include <ESP32Servo.h>

HardwareSerial & serial_stream = Serial2;
ESP32PWM stepper;
ESP32Encoder encoder;

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
        if (encoder_reset) {
          encoder.setCount(0);}
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
    vTaskDelay(150 / portTICK_PERIOD_MS); // Serial communication delay
  }
}

// serial communication sender task
void serialCommOutTask(void * parameter) {
  for (;;) {
    Serial.printf("%d,%d,%u,%d,%d,%d\n", stallguard_result, velocity, vel_actual, motor_enable, motor_stall, temp_newPosition);

    vTaskDelay(25000 / portTICK_PERIOD_MS); // Print delay
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
    stepper.write(0);
    return;
  }

  // Calculate frequency from velocity (pulses per second)
  double frequency = abs(velocity);

  // Set the pulse duration (fixed at 0.2 ms)
  double pulseDuration = 0.0002; // 0.2 milliseconds in seconds

  // Calculate the duty cycle as a fraction
  double dutyCycleFraction = pulseDuration * frequency; // e.g., for 10 Hz -> 0.002 * 10 = 0.02

  // Limit duty cycle fraction to 1.0 (to avoid overflows)
  dutyCycleFraction = 0.5;//constrain(dutyCycleFraction, 0.0, 1.0);

  // Set the direction pin based on velocity sign
  digitalWrite(dirPin, velocity > 0 ? HIGH : LOW);

  // Adjust PWM frequency and duty cycle
  stepper.adjustFrequency(frequency, dutyCycleFraction);
}



void mainLoop(void * parameter) {
  for (;;) {

    if (motor_enable && !motor_stall) {
      velocity = (velocity > minMaxVelocity) ? minMaxVelocity : (velocity < -minMaxVelocity) ? -minMaxVelocity : velocity; // Limit velocity to -50 to 50
      if (temp_newPosition < minEncoderValue && velocity > 0) {
        velocity = 0;
      }
      else if (temp_newPosition > maxEncoderValue && velocity < 0) {
        velocity = 0;
      }
      //stepper_driver.moveAtVelocity(velocity);
      moveAtVelocity(velocity);
    }
    else {
      //stepper_driver.moveAtVelocity(0);
      moveAtVelocity(0);
    }
  
    vTaskDelay(10 / portTICK_PERIOD_MS); // Motor control delay
  }
}

void IRAM_ATTR handleInterrupt() {
  motor_stall = true;
}

void encoderTask(void * parameter) {
  for (;;) {
    long newPosition = encoder.getCount() / 2;
    if (newPosition != temp_newPosition) {
      //Serial.printf("Position: %ld\n", newPosition);
      temp_newPosition = newPosition;
    }

    // vi kan nemt tilføje Z-pin her, hvis vi vil have en tæller for hver omdrejning

    vTaskDelay(10 / portTICK_PERIOD_MS); // Encoder update delay
  }
}

void setup() {
  pinMode(stallGuardPin, INPUT);
  pinMode(Apin, INPUT);
  pinMode(Bpin, INPUT);
  pinMode(Zpin, INPUT);
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);
  encoder.attachSingleEdge( Apin, Bpin );
  encoder.setCount ( 0 );
  
  // attach pwm pins
  stepper.attachPin(stepPin, 0, 16);

  
  //ESP32 needs special "IRAM_ATTR" in interrupt
  // Set stalled motor flag with function stored in IRAM
  attachInterrupt(digitalPinToInterrupt(stallGuardPin), handleInterrupt, RISING);
  
  pinMode(enablePin, OUTPUT);

  Serial.begin(115200);
  //uartLoopbackTest();
  // driver setup
  stepper_driver.setup(serial_stream);
  stepper_driver.setHardwareEnablePin(enablePin);
  stepper_driver.enable();
  motor_enable = true;

  stepper_driver.setMicrostepsPerStep(0);
  stepper_driver.disableStealthChop();
  stepper_driver.setRunCurrent(RUN_CURRENT_PERCENT);
  stepper_driver.setHoldCurrent(50);
  /* stepper_driver.enableStealthChop();

  stepper_driver.useExternalSenseResistors();
  stepper_driver.setStealthChopDurationThreshold(230); // lower lim SG
  stepper_driver.setCoolStepDurationThreshold(0xFFFF); // upper lim SG
   */
  stepper_driver.setMicrostepsPerStep(0);

  

  // enable spreadCycle for low speed


  // NOTES:
  //  DISABLE COOLSTEP DURING STALLGUARD HOMING. COOLSTEP CAUSES SPURIOUS DETECTION OF MOTOR STALLS
  //  ENABLE COOLSTEP AFTER HOMING AND DISABLE STALLGUARD.

  //  TUNING:
  //  ENABLE STEALTCHCHOP. DISABLE COOLSTEP. TUNE STALLGUARD ONLY FIRST. THEN DISABLE STALLGUARD AND TUNE COOLSTEP.


  //  ADDRESSES:
  //  ADDRESS_TPWMTHRS = SETSTEALTHCHOPDURATIONTHRESHOLD --> LOWER LIM FOR STALLGUARD
  //  ADDRESS_TCOOLTHRS = SETCOOLSTEPDURATIONTHRESHOLD --> UPPER LIM FOR STALLGUARD
  //  ADDRESS_SGTHRS = SETSTALLGUARDTHRESHOLD
  //  ADDRESS_TSTEP = SETINTERSTEPDURATION


  // Coolstep related:
  //  high currect increment (SEUP): faster current ramp-up -> faster response to high-torque demands. Too high: motor oscillations
  //  standstill/low velocity: cannot measure motor load. Coolstep disabled below a certain velocity -> set by coolstep lower threshold
  //  when below velocity threshold: current is set with IRUN and IHOLD. When above threshold: current is set by coolstep
  //  Coolstep increments current with SEUP and decrements with SEDN.
  //  SEMIN sets the current where coolstep starts to increment current. SEMAX sets the maximum current, where coolstep decrements current.
  //  SG_RESULT is the stallguard value, but is actually also motor current. COOLSTEP uses SG_RESULT to monitor motor current.
  //  TPWMTHRS: Upper velocity value. When above this velocity, SpreadCycle is used, and CoolStep and Stallguard are disabled.
  //  TCOOLTHRS: Lower velocity value. When below this velocity, CoolStep is disabled.

  //  Tuning CoolStep:
  //  If stallguard has been implemented, SEMIN can be set as SEMIN = 1+SGTHRS/16 for a starting value.
  // coolstep setup (DON'T USE WHEN USING STALLGUARD)
  stepper_driver.disableCoolStep();
  //stepper_driver.enableCoolStep();
  //stepper_driver.setCoolStepDurationThreshold(0xFFFF);
  //stepper_driver.set
  //stepper_driver.moveAtVelocity(100);


  // stallguard setup (DISABLE COOLSTEP)
  stepper_driver.setStallGuardThreshold(0);

  

  if (debug) {
    delay(1000);
    if (not stepper_driver.isCommunicating()) {
      Serial.println("Stepper driver not communicating!");
    }
    else {
      Serial.println("Stepper driver communicating!");
      TMC2209::Settings settings = stepper_driver.getSettings();
      Serial.println("Settings:");
      Serial.printf("is_setup: %d\n", settings.is_setup);
      Serial.printf("software_enabled: %d\n", settings.software_enabled);
      Serial.printf("microsteps_per_step: %u\n", settings.microsteps_per_step);
      Serial.printf("inverse_motor_direction_enabled: %d\n", settings.inverse_motor_direction_enabled);
      Serial.printf("stealth_chop_enabled: %d\n", settings.stealth_chop_enabled);
      Serial.printf("standstill_mode: %u\n", settings.standstill_mode);
      Serial.printf("irun_percent: %u\n", settings.irun_percent);
      Serial.printf("irun_register_value: %u\n", settings.irun_register_value);
      Serial.printf("ihold_percent: %u\n", settings.ihold_percent);
      Serial.printf("ihold_register_value: %u\n", settings.ihold_register_value);
      Serial.printf("iholddelay_percent: %u\n", settings.iholddelay_percent);
      Serial.printf("iholddelay_register_value: %u\n", settings.iholddelay_register_value);
      Serial.printf("automatic_current_scaling_enabled: %d\n", settings.automatic_current_scaling_enabled);
      Serial.printf("automatic_gradient_adaptation_enabled: %d\n", settings.automatic_gradient_adaptation_enabled);
      Serial.printf("pwm_offset: %u\n", settings.pwm_offset);
      Serial.printf("pwm_gradient: %u\n", settings.pwm_gradient);
      Serial.printf("cool_step_enabled: %d\n", settings.cool_step_enabled);
      Serial.printf("analog_current_scaling_enabled: %d\n", settings.analog_current_scaling_enabled);
      Serial.printf("internal_sense_resistors_enabled: %d\n", settings.internal_sense_resistors_enabled);
      Serial.println("Settings printed");
    }
  }
  else {
    delay(200);
  }


  xTaskCreatePinnedToCore(mainLoop, "MainLoopTask", 4096, NULL, 1, NULL, 0);
  xTaskCreatePinnedToCore(serialCommOutTask, "serialCommOutTaskTask", 4096, NULL, 2, NULL, 1);
  xTaskCreatePinnedToCore(serialCommInTask, "serialCommInTask", 4096, NULL, 1, NULL, 1);
  xTaskCreatePinnedToCore(updateInfoTask, "updateInfoTask", 4096, NULL, 1, NULL, 1);
  xTaskCreatePinnedToCore(encoderTask, "encoderTask", 4096, NULL, 1, NULL, 1);
  // xTaskCreate(checkMotorStalled, "CheckMotorStalledTask", 4096, NULL, 1, NULL);
}



void loop() {
  // Empty loop as tasks are running independently
}