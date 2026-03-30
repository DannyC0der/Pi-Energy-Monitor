import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import math

# Initialize I2C and ADS1115
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# SET GAIN HERE: 
# Start with 4 (+/- 1.024V). If the reading "flatlines", go to 2.
# For tiny loads like a laptop charger, try 8 or 16.
ads.gain = 8 

# Use Differential Mode: P0 minus P1
chan = AnalogIn(ads, 0, 1)

SENSITIVITY = 30.0  # 30A / 1V
SAMPLES = 500

def get_differential_current():
    sum_sq_v = 0
    for _ in range(SAMPLES):
        # In differential mode, 'chan.voltage' is already (A0 - A1)
        # So the 1.635V bias is automatically removed!
        v = chan.voltage
        sum_sq_v += v * v
    
    rms_v = math.sqrt(sum_sq_v / SAMPLES)
    return rms_v * SENSITIVITY

print(f"Monitoring in Differential Mode (Gain: {ads.gain})...")

try:
    while True:
        amps = get_differential_current()
        
        # Lower noise floor for higher sensitivity
        if amps < 0.02: amps = 0.0
        
        print(f"Current: {amps:.3f} A")
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\nStopped.")
