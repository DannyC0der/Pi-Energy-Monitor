#!/usr/bin/env python3
"""
ADC Reader v3 - With detailed error reporting
"""

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
import time
import numpy as np

class CurrentSensor:
    def __init__(self):
        print("Initializing sensor...")
        
        # Initialize I2C and ADC
        i2c = busio.I2C(board.SCL, board.SDA)
        self.ads = ADS.ADS1115(i2c)
        self.ads.gain = 1
        
        # Configuration
        self.burden_resistor = 100
        self.ct_ratio = 2000
        
        print("✓ Sensor initialized")
        print(f"✓ Burden resistor: {self.burden_resistor}Ω\n")
    
    def read_voltage_direct(self):
        """Read voltage using direct channel access"""
        try:
            # Read differential channel 0-1
            # ADS1115 has channels 0,1,2,3
            # We're reading channel 0 referenced to channel 1
            raw = self.ads.read_adc_difference(0)
            
            # Convert to voltage
            # gain=1 gives ±4.096V range over 16-bit signed integer
            voltage = raw * 4.096 / 32768.0
            
            return voltage
            
        except AttributeError:
            # If read_adc_difference doesn't exist, try alternative
            print("Trying alternative read method...")
            raw = self.ads.read(0, is_differential=False)
            voltage = raw * 4.096 / 32768.0
            return voltage
    
    def test_single_read(self):
        """Test a single ADC reading"""
        print("Testing single ADC read...")
        try:
            voltage = self.read_voltage_direct()
            print(f"✓ Single read successful: {voltage:.4f}V")
            return True
        except Exception as e:
            print(f"✗ Single read failed: {e}")
            return False
    
    def read_samples(self, duration=1.0):
        """Collect samples for specified duration"""
        samples = []
        start_time = time.time()
        read_count = 0
        error_count = 0
        
        print(f"Collecting samples for {duration} second(s)...")
        
        while time.time() - start_time < duration:
            try:
                voltage = self.read_voltage_direct()
                samples.append(voltage)
                read_count += 1
                time.sleep(0.001)  # ~1ms between samples
                
            except Exception as e:
                error_count += 1
                if error_count < 5:  # Only print first few errors
                    print(f"  Read error #{error_count}: {e}")
                continue
        
        print(f"✓ Collected {len(samples)} samples ({error_count} errors)")
        
        if len(samples) == 0:
            print("✗ ERROR: No samples collected!")
            print("  This usually means:")
            print("  1. ADC wiring is incorrect")
            print("  2. ADC is not responding")
            print("  3. I2C communication problem")
            return None
        
        return np.array(samples)
    
    def calculate_current(self, samples):
        """Calculate RMS current from samples"""
        if samples is None or len(samples) == 0:
            return 0.0
        
        # Remove DC offset
        ac_samples = samples - np.mean(samples)
        
        # RMS voltage
        rms_voltage = np.sqrt(np.mean(ac_samples**2))
        
        # Convert to current
        current = (rms_voltage / self.burden_resistor) * self.ct_ratio
        
        return current
    
    def test(self):
        """Run test"""
        print("\n" + "="*50)
        print("TESTING CURRENT SENSOR")
        print("="*50)
        
        # First test single read
        if not self.test_single_read():
            print("\n✗ Cannot proceed - single read failed")
            return None, None
        
        print()
        
        # Collect samples
        samples = self.read_samples(1.0)
        
        if samples is None:
            return None, None
        
        # Calculate values
        current = self.calculate_current(samples)
        power = current * 230
        
        print(f"\nVoltage range: {np.min(samples):.4f}V to {np.max(samples):.4f}V")
        print(f"Mean voltage: {np.mean(samples):.4f}V")
        print(f"RMS voltage: {np.sqrt(np.mean(samples**2)):.4f}V")
        print(f"\n✓ Current: {current:.3f} A")
        print(f"✓ Power: {power:.1f} W")
        print("="*50)
        
        return current, power

# Main
if __name__ == "__main__":
    print("\n" + "="*50)
    print("ADC READER V3 - DIAGNOSTIC VERSION")
    print("="*50)
    print()
    
    try:
        sensor = CurrentSensor()
        
        print("\nStarting continuous monitoring...")
        print("Press Ctrl+C to stop\n")
        
        while True:
            result = sensor.test()
            if result[0] is None:
                print("\n✗ Test failed - stopping")
                break
            
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n\n✓ Stopped by user!")
        
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
