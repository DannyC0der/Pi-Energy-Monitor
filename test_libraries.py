import numpy
import pandas
import matplotlib
import scipy
import psutil
import requests
import flask 

print("Numpy version:", numpy.__version__)
print("Pandas version:", pandas.__version__)
print("Matplotlib version:", matplotlib.__version__)
print("Scipy version:", scipy.__version__)

print("CPU usage:", psutil.cpu_percent())
print("RAM usage:", psutil.virtual_memory().percent)

print("All lbraries imported successfully")
