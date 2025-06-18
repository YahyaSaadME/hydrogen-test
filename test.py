import serial

# Adjust the COM port (Windows: 'COM3', Linux/Mac: '/dev/ttyUSB0' or '/dev/ttyACM0')
arduino = serial.Serial('/dev/serial0',9600)  # Replace with your port
arduino.flush()

while True:
    if arduino.in_waiting > 0:
        line = arduino.readline().decode('utf-8').strip()
        print(f"Received: {line}")
