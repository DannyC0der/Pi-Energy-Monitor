#!/usr/bin/env python3
import board
import busio
import adafruit_ads1x15.ads1115 as ADS

print("Testing ADC library...")

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = 1

print("✓ ADC initialized")

# Try reading channel 0
try:
    value = ads.read(0)
    voltage = value * 4.096 / 32767
    print(f"✓ Raw value: {value}")
    print(f"✓ Voltage: {voltage:.3f}V")
    print("\n✓ Library works!")
except Exception as e:
    print(f"✗ Error: {e}")
