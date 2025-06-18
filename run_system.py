import threading
import time
import sys
import os
import queue
from multiprocessing import Manager, Process, Queue

class DataBridge:
    """Bridge class to transfer data between GUI and web server"""
    def __init__(self):
        # Shared data structure using multiprocessing Manager
        self.manager = Manager()
        self.shared_sensor_data = self.manager.list([
            self.manager.dict({
                "value": "--",
                "resistance": "--",
                "ratio": "--",
                "timestamp": None,
                "status": "disconnected"
            }),
            self.manager.dict({
                "value": "--",
                "resistance": "--",
                "ratio": "--",
                "timestamp": None,
                "status": "disconnected"
            })
        ])
        
        # Communication queues
        self.gui_to_bridge_queue = Queue()
        self.bridge_to_web_queue = Queue()
        
    def update_sensor_data(self, sensor_index, data):
        """Update sensor data in shared memory"""
        try:
            if 0 <= sensor_index < len(self.shared_sensor_data):
                sensor_dict = self.shared_sensor_data[sensor_index]
                for key, value in data.items():
                    sensor_dict[key] = value
                print(f"Bridge: Updated sensor {sensor_index + 1} - PPM: {data.get('value', '--')}")
        except Exception as e:
            print(f"Bridge error updating sensor data: {e}")
    
    def get_sensor_data(self):
        """Get current sensor data"""
        try:
            return [dict(sensor) for sensor in self.shared_sensor_data]
        except Exception as e:
            print(f"Bridge error getting sensor data: {e}")
            return []
    
    def start_bridge_process(self):
        """Start the data bridge process"""
        bridge_process = Process(target=self.run_data_bridge)
        bridge_process.daemon = True
        bridge_process.start()
        return bridge_process
    
    def run_data_bridge(self):
        """Run the data bridge in a separate process"""
        print("Data bridge started...")
        while True:
            try:
                # Check for data from GUI
                if not self.gui_to_bridge_queue.empty():
                    data = self.gui_to_bridge_queue.get_nowait()
                    sensor_index = data.get('sensor_index', 0)
                    sensor_data = data.get('data', {})
                    self.update_sensor_data(sensor_index, sensor_data)
                
                time.sleep(0.1)
            except Exception as e:
                print(f"Bridge process error: {e}")
                time.sleep(1)

# Global bridge instance
data_bridge = DataBridge()

