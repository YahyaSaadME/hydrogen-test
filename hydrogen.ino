const int sensor1Pin = A0;
const int sensor2Pin = A1;
const int heaterPin = 9;

// Calibration values for sensor 1
const float R0_1 = 3184541.46;
const float A_1 = 2.2217;
const float B_1 = 0.4130;

// Calibration values for sensor 2
const float R0_2 = 3184541.46;
const float A_2 = 2.2217;
const float B_2 = 0.4130;

// Load resistors - you may need to adjust RL_1 if sensor 1 has different load resistor
const float RL_1 = 10000.0;  // 10k ohm for sensor 1
const float RL_2 = 10000.0;  // 10k ohm for sensor 2

// Voltage thresholds - lowered to handle more sensitive readings
const float MIN_VOLTAGE_1 = 0.005;  // Reduced threshold for sensor 1
const float MIN_VOLTAGE_2 = 0.01;   // Keep original threshold for sensor 2

// Sensor variables
float sensor1Value, sensor2Value;
float sensor1Voltage, sensor2Voltage;
float sensor1Resistance, sensor2Resistance;
float ratio1, ratio2;
float ppm1, ppm2;

// Timing variables for consistent data output
unsigned long lastReadTime = 0;
const unsigned long readInterval = 1000; // 1 second between readings

void setup() {
  Serial.begin(9600);
  pinMode(heaterPin, OUTPUT);
  digitalWrite(heaterPin, HIGH);

  Serial.println("MICS-5524 Dual Hydrogen Sensor Readings");
  Serial.println("Warming up sensors...");
  
  // Longer warm-up for stable readings
  for (int i = 60; i > 0; i--) {
    Serial.print("Warming up... ");
    Serial.print(i);
    Serial.println(" seconds remaining");
    delay(1000);
  }
  
  Serial.println("Sensors ready!");
  Serial.println("Time(s)\tSensor\tRs(ohms)\tRs/R0\tH2(ppm)");
  Serial.flush(); // Ensure all setup messages are sent
}

void loop() {
  unsigned long currentTime = millis();
  
  // Only read sensors at specified intervals
  if (currentTime - lastReadTime >= readInterval) {
    lastReadTime = currentTime;
    
    // Read and process both sensors
    readSensor1();
    delay(100); // Small delay between sensor readings
    readSensor2();
  }
  
  // Small delay to prevent overwhelming the serial port
  delay(50);
}

void readSensor1() {
  sensor1Value = analogRead(sensor1Pin);
  sensor1Voltage = sensor1Value * (5.0 / 1023.0);

  // Debug output for sensor 1
  if (sensor1Voltage <= MIN_VOLTAGE_1) {
    Serial.print(millis() / 1000);
    Serial.print("\t1\tDebug: Raw=");
    Serial.print(sensor1Value);
    Serial.print(" V=");
    Serial.print(sensor1Voltage, 4);
    Serial.println(" (voltage too low)");
    return;
  }

  sensor1Resistance = ((5.0 * RL_1) / sensor1Voltage) - RL_1;
  
  // Validate resistance value
  if (sensor1Resistance > 0) {
    ratio1 = sensor1Resistance / R0_1;
    ppm1 = A_1 * pow((R0_1 / sensor1Resistance), B_1);
    
    // Ensure PPM is not negative
    if (ppm1 < 0) ppm1 = 0;

    // Output sensor 1 data with consistent formatting
    Serial.print(millis() / 1000);
    Serial.print("\t1\t");
    Serial.print(sensor1Resistance, 2);
    Serial.print("\t");
    Serial.print(ratio1, 4);
    Serial.print("\t");
    Serial.print(ppm1, 2);
    Serial.println(" ppm");
  } else {
    Serial.print(millis() / 1000);
    Serial.print("\t1\tDebug: V=");
    Serial.print(sensor1Voltage, 4);
    Serial.print(" R=");
    Serial.print(sensor1Resistance, 2);
    Serial.println(" (invalid resistance)");
  }
}

void readSensor2() {
  sensor2Value = analogRead(sensor2Pin);
  sensor2Voltage = sensor2Value * (5.0 / 1023.0);

  if (sensor2Voltage > MIN_VOLTAGE_2) {
    sensor2Resistance = ((5.0 * RL_2) / sensor2Voltage) - RL_2;
    
    // Validate resistance value
    if (sensor2Resistance > 0) {
      ratio2 = sensor2Resistance / R0_2;
      ppm2 = A_2 * pow((R0_2 / sensor2Resistance), B_2);
      
      // Ensure PPM is not negative
      if (ppm2 < 0) ppm2 = 0;

      // Output sensor 2 data with consistent formatting
      Serial.print(millis() / 1000);
      Serial.print("\t2\t");
      Serial.print(sensor2Resistance, 2);
      Serial.print("\t");
      Serial.print(ratio2, 4);
      Serial.print("\t");
      Serial.print(ppm2, 2);
      Serial.println(" ppm");
    } else {
      Serial.print(millis() / 1000);
      Serial.println("\t2\tWarning: Invalid resistance calculation");
    }
  } else {
    Serial.print(millis() / 1000);
    Serial.println("\t2\tWarning: sensor 2 voltage too low!");
  }
}