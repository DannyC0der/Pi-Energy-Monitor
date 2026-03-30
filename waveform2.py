import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import butter, filtfilt
from scipy.fft import fft, fftfreq

# ==========================================
# --- 1. SETTINGS & HARDWARE SETUP ---
# ==========================================
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# MUST MATCH YOUR HARDWARE:
# For Differential Mode (A0-A1) with 1.635V bias and small laptop charger load
# Gain 8 (+/- 0.512V) is usually safe for <150W loads.
ads.gain = 8 
chan = AnalogIn(ads, 0, 1)

SENSITIVITY = 30.0  # 30A / 1V output
DURATION = 10       # Seconds to record
AC_FREQ = 50        # AC Frequency (Hz) (50 for UK, 60 for US)

# Lists to store the data
raw_timestamps = []
raw_current = []

# ==========================================
# --- 2. DATA COLLECTION LOOP (Fast as possible) ---
# ==========================================
print(f"Recording for {DURATION} seconds... Start the load now!")
start_time = time.time()

while (time.time() - start_time) < DURATION:
    now = time.time() - start_time
    # Record timestamp and instantaneous current
    raw_timestamps.append(now)
    # The Differential signal is already centered near 0
    raw_current.append(chan.voltage * SENSITIVITY)

# Convert lists to NumPy arrays for faster processing
t = np.array(raw_timestamps)
y_raw = np.array(raw_current)
n = len(y_raw)
actual_fs = n / DURATION  # Calculate actual sampling frequency (samples per second)

print(f"Captured {n} samples (fs = {actual_fs:.1f} Hz).")

# ==========================================
# --- 3. SIGNAL PROCESSING (DSP) ---
# ==========================================

def apply_butterworth_filter(data, cutoff, fs, order=5):
    """Applies a Butterworth Low-Pass Filter."""
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    # filtfilt applies the filter forward and backward, eliminating phase lag
    return filtfilt(b, a, data)

# Calculate Nyquist frequency
nyquist_limit = 0.5 * actual_fs
# Set cutoff to 150Hz, but ensure it's at least 10% below Nyquist to avoid the error
safe_cutoff = min(150, nyquist_limit * 0.9)

print(f"Nyquist limit: {nyquist_limit:.2f}Hz. Using safe cutoff: {safe_cutoff:.2f}Hz")

y_clean = apply_butterworth_filter(y_raw, safe_cutoff, actual_fs)

# ==========================================
# --- 4. FFT AMPLITUDE SPECTRUM ---
# ==========================================
# Compute the FFT
yf_raw = fft(y_clean)
xf_raw = fftfreq(n, 1/actual_fs)

# Only take the positive frequencies and scale the amplitude
xf = xf_raw[:n//2]
# Amplitude Scaling: Multiply by 2.0 (one-sided FFT) and divide by N (normalize)
yf = 2.0/n * np.abs(yf_raw[:n//2])

# ==========================================
# --- 5. VISUALIZATION ---
# ==========================================
print("Generating graphs...")
plt.figure(figsize=(12, 12))

# Subplot 1: The full 10s Time Domain capture (Raw AC Signal)
# (This replaces the top graph from image_1.png)
plt.subplot(3, 1, 1)
plt.plot(t, y_raw, color='blue', linewidth=0.5)
plt.title(f'Time Domain: Instantaneous Current (Raw Noisy Data, fs={actual_fs:.1f} Hz)')
plt.ylabel('Current (Amps)')
plt.grid(True)

# Subplot 2: Zoomed-in comparison of Raw vs. Filtered Signal (DSP)
# (This replaces the bottom graph from image_1.png with meaningful, cleaned data)
plt.subplot(3, 1, 2)
plt.plot(t, y_raw, color='lightgray', label='Raw (Noisy)', alpha=0.7)
plt.plot(t, y_clean, color='red', label='Filtered (Clean)', linewidth=2)
# Zoom into 0.1 seconds to show 5 complete 50Hz cycles 
plt.title(f'Time Domain: Full Filtered Waveform')
plt.ylabel('Current (Amps)')
plt.legend(loc='upper right')
plt.grid(True)

# Subplot 3: Frequency Domain: FFT Power Spectrum (The Signature)
# (The "clean signature" you asked for)
plt.subplot(3, 1, 3)
plt.stem(xf, yf, markerfmt=" ", basefmt=" ", linefmt="C0-")
plt.title('Frequency Domain: FFT Power Spectrum (The Appliance Signature)')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Amplitude (Amps Peak)')
# Focus on the region where harmonics live (0 to 300Hz)
plt.xlim(0, 180) 
plt.xticks([0, AC_FREQ, AC_FREQ*2, AC_FREQ*3, AC_FREQ*4, AC_FREQ*5]) # Mark the harmonics
plt.grid(True)

plt.tight_layout()
plt.savefig('complete_current_signature.png')
print("Complete DSP output saved as 'complete_current_signature.png'")
