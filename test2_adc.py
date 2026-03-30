#!/usr/bin/env python3

import time
import board
import busio
import matplotlib.pyplot as plt
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# I2C setup
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# Gain 1: +/- 4.096V (Safe for 1.64V signal)
# Gain 16: +/- 0.256V (Only use if signal is ALREADY centered at 0 via hardware)
ads.gain = 1

chan = AnalogIn(ads, 0)

# --- SETTINGS ---
TARGET_CENTER = 0.98
DURATION = 10         # Total seconds
INTERVAL = 0.1        # Take a reading every 0.1 seconds

voltages = []
timestamps = []

print("Calibrating hardware offset...")
# Take 10 quick samples to find the actual resting voltage (around 1.64V)
samples = [chan.voltage for _ in range(10)]
hardware_bias = sum(samples) / len(samples)
print(f"Detected hardware bias: {hardware_bias:.3f}V")

print(f"Starting {DURATION}-second capture (one reading every {INTERVAL}s)...")
start_time = time.time()
next_reading = start_time

try:
    while (time.time() - start_time) < DURATION:
        current_time = time.time()

        # Check if it is time for the next 0.1s interval
        if current_time >= next_reading:
            raw_voltage = chan.voltage

            # Shift the voltage to be centered at 0.98V
            adjusted_voltage = (raw_voltage - hardware_bias) + TARGET_CENTER

            voltages.append(adjusted_voltage)
            timestamps.append(current_time - start_time)

            # Schedule the next reading exactly 0.1s after the last scheduled one
            next_reading += INTERVAL

        # Short sleep to prevent CPU maxing out while waiting for the next interval
        time.sleep(0.001)

except KeyboardInterrupt:
    print("\nCapture interrupted by user.")

print(f"Capture complete. Collected {len(voltages)} samples.")

# Plot graph
plt.figure(figsize=(10, 5))
plt.plot(timestamps, voltages, marker='o', linestyle='-', markersize=4)
plt.xlabel("Time (seconds)")
plt.ylabel("Adjusted Voltage (V)")
plt.title(f"CT Clamp Voltage (Interval: {INTERVAL}s)")

# Zoom into your target range
plt.ylim(0.960, 1.000) 
plt.grid(True)
plt.savefig("voltage2_plot.png")
print("Plot saved as voltage_plot.png")
plt.show()
