import spidev
import time
import math

# SPI setup
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

# Read channel from MCP3008
def read_channel(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    value = ((adc[1] & 3) << 8) + adc[2]
    return value

# Convert ADC to voltage
def adc_to_voltage(adc_value, vref=3.3):
    return (adc_value / 1023.0) * vref

# Calculate Rs
def calculate_rs(voltage, rl=10000.0, vc=3.3):
    return ((vc - voltage) * rl) / voltage

# Estimate H2 ppm using Rs/R0 and datasheet curve
def estimate_h2_ppm(rs_r0_ratio):
    if rs_r0_ratio <= 0:
        return 0
    log_ppm = -1.2 * math.log10(rs_r0_ratio) + 1.0
    return round(10 ** log_ppm, 2)

# 🔧 Auto-calibration (in clean air)
print("Calibrating sensor... (10 seconds)")
r0_samples = []

for i in range(10):
    adc_val = read_channel(0)
    voltage = adc_to_voltage(adc_val)
    rs = calculate_rs(voltage)
    r0_samples.append(rs)
    time.sleep(1)

r0 = sum(r0_samples) / len(r0_samples)
print(f"Calibration complete. R0 (clean air Rs): {r0:.2f} Ω")

# 📡 Continuous Monitoring
try:
    while True:
        try:
            adc_val = read_channel(0)
            voltage = adc_to_voltage(adc_val)
            rs = calculate_rs(voltage)
            rs_r0 = rs / r0
            ppm = estimate_h2_ppm(rs_r0)

            print(f"Voltage: {voltage:.2f} V | Rs: {rs:.2f} Ω | Rs/R0: {rs_r0:.2f} | Hydrogen: {ppm} ppm")
            time.sleep(.5)
        except Exception as e:
            print(f"Error: {e}")
except KeyboardInterrupt:
    print("Stopped")
