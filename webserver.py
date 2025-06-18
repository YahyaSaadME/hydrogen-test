from flask import Flask, render_template, jsonify
import threading
import time
import json

app = Flask(__name__)

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/sensors')
def get_all_sensors():
    """API endpoint to get all sensor data from bridge"""
    # This will be overridden by run_system.py when used as bridge
    # Fallback data for standalone operation
    fallback_data = [
        {
            "value": "--",
            "resistance": "--",
            "ratio": "--",
            "timestamp": None,
            "status": "disconnected"
        },
        {
            "value": "--",
            "resistance": "--",
            "ratio": "--",
            "timestamp": None,
            "status": "disconnected"
        }
    ]
    return jsonify(fallback_data)

@app.route('/api/sensor/<int:sensor_id>')
def get_sensor_data(sensor_id):
    """API endpoint to get specific sensor data from bridge"""
    if sensor_id < 1 or sensor_id > 2:
        return jsonify({"error": "Invalid sensor ID"}), 400
    
    # Fallback for standalone operation
    fallback_data = {
        "value": "--",
        "resistance": "--", 
        "ratio": "--",
        "timestamp": None,
        "status": "disconnected"
    }
    return jsonify(fallback_data)

if __name__ == '__main__':
    print("Note: Use run_system.py to start the complete system")
    print("Starting web server only...")
    app.run(host='0.0.0.0', port=5000, debug=True)
if __name__ == '__main__':
    # Start a background thread to simulate sensor data updates
    threading.Thread(target=update_sensor_data, daemon=True).start()

    # Run the Flask web server
    app.run(host='0.0.0.0', port=5000)
