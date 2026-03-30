import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import math

app = Flask(__name__)
# Explicitly allow all origins and set async_mode
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Hardware Setup
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = 8 
chan = AnalogIn(ads, 0, 1)
SENSITIVITY = 30.0

def read_sensor():
    while True:
        sum_sq = 0
        num_samples = 150 
        for _ in range(num_samples):
            v = chan.voltage
            sum_sq += v * v
        
        rms_v = math.sqrt(sum_sq / num_samples)
        current = rms_v * SENSITIVITY
        
        # Use 'broadcast=True' to force it to all connected browsers
        socketio.emit('new_data', {'value': round(current, 3)})
        print(f"Broadcasted: {current:.3f} A") 
        socketio.sleep(1) # Using socketio.sleep is safer than time.sleep inside the thread

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    sensor_thread = threading.Thread(target=read_sensor)
    sensor_thread.daemon = True
    sensor_thread.start()
    # Port 5000 is fine, but make sure no other process is using it
    socketio.run(app, host='192.168.0.236', port=5000)