def start_gui_app():
    """Start the main GUI application with data bridge integration"""
    try:
        # Import and modify the GUI app to use data bridge
        import tkinter as tk
        import serial
        import threading
        import time
        from datetime import datetime
        import queue
        import RPi.GPIO as GPIO
        
        class BridgedHydrogenMonitorApp:
            def __init__(self, root, serial_port='/dev/serial0', baud_rate=9600):
                # ...existing code...
                self.root = root
                self.root.title("Hydrogen Sensor Monitor")
                self.root.attributes('-fullscreen', True)
                self.root.attributes('-topmost', True)
                self.root.overrideredirect(True)
                self.root.focus_force()
                self.root.grab_set()
                
                self.threshold = 150
                self.serial_port = serial_port
                self.baud_rate = baud_rate
                self.serial = None
                self.connected = False
                
                # Buzzer setup
                self.buzzer_pin = 26
                self.buzzer_active = False
                self.alert_sensors = set()
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.buzzer_pin, GPIO.OUT)
                GPIO.output(self.buzzer_pin, GPIO.LOW)
                
                self.data_queue = queue.Queue()
                
                # UI setup
                self.root.configure(bg="black")
                self.main_frame = tk.Frame(self.root, bg="black")
                self.main_frame.pack(expand=True, fill="both", padx=50, pady=50)
                self.main_frame.grid_rowconfigure(0, weight=1)
                self.main_frame.grid_columnconfigure(0, weight=1)
                self.main_frame.grid_columnconfigure(1, weight=1)
                
                # Create sensor displays
                self.create_sensor_displays()
                
                # Initialize sensor data
                self.sensor_data = [
                    {"value": "--", "resistance": "--", "ratio": "--", "timestamp": None},
                    {"value": "--", "resistance": "--", "ratio": "--", "timestamp": None}
                ]
                
                # Bind exit keys
                self.root.bind("<Control-Shift-q>", self.emergency_exit)
                self.root.bind("<Control-Shift-Q>", self.emergency_exit)
                self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
                
                # Start threads
                self.serial_thread = threading.Thread(target=self.run_serial_connection)
                self.serial_thread.daemon = True
                self.serial_thread.start()
                
                self.buzzer_thread = threading.Thread(target=self.buzzer_control)
                self.buzzer_thread.daemon = True
                self.buzzer_thread.start()
                
                # Start data bridge communication
                self.bridge_thread = threading.Thread(target=self.send_data_to_bridge)
                self.bridge_thread.daemon = True
                self.bridge_thread.start()
                
                self.update_ui()
            
            def create_sensor_displays(self):
                """Create sensor display UI elements"""
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
                
                for i in range(2):
                    sensor_frame = tk.Frame(self.main_frame, bg="black")
                    sensor_frame.grid(row=0, column=i, sticky="nsew", padx=10, pady=10)
                    self.sensor_frames.append(sensor_frame)
                    
                    # Status bar
                    status_bar = tk.Frame(sensor_frame, bg="black")
                    status_bar.pack(fill=tk.X, anchor="ne")
                    
                    unit_label = tk.Label(status_bar, font=("Arial", 16, "bold"), text="PPM", fg="white", bg="black")
                    unit_label.pack(side=tk.RIGHT, padx=10)
                    self.unit_labels.append(unit_label)
                    
                    led_indicator = tk.Canvas(status_bar, width=20, height=20, bg="black", highlightthickness=0)
                    led_indicator.pack(side=tk.RIGHT, padx=5)
                    led = led_indicator.create_oval(2, 2, 18, 18, fill="gray", outline="white")
                    self.led_indicators.append(led_indicator)
                    self.leds.append(led)
                    
                    # Sensor name
                    name_label = tk.Label(sensor_frame, font=("Arial", 24, "bold"), text=f"Hydrogen {i+1}", fg="white", bg="black")
                    name_label.pack(pady=(0, 10))
                    self.name_labels.append(name_label)
                    
                    # Alert label
                    alert_label = tk.Label(sensor_frame, font=("Arial", 18, "bold"), text="⚠️ ALERT ⚠️", fg="red", bg="black")
                    alert_label.pack()
                    alert_label.pack_forget()
                    self.alert_labels.append(alert_label)
                    
                    # Value display
                    value_label = tk.Label(sensor_frame, font=("Arial", 120, "bold"), text="--", fg="white", bg="black")
                    value_label.pack()
                    self.value_labels.append(value_label)
                    
                    # Timestamp
                    timestamp_label = tk.Label(sensor_frame, font=("Arial", 12), text="Last updated: --", fg="gray", bg="black")
                    timestamp_label.pack(pady=(5, 0))
                    self.timestamp_labels.append(timestamp_label)
                    
                    # Info frame
                    info_frame = tk.Frame(sensor_frame, bg="black")
                    info_frame.pack(pady=20)
                    
                    resistance_label = tk.Label(info_frame, font=("Arial", 16), text="Resistance: -- Ω", fg="white", bg="black")
                    resistance_label.pack(pady=5)
                    self.resistance_labels.append(resistance_label)
                    
                    ratio_label = tk.Label(info_frame, font=("Arial", 16), text="Rs/R0: --", fg="white", bg="black")
                    ratio_label.pack(pady=5)
                    self.ratio_labels.append(ratio_label)
                
                # Status label
                self.status_label = tk.Label(self.root, font=("Arial", 12), text="Connecting to serial port...", fg="yellow", bg="black")
                self.status_label.pack(side=tk.BOTTOM, pady=10)
            
            def send_data_to_bridge(self):
                """Send sensor data to bridge continuously"""
                while True:
                    try:
                        for i in range(2):
                            data = self.sensor_data[i].copy()
                            data["status"] = "connected" if data["timestamp"] and time.time() - data["timestamp"] < 10 else "disconnected"
                            
                            # Send to bridge queue
                            bridge_data = {
                                "sensor_index": i,
                                "data": data
                            }
                            data_bridge.gui_to_bridge_queue.put_nowait(bridge_data)
                        
                        time.sleep(1)
                    except Exception as e:
                        print(f"Error sending data to bridge: {e}")
                        time.sleep(1)
            
            def emergency_exit(self, event=None):
                self.on_closing()
                return "break"
            
            def on_closing(self):
                print("Closing GUI application...")
                GPIO.output(self.buzzer_pin, GPIO.LOW)
                GPIO.cleanup()
                self.root.destroy()
            
            def buzzer_control(self):
                # ...existing code...
                while True:
                    if self.alert_sensors:
                        if not self.buzzer_active:
                            self.buzzer_active = True
                            print(f"ALERT: Sensors {list(self.alert_sensors)} exceeded threshold!")
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
                # ...existing code...
                while not self.data_queue.empty():
                    try:
                        sensor_data = self.data_queue.get_nowait()
                        sensor_index = sensor_data["sensor_index"]
                        self.sensor_data[sensor_index] = sensor_data["data"]
                    except queue.Empty:
                        break
                
                for sensor_index in range(2):
                    data = self.sensor_data[sensor_index]
                    
                    if data["value"] != "--":
                        try:
                            value = float(data["value"])
                            display_value = f"{value:.2f}"
                            
                            if value > self.threshold:
                                self.value_labels[sensor_index].config(text=display_value, fg="red")
                                self.led_indicators[sensor_index].itemconfig(self.leds[sensor_index], fill="red")
                                self.alert_labels[sensor_index].pack(pady=(0, 5))
                                self.alert_sensors.add(sensor_index + 1)
                                
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
                            current_text = self.value_labels[sensor_index].cget("text")
                            if current_text != "--":
                                self.value_labels[sensor_index].config(fg="orange")
                            else:
                                self.value_labels[sensor_index].config(text="--", fg="red")
                            self.led_indicators[sensor_index].itemconfig(self.leds[sensor_index], fill="gray")
                            self.alert_labels[sensor_index].pack_forget()
                            self.alert_sensors.discard(sensor_index + 1)
                    else:
                        if not self.connected:
                            self.value_labels[sensor_index].config(text="--", fg="red")
                            self.led_indicators[sensor_index].itemconfig(self.leds[sensor_index], fill="gray")
                            self.alert_labels[sensor_index].pack_forget()
                            self.alert_sensors.discard(sensor_index + 1)
                    
                    if data["timestamp"]:
                        time_str = datetime.fromtimestamp(data["timestamp"]).strftime('%H:%M:%S.%f')[:-3]
                        self.timestamp_labels[sensor_index].config(text=f"Last updated: {time_str}")
                        
                        if time.time() - data["timestamp"] > 5:
                            current_text = self.value_labels[sensor_index].cget("text")
                            if current_text != "--":
                                self.value_labels[sensor_index].config(fg="orange")
                    
                    if data["resistance"] != "--" and data["ratio"] != "--":
                        self.resistance_labels[sensor_index].config(text=f"Resistance: {data['resistance']} Ω")
                        self.ratio_labels[sensor_index].config(text=f"Rs/R0: {data['ratio']}")
                
                self.root.after(150, self.update_ui)
            
            def run_serial_connection(self):
                # ...existing code...
                while True:
                    try:
                        self.status_label.config(text=f"Connecting to {self.serial_port}...", fg="yellow")
                        self.serial = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
                        self.serial.flushInput()
                        time.sleep(2)
                        
                        self.status_label.config(text=f"Connected to {self.serial_port}", fg="green")
                        self.connected = True
                        
                        buffer = ""
                        while True:
                            try:
                                if self.serial.in_waiting > 0:
                                    new_data = self.serial.read(self.serial.in_waiting).decode('utf-8', errors='ignore')
                                    buffer += new_data
                                    
                                    while '\n' in buffer:
                                        line, buffer = buffer.split('\n', 1)
                                        line = line.strip()
                                        if line:
                                            self.process_sensor_data(line)
                                            
                            except (serial.SerialException, OSError) as e:
                                self.status_label.config(text=f"Serial error: {str(e)}", fg="red")
                                self.connected = False
                                break
                            
                            time.sleep(0.01)
                    
                    except (serial.SerialException, OSError) as e:
                        self.status_label.config(text=f"Connection failed: {str(e)}. Retrying in 5s...", fg="red")
                        self.connected = False
                        if self.serial:
                            try:
                                self.serial.close()
                            except:
                                pass
                    
                    time.sleep(5)
            
            def process_sensor_data(self, data_line):
                # ...existing code...
                try:
                    if any(skip_word in data_line for skip_word in ["MICS-5524", "Warming", "Sensors ready", "Time(s)"]):
                        return
                    
                    parts = data_line.split('\t')
                    
                    if len(parts) >= 2:
                        try:
                            sensor_id = int(parts[1])
                            if sensor_id not in [1, 2]:
                                return
                            
                            sensor_index = sensor_id - 1
                            
                            if "Debug:" in data_line or "Warning:" in data_line:
                                if self.sensor_data[sensor_index]["value"] != "--":
                                    self.sensor_data[sensor_index]["timestamp"] = time.time()
                                return
                            
                            if len(parts) >= 5:
                                resistance = parts[2]
                                ratio = parts[3]
                                ppm_part = parts[4].split()[0]
                                
                                float(ppm_part)
                                float(resistance)
                                float(ratio)
                                
                                sensor_data = {
                                    "sensor_index": sensor_index,
                                    "data": {
                                        "value": ppm_part,
                                        "resistance": resistance,
                                        "ratio": ratio,
                                        "timestamp": time.time()
                                    }
                                }
                                
                                try:
                                    self.data_queue.put_nowait(sensor_data)
                                except queue.Full:
                                    try:
                                        self.data_queue.get_nowait()
                                        self.data_queue.put_nowait(sensor_data)
                                    except queue.Empty:
                                        pass
                                        
                        except (ValueError, IndexError):
                            return
                            
                except Exception as e:
                    print(f"Error processing data: {str(e)}, Line: {data_line}")
        
        # Create and run the GUI app
        root = tk.Tk()
        app = BridgedHydrogenMonitorApp(root)
        root.mainloop()
        
    except Exception as e:
        print(f"Error starting GUI application: {e}")
        sys.exit(1)

