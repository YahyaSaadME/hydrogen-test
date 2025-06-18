class HydrogenGauge {
    constructor(canvasId, maxValue = 1000) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.maxValue = maxValue;
        this.threshold = 100;
        this.currentValue = 0;
        this.alertColor = '#ff4444';
        this.normalColor = '#4CAF50';
        this.warningColor = '#ff9800';
        
        this.setupCanvas();
        this.draw();
    }

    setupCanvas() {
        const rect = this.canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        
        this.ctx.scale(dpr, dpr);
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = rect.height + 'px';
    }

    draw() {
        const centerX = this.canvas.width / (window.devicePixelRatio || 1) / 2;
        const centerY = this.canvas.height / (window.devicePixelRatio || 1) / 2 + 20;
        const radius = Math.min(centerX, centerY) - 20;
        
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw background arc
        this.drawArc(centerX, centerY, radius, -Math.PI, 0, '#e0e0e0', 8);
        
        // Draw threshold marker
        const thresholdAngle = -Math.PI + (this.threshold / this.maxValue) * Math.PI;
        this.drawThresholdMarker(centerX, centerY, radius, thresholdAngle);
        
        // Draw value arc
        const valueAngle = -Math.PI + (this.currentValue / this.maxValue) * Math.PI;
        const color = this.getValueColor(this.currentValue);
        this.drawArc(centerX, centerY, radius, -Math.PI, valueAngle, color, 8);
        
        // Draw scale marks
        this.drawScaleMarks(centerX, centerY, radius);
        
        // Draw scale labels
        this.drawScaleLabels(centerX, centerY, radius);
    }

    drawArc(centerX, centerY, radius, startAngle, endAngle, color, lineWidth) {
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, radius, startAngle, endAngle);
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = lineWidth;
        this.ctx.lineCap = 'round';
        this.ctx.stroke();
    }

    drawThresholdMarker(centerX, centerY, radius, angle) {
        const x1 = centerX + (radius - 15) * Math.cos(angle);
        const y1 = centerY + (radius - 15) * Math.sin(angle);
        const x2 = centerX + (radius + 5) * Math.cos(angle);
        const y2 = centerY + (radius + 5) * Math.sin(angle);
        
        this.ctx.beginPath();
        this.ctx.moveTo(x1, y1);
        this.ctx.lineTo(x2, y2);
        this.ctx.strokeStyle = this.alertColor;
        this.ctx.lineWidth = 3;
        this.ctx.stroke();
    }

    drawScaleMarks(centerX, centerY, radius) {
        const steps = 10;
        for (let i = 0; i <= steps; i++) {
            const angle = -Math.PI + (i / steps) * Math.PI;
            const x1 = centerX + (radius - 10) * Math.cos(angle);
            const y1 = centerY + (radius - 10) * Math.sin(angle);
            const x2 = centerX + radius * Math.cos(angle);
            const y2 = centerY + radius * Math.sin(angle);
            
            this.ctx.beginPath();
            this.ctx.moveTo(x1, y1);
            this.ctx.lineTo(x2, y2);
            this.ctx.strokeStyle = '#666';
            this.ctx.lineWidth = 1;
            this.ctx.stroke();
        }
    }

    drawScaleLabels(centerX, centerY, radius) {
        const steps = 5;
        this.ctx.font = '12px Arial';
        this.ctx.fillStyle = '#666';
        this.ctx.textAlign = 'center';
        
        for (let i = 0; i <= steps; i++) {
            const value = (i / steps) * this.maxValue;
            const angle = -Math.PI + (i / steps) * Math.PI;
            const labelRadius = radius + 20;
            const x = centerX + labelRadius * Math.cos(angle);
            const y = centerY + labelRadius * Math.sin(angle) + 4;
            
            this.ctx.fillText(Math.round(value).toString(), x, y);
        }
    }

    getValueColor(value) {
        if (value > this.threshold) {
            return this.alertColor;
        } else if (value > this.threshold * 0.8) {
            return this.warningColor;
        } else {
            return this.normalColor;
        }
    }

    updateValue(value) {
        this.currentValue = Math.max(0, Math.min(value, this.maxValue));
        this.draw();
    }

    setThreshold(threshold) {
        this.threshold = threshold;
        this.draw();
    }
}

// Global gauge instances
window.gauge1 = null;
window.gauge2 = null;

// Initialize gauges when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.gauge1 = new HydrogenGauge('gauge1', 1000);
    window.gauge2 = new HydrogenGauge('gauge2', 1000);
});
