import matplotlib.pyplot as plt
import numpy as np


# Load the data from the .npz file
data = np.load('shimmer_data6.npz')['data']

# Extract the timestamps and the GSR data
timestamps = data[:, 0]
sensor1_data = data[:, 1]
sensor2_data = data[:, 2]

# Perform high pass filtering
from scipy.signal import butter, lfilter

def butter_highpass(cutoff, fs, order=5):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    return b, a

def highpass_filter(data, cutoff, fs, order=5):
    b, a = butter_highpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y

# Define the high pass filter parameters
fs = 512
cutoff = 5

# Apply the high pass filter to the GSR data
sensor1_data = highpass_filter(sensor1_data, cutoff, fs)
sensor2_data = highpass_filter(sensor2_data, cutoff, fs)

# Remove the first 2000 entries to remove the transient response
timestamps = timestamps[1024:]
sensor1_data = sensor1_data[1024:]
sensor2_data = sensor2_data[1024:]

# Absolute value of the data
sensor1_data = np.abs(sensor1_data)
sensor2_data = np.abs(sensor2_data)

# Moving average filter
def moving_average(data, window_size):
    return np.convolve(data, np.ones(window_size) / window_size, mode='same')

# Apply the moving average filter to the EMG data
window_size = 100
sensor1_data = moving_average(sensor1_data, window_size)
sensor2_data = moving_average(sensor2_data, window_size)

""" # calculate the derivative of the data
sensor1_data = np.gradient(sensor1_data)
sensor2_data = np.gradient(sensor2_data)
 """


plt.figure()
plt.plot(timestamps, sensor1_data, label='Sensor 1')
plt.plot(timestamps, sensor2_data, label='Sensor 2')


# Set y-axis range
plt.ylim(0, 100)

plt.xlabel('Timestamp')
plt.ylabel('EMG Data')
plt.legend()
plt.show()