def start_web_server():
    """Start the Flask web server with bridge integration"""
    try:
        from flask import Flask, render_template, jsonify
        
        app = Flask(__name__)
        
        @app.route('/')
        def index():
            return render_template('index.html')
        
        @app.route('/api/sensors')
        def get_all_sensors():
            # Get data from bridge
            sensor_data = data_bridge.get_sensor_data()
            return jsonify(sensor_data)
        
        @app.route('/api/sensor/<int:sensor_id>')
        def get_sensor_data(sensor_id):
            if sensor_id < 1 or sensor_id > 2:
                return jsonify({"error": "Invalid sensor ID"}), 400
            
            sensor_data = data_bridge.get_sensor_data()
            if sensor_data and len(sensor_data) > sensor_id - 1:
                return jsonify(sensor_data[sensor_id - 1])
            else:
                return jsonify({"error": "No data available"}), 404
        
        print("Starting web server with bridge integration...")
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        
    except Exception as e:
        print(f"Error starting web server: {e}")
        sys.exit(1)

def main():
    """Main function to start the complete bridged system"""
    print("Starting Hydrogen Leak Detection System with Data Bridge...")
    print("=" * 60)
    
    try:
        # Start the data bridge process
        print("Initializing data bridge...")
        bridge_process = data_bridge.start_bridge_process()
        time.sleep(1)  # Let bridge initialize
        
        # Start GUI application in a separate process
        print("Starting GUI application...")
        gui_process = Process(target=start_gui_app)
        gui_process.daemon = False
        gui_process.start()
        
        # Start web server in a separate process
        print("Starting web server...")
        web_process = Process(target=start_web_server)
        web_process.daemon = True
        web_process.start()
        
        print("\nSystem started successfully!")
        print("=" * 60)
        print("GUI: Full-screen hydrogen monitor display")
        print("Web: http://localhost:5000 (with real-time data bridge)")
        print("Bridge: Real-time data transfer between GUI and web")
        print("Press Ctrl+Shift+Q on GUI to exit")
        print("=" * 60)
        
        # Wait for GUI process to complete
        gui_process.join()
        
        # Cleanup
        if web_process.is_alive():
            web_process.terminate()
        if bridge_process.is_alive():
            bridge_process.terminate()
        
    except KeyboardInterrupt:
        print("\nShutting down system...")
        sys.exit(0)
    except Exception as e:
        print(f"System error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
