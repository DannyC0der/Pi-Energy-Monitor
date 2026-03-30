import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import matplotlib.pyplot as plt

# 1. Setup
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = 8  # Higher gain for the small laptop signal
chan = AnalogIn(ads, 0, 1)

SENSITIVITY = 30.0 # 30A/1V
DURATION = 10      # Seconds to record

timestamps = []
current_values = []

print(f"Recording for {DURATION} seconds... start the laptop load now!")
start_time = time.time()

# 2. Fast Data Collection
# We use a tight loop to get as many samples as the I2C bus allows
while (time.time() - start_time) < DURATION:
    now = time.time() - start_time
    # In differential mode, chan.voltage is already the AC swing
    instantaneous_current = chan.voltage * SENSITIVITY
    
    timestamps.append(now)
    current_values.append(instantaneous_current)

print(f"Captured {len(timestamps)} samples.")

# 3. Plotting the results
plt.figure(figsize=(12, 6))

# Plot 1: The full 10-second capture (will look like a solid block of color)
plt.subplot(2, 1, 1)
plt.plot(timestamps, current_values, color='blue', linewidth=0.5)
plt.title('Instantaneous Current over 10 Seconds (Raw AC Signal)')
plt.ylabel('Current (Amps)')
plt.grid(True)

# Plot 2: A "Zoom-in" on the first 0.1 seconds to see the actual waveform
plt.subplot(2, 1, 2)
plt.plot(timestamps, current_values, color='red')
plt.xlim(0, 0.1) # Zoom into the first 100ms
plt.title('Zoomed-in Waveform (First 100ms - Approx 5 Cycles)')
plt.xlabel('Time (seconds)')
plt.ylabel('Current (Amps)')
plt.grid(True)

plt.tight_layout()
plt.savefig('current_waveform.png')
print("Graph saved as 'current_waveform.png'")
