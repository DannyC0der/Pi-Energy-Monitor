import time
import board
import busio
import pandas as pd
import joblib
import numpy as np
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import math

app = Flask(__name__)
# Explicitly allow all origins and set async_mode
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

model = joblib.load('classifier.pkl')

# Hardware Setup
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = 8 
chan = AnalogIn(ads, 0, 1)
SENSITIVITY = 30.0

def read_sensor():
    while True:
        try:
            samples = []
            sum_sq = 0
            num_samples = 150
            
            # 1. Collect the data correctly
            for _ in range(num_samples):
                v = chan.voltage
                curr = v * SENSITIVITY
                samples.append(curr)
                sum_sq += curr * curr
            
            # 2. CALCULATE the variables correctly
            # Use the sum_sq we calculated in the loop above
            rms = math.sqrt(sum_sq / num_samples)
            
            # FFT for harmonics (pass the SAMPLES list, not the number 150)
            yf = np.abs(np.fft.fft(samples))
            # The fundamental is usually at index 1 for this sample size
            fundamental = yf[1] if yf[1] > 0 else 1
            h3 = yf[3] / fundamental
            h5 = yf[5] / fundamental

            # 3. Predict the device
            features = pd.DataFrame([[rms, h3, h5]], columns=['rms', 'h3_ratio', 'h5_ratio'])
            probs = model.predict_proba(features)[0]
            max_conf = float(np.max(probs))
            best_guess = model.classes_[np.argmax(probs)]

            #70% cnfidence threshold
            if max_conf < 0.70:
            	final_prediction = "UNKNOWN"
            else:
            	final_prediction = best_guess
            
            # 4. Emit to web dashboard
            socketio.emit('new_data', {
                'value': round(rms, 3), 
                'device': final_prediction,
		'confidence': max_conf
            })
            
            print(f"Detected: {final_prediction} at {rms:.3f}A and ({max_conf*100:.lf%}) confidence")

            # Inside your read_sensor while loop
            socketio.emit('new_data', {
               'value': float(rms),
               'device': str(final_prediction),
               'confidence': float(max_conf)
            })

        except Exception as e:
            print(f"Error: {e}")
            
        socketio.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    sensor_thread = threading.Thread(target=read_sensor)
    sensor_thread.daemon = True
    sensor_thread.start()
    # Port 5000 is fine, but make sure no other process is using it
    socketio.run(app, host='192.168.0.236', port=5001)
