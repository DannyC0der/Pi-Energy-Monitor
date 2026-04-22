import time, board, busio, math, csv
import os
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import numpy as np
from scipy.fft import fft

# Setup
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c); ads.gain = 8
chan = AnalogIn(ads, 0, 1)
SENSITIVITY = 30.0

label = input("Enter device name (e.g., laptop, lamp, fan): ")
filename = f"data/{label}_training.csv"

file_exists = os.path.isfile(filename)

print(f"Logging {label}... Press Ctrl+C to stop.")

with open(filename, mode='a', newline='') as f:
    writer = csv.writer(f)

    # Only write header  if we are making a new file
    if not file_exists:
    	writer.writerow(['rms', 'h3_ratio', 'h5_ratio', 'label'])

    while True:
        samples = []
        for _ in range(200): # Capture a burst
            samples.append(chan.voltage * SENSITIVITY)
        
        # 1. Calculate RMS
        rms = math.sqrt(sum(s*s for s in samples)/len(samples))
        
        # 2. Calculate Harmonics via FFT
        yf = np.abs(fft(samples))
        fundamental = yf[1] if yf[1] > 0 else 1 # Avoid div by zero
        h3 = yf[3] / fundamental
        h5 = yf[5] / fundamental

        writer.writerow([round(rms, 4), round(h3, 4), round(h5, 4), label])
        print(f"Logged: RMS={rms:.3f}, H3={h3:.2f}, H5={h5:.2f}")
        time.sleep(1)
