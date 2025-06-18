class HydrogenMonitor {
    constructor() {
        this.threshold = 100; // PPM threshold for alerts
        this.updateInterval = 1000; // Update every second
        this.init();
    }

    init() {
        this.startDataUpdates();
        this.setupEventListeners();
    }

    startDataUpdates() {
        this.updateData();
        setInterval(() => {
            this.updateData();
        }, this.updateInterval);
    }

    async updateData() {
        try {
            const response = await fetch('/api/sensors');
            const data = await response.json();
            
            data.forEach((sensor, index) => {
                this.updateSensorDisplay(index + 1, sensor);
            });
            
            this.updateSystemStatus(data);
        } catch (error) {
            console.error('Error fetching sensor data:', error);
            this.showError();
        }
    }

    updateSensorDisplay(sensorId, data) {
        const gaugeValueElement = document.getElementById(`gaugeValue${sensorId}`);
        const resistanceElement = document.getElementById(`resistance${sensorId}`);
        const ratioElement = document.getElementById(`ratio${sensorId}`);
        const timestampElement = document.getElementById(`timestamp${sensorId}`);
        const statusElement = document.getElementById(`status${sensorId}`);
        const alertElement = document.getElementById(`alert${sensorId}`);
        const sensorCard = document.getElementById(`sensor${sensorId}`);

        // Update gauge and PPM value
        if (data.value !== "--" && data.value !== null) {
            const ppmValue = parseFloat(data.value);
            
            // Update gauge
            const gauge = window[`gauge${sensorId}`];
            if (gauge) {
                gauge.updateValue(ppmValue);
            }
            
            // Update gauge value display
            gaugeValueElement.textContent = ppmValue.toFixed(2);
            
            // Check for alert condition
            if (ppmValue > this.threshold) {
                gaugeValueElement.classList.add('alert');
                sensorCard.classList.add('alert');
                alertElement.style.display = 'block';
                statusElement.className = 'sensor-status warning';
                statusElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
            } else {
                gaugeValueElement.classList.remove('alert');
                sensorCard.classList.remove('alert');
                alertElement.style.display = 'none';
                statusElement.className = 'sensor-status connected';
                statusElement.innerHTML = '<i class="fas fa-circle"></i>';
            }
        } else {
            // Update gauge to show no data
            const gauge = window[`gauge${sensorId}`];
            if (gauge) {
                gauge.updateValue(0);
            }
            
            gaugeValueElement.textContent = '--';
            gaugeValueElement.classList.remove('alert');
            sensorCard.classList.remove('alert');
            alertElement.style.display = 'none';
        }

        // Update resistance
        if (data.resistance !== "--" && data.resistance !== null) {
            resistanceElement.textContent = `${parseFloat(data.resistance).toFixed(2)} Ω`;
        } else {
            resistanceElement.textContent = '-- Ω';
        }

        // Update ratio
        if (data.ratio !== "--" && data.ratio !== null) {
            ratioElement.textContent = parseFloat(data.ratio).toFixed(3);
        } else {
            ratioElement.textContent = '--';
        }

        // Update timestamp
        if (data.timestamp) {
            const date = new Date(data.timestamp * 1000);
            timestampElement.textContent = date.toLocaleTimeString();
            
            // Check if data is stale (older than 10 seconds)
            const now = new Date().getTime() / 1000;
            if (now - data.timestamp > 10) {
                statusElement.className = 'sensor-status warning';
                statusElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
            }
        } else {
            timestampElement.textContent = '--';
            statusElement.className = 'sensor-status disconnected';
            statusElement.innerHTML = '<i class="fas fa-times-circle"></i>';
        }
    }

    updateSystemStatus(data) {
        const systemStatus = document.getElementById('systemStatus');
        const hasActiveAlerts = data.some(sensor => 
            sensor.value !== "--" && sensor.value !== null && parseFloat(sensor.value) > this.threshold
        );
        
        const hasConnection = data.some(sensor => sensor.timestamp !== null);
        
        if (hasActiveAlerts) {
            systemStatus.className = 'status-indicator offline';
            systemStatus.innerHTML = '<i class="fas fa-exclamation-triangle"></i><span>ALERT ACTIVE</span>';
        } else if (hasConnection) {
            systemStatus.className = 'status-indicator';
            systemStatus.innerHTML = '<i class="fas fa-circle"></i><span>System Online</span>';
        } else {
            systemStatus.className = 'status-indicator offline';
            systemStatus.innerHTML = '<i class="fas fa-times-circle"></i><span>System Offline</span>';
        }
    }

    showError() {
        const systemStatus = document.getElementById('systemStatus');
        systemStatus.className = 'status-indicator offline';
        systemStatus.innerHTML = '<i class="fas fa-exclamation-triangle"></i><span>Connection Error</span>';
    }

    setupEventListeners() {
        // Add any additional event listeners here
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                // Refresh data when page becomes visible
                this.updateData();
            }
        });
    }
}

// Initialize the monitor when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new HydrogenMonitor();
});
