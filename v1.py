import tkinter as tk
import serial
import threading
import time
from datetime import datetime
import queue
import RPi.GPIO as GPIO

class HydrogenMonitorApp:
    def __init__(self, root, serial_port='/dev/serial0', baud_rate=9600):
        self.root = root
        self.root.title("Hydrogen Sensor Monitor")

        # Force fullscreen mode and disable window decorations
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)  # Keep window on top
        self.root.overrideredirect(True)  # Remove window decorations
        
        # Disable Alt+Tab and other window switching
        self.root.focus_force()
        self.root.grab_set()

        # Set threshold for alert (in PPM) - 100 ppm
        self.threshold = 100

        # Serial connection parameters
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.serial = None
        self.connected = False

        # Buzzer setup
        self.buzzer_pin = 26  # GPIO 26
        self.buzzer_active = False
        self.alert_sensors = set()  # Track which sensors are in alert state
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.buzzer_pin, GPIO.OUT)
        GPIO.output(self.buzzer_pin, GPIO.LOW)

        # Data queue for thread-safe communication
        self.data_queue = queue.Queue()

        # Set fullscreen mode
        self.root.attributes('-fullscreen', True)

        # Set black background
        self.root.configure(bg="black")

        # Create a frame to hold the content
        self.main_frame = tk.Frame(self.root, bg="black")
        self.main_frame.pack(expand=True, fill="both", padx=50, pady=50)

        # Configure grid for 1 row, 2 columns
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        # Create frames for both hydrogen sensors
        self.sensor_frames = []
        self.unit_labels = []
        self.led_indicators = []
        self.leds = []
        self.name_labels = []
        self.value_labels = []
        self.timestamp_labels = []
        self.resistance_labels = []
        self.ratio_labels = []
        self.alert_labels = []

        # Create displays for both sensors
        for i in range(2):
            sensor_frame = tk.Frame(self.main_frame, bg="black")
            sensor_frame.grid(row=0, column=i, sticky="nsew", padx=10, pady=10)
            self.sensor_frames.append(sensor_frame)

            # Top status bar with unit label
            status_bar = tk.Frame(sensor_frame, bg="black")
            status_bar.pack(fill=tk.X, anchor="ne")

            # Unit label - top right
            unit_label = tk.Label(
                status_bar,
                font=("Arial", 16, "bold"),
                text="PPM",
                fg="white",
                bg="black"
            )
            unit_label.pack(side=tk.RIGHT, padx=10)
            self.unit_labels.append(unit_label)

            # LED indicator for threshold
            led_indicator = tk.Canvas(status_bar, width=20, height=20, bg="black", highlightthickness=0)
            led_indicator.pack(side=tk.RIGHT, padx=5)
            led = led_indicator.create_oval(2, 2, 18, 18, fill="gray", outline="white")
            self.led_indicators.append(led_indicator)
            self.leds.append(led)

            # Sensor name label
            name_label = tk.Label(
                sensor_frame,
                font=("Arial", 24, "bold"),
                text=f"Hydrogen {i+1}",
                fg="white",
                bg="black"
            )
            name_label.pack(pady=(0, 10))
            self.name_labels.append(name_label)

            # Alert label (initially hidden)
            alert_label = tk.Label(
                sensor_frame,
                font=("Arial", 18, "bold"),
                text="⚠️ ALERT ⚠️",
                fg="red",
                bg="black"
            )
            alert_label.pack()
            alert_label.pack_forget()  # Hide initially
            self.alert_labels.append(alert_label)

            # Sensor value display
            value_label = tk.Label(
                sensor_frame,
                font=("Arial", 120, "bold"),
                text="--",
                fg="white",
                bg="black"
            )
            value_label.pack()
            self.value_labels.append(value_label)

            # Timestamp label
            timestamp_label = tk.Label(
                sensor_frame,
                font=("Arial", 12),
                text="Last updated: --",
                fg="gray",
                bg="black"
            )
            timestamp_label.pack(pady=(5, 0))
            self.timestamp_labels.append(timestamp_label)

            # Additional information frame
            info_frame = tk.Frame(sensor_frame, bg="black")
            info_frame.pack(pady=20)

            # Sensor resistance display
            resistance_label = tk.Label(
                info_frame,
                font=("Arial", 16),
                text="Resistance: -- Ω",
                fg="white",
                bg="black"
            )
            resistance_label.pack(pady=5)
            self.resistance_labels.append(resistance_label)

            # Sensor ratio display
            ratio_label = tk.Label(
                info_frame,
                font=("Arial", 16),
                text="Rs/R0: --",
                fg="white",
                bg="black"
            )
            ratio_label.pack(pady=5)
            self.ratio_labels.append(ratio_label)

        # Serial connection status
        self.status_label = tk.Label(
            self.root,
            font=("Arial", 12),
            text="Connecting to serial port...",
            fg="yellow",
            bg="black"
        )
        self.status_label.pack(side=tk.BOTTOM, pady=10)

        # Remove escape key binding to prevent easy exit from fullscreen
        # self.root.bind("<Escape>", self.end_fullscreen)  # Commented out
        
        # Add a secret key combination to exit (Ctrl+Shift+Q)
        self.root.bind("<Control-Shift-q>", self.emergency_exit)
        self.root.bind("<Control-Shift-Q>", self.emergency_exit)

        # Initialize sensor data for both sensors
        self.sensor_data = [
            {
                "value": "--",
                "resistance": "--",
                "ratio": "--",
                "timestamp": None
            },
            {
                "value": "--",
                "resistance": "--",
                "ratio": "--",
                "timestamp": None
            }
        ]

        # Register cleanup function to run on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Start serial connection in a separate thread
        self.serial_thread = threading.Thread(target=self.run_serial_connection)
        self.serial_thread.daemon = True
        self.serial_thread.start()

        # Start buzzer control thread
        self.buzzer_thread = threading.Thread(target=self.buzzer_control)
        self.buzzer_thread.daemon = True
        self.buzzer_thread.start()

        # Schedule UI updates
        self.update_ui()

    def end_fullscreen(self, event=None):
        # Disabled - keep in fullscreen
        return "break"

    def emergency_exit(self, event=None):
        """Emergency exit with Ctrl+Shift+Q"""
        self.on_closing()
        return "break"

    def on_closing(self):
        """Clean up and close application"""
        print("Closing application...")
        GPIO.output(self.buzzer_pin, GPIO.LOW)
        GPIO.cleanup()
        self.root.destroy()

    def buzzer_control(self):
        """Control buzzer based on alert state"""
        while True:
            if self.alert_sensors:
                if not self.buzzer_active:
                    self.buzzer_active = True
                    print(f"ALERT: Sensors {list(self.alert_sensors)} exceeded threshold!")
                
                # Intermittent buzzer pattern
                GPIO.output(self.buzzer_pin, GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(self.buzzer_pin, GPIO.LOW)
                time.sleep(0.5)
            else:
                if self.buzzer_active:
                    self.buzzer_active = False
                    GPIO.output(self.buzzer_pin, GPIO.LOW)
                    print("Alert cleared - buzzer off")
                time.sleep(0.1)

    def update_ui(self):
        """Update UI with the latest sensor data"""
        # Process queued data
        while not self.data_queue.empty():
            try:
                sensor_data = self.data_queue.get_nowait()
                sensor_index = sensor_data["sensor_index"]
                self.sensor_data[sensor_index] = sensor_data["data"]
            except queue.Empty:
                break

        for sensor_index in range(2):
            data = self.sensor_data[sensor_index]

            # Update PPM value - only show "--" if never received data
            if data["value"] != "--":
                try:
                    value = float(data["value"])
                    # Format with 2 decimal places minimum
                    display_value = f"{value:.2f}"
                    
                    # Check for alert condition
                    if value > self.threshold:
                        self.value_labels[sensor_index].config(text=display_value, fg="red")
                        self.led_indicators[sensor_index].itemconfig(self.leds[sensor_index], fill="red")
                        self.alert_labels[sensor_index].pack(pady=(0, 5))
                        self.alert_sensors.add(sensor_index + 1)
                        
                        # Flash the sensor name
                        current_color = self.name_labels[sensor_index].cget("fg")
                        new_color = "red" if current_color == "white" else "white"
                        self.name_labels[sensor_index].config(fg=new_color)
                    else:
                        self.value_labels[sensor_index].config(text=display_value, fg="white")
                        self.led_indicators[sensor_index].itemconfig(self.leds[sensor_index], fill="green")
                        self.alert_labels[sensor_index].pack_forget()
                        self.alert_sensors.discard(sensor_index + 1)
                        self.name_labels[sensor_index].config(fg="white")
                        
                except (ValueError, TypeError):
                    # Keep showing last valid value, just change color to indicate issue
                    current_text = self.value_labels[sensor_index].cget("text")
                    if current_text != "--":
                        self.value_labels[sensor_index].config(fg="orange")  # Orange indicates stale data
                    else:
                        self.value_labels[sensor_index].config(text="--", fg="red")
                    self.led_indicators[sensor_index].itemconfig(self.leds[sensor_index], fill="gray")
                    self.alert_labels[sensor_index].pack_forget()
                    self.alert_sensors.discard(sensor_index + 1)
            else:
                # Only show "--" if we've never received data for this sensor
                if not self.connected:
                    self.value_labels[sensor_index].config(text="--", fg="red")
                    self.led_indicators[sensor_index].itemconfig(self.leds[sensor_index], fill="gray")
                    self.alert_labels[sensor_index].pack_forget()
                    self.alert_sensors.discard(sensor_index + 1)

            # Update timestamp
            if data["timestamp"]:
                time_str = datetime.fromtimestamp(data["timestamp"]).strftime('%H:%M:%S.%f')[:-3]
                self.timestamp_labels[sensor_index].config(text=f"Last updated: {time_str}")
                
                # Check if data is stale (older than 5 seconds)
                if time.time() - data["timestamp"] > 5:
                    current_text = self.value_labels[sensor_index].cget("text")
                    if current_text != "--":
                        self.value_labels[sensor_index].config(fg="orange")  # Indicate stale data

            # Update additional info - keep last known values
            if data["resistance"] != "--" and data["ratio"] != "--":
                self.resistance_labels[sensor_index].config(text=f"Resistance: {data['resistance']} Ω")
                self.ratio_labels[sensor_index].config(text=f"Rs/R0: {data['ratio']}")

        # Schedule next update - reduced frequency for better performance
        self.root.after(100, self.update_ui)

    def run_serial_connection(self):
        """Run the serial connection in a separate thread"""
        while True:
            try:
                # Try to open the serial connection
                self.status_label.config(text=f"Connecting to {self.serial_port}...", fg="yellow")
                self.serial = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
                
                # Clear any existing data in the buffer
                self.serial.flushInput()
                time.sleep(2)  # Wait for connection to initialize

                self.status_label.config(text=f"Connected to {self.serial_port}", fg="green")
                self.connected = True

                # Main reading loop
                buffer = ""
                while True:
                    try:
                        if self.serial.in_waiting > 0:
                            # Read available data
                            new_data = self.serial.read(self.serial.in_waiting).decode('utf-8', errors='ignore')
                            buffer += new_data
                            
                            # Process complete lines
                            while '\n' in buffer:
                                line, buffer = buffer.split('\n', 1)
                                line = line.strip()
                                if line:
                                    self.process_sensor_data(line)
                                    
                    except (serial.SerialException, OSError) as e:
                        self.status_label.config(text=f"Serial error: {str(e)}", fg="red")
                        self.connected = False
                        break

                    time.sleep(0.01)  # Very short delay to prevent CPU hogging

            except (serial.SerialException, OSError) as e:
                self.status_label.config(text=f"Connection failed: {str(e)}. Retrying in 5s...", fg="red")
                self.connected = False
                if self.serial:
                    try:
                        self.serial.close()
                    except:
                        pass

            # Wait before reconnecting
            time.sleep(5)

    def process_sensor_data(self, data_line):
        """Process the data coming from the Arduino"""
        try:
            # Skip header lines and warnings, but allow debug messages
            if any(skip_word in data_line for skip_word in ["MICS-5524", "Warming", "Sensors ready", "Time(s)"]):
                return

            # Parse the data line
            parts = data_line.split('\t')

            if len(parts) >= 2:
                try:
                    sensor_id = int(parts[1])
                    if sensor_id not in [1, 2]:
                        return

                    # Adjust to 0-based index
                    sensor_index = sensor_id - 1

                    # Handle debug/warning messages - keep last known values
                    if "Debug:" in data_line or "Warning:" in data_line:
                        # Don't update values, just update timestamp to show it's still active
                        if self.sensor_data[sensor_index]["value"] != "--":
                            self.sensor_data[sensor_index]["timestamp"] = time.time()
                        return

                    # Handle normal data - Expected format: Time(s)\tSensor\tRs(ohms)\tRs/R0\tH2(ppm)
                    if len(parts) >= 5:
                        resistance = parts[2]
                        ratio = parts[3]
                        ppm_part = parts[4].split()[0]  # Remove the " ppm" part

                        # Validate numeric values
                        float(ppm_part)  # This will raise ValueError if invalid
                        float(resistance)
                        float(ratio)

                        # Queue the data for UI update
                        sensor_data = {
                            "sensor_index": sensor_index,
                            "data": {
                                "value": ppm_part,
                                "resistance": resistance,
                                "ratio": ratio,
                                "timestamp": time.time()
                            }
                        }
                        
                        # Add to queue (non-blocking)
                        try:
                            self.data_queue.put_nowait(sensor_data)
                        except queue.Full:
                            # If queue is full, remove oldest item and add new one
                            try:
                                self.data_queue.get_nowait()
                                self.data_queue.put_nowait(sensor_data)
                            except queue.Empty:
                                pass
                            
                except (ValueError, IndexError):
                    # Skip invalid data but don't reset values
                    return
                    
        except Exception as e:
            print(f"Error processing data: {str(e)}, Line: {data_line}")

if __name__ == "__main__":
    # Create Tkinter window
    root = tk.Tk()

    # On Windows, use COM port instead of /dev/serial0
    # For example: app = HydrogenMonitorApp(root, serial_port='COM3')
    app = HydrogenMonitorApp(root)

    # Start the Tkinter main loop
    root.mainloop()
