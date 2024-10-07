import matplotlib.pyplot as plt
import numpy as np
import Filter.filter as filter

# Load the data from the .npz file
data = np.load('BevægelseHorisontalt.npz')['data']

# Extract the timestamps and the GSR data
timestamps = data[:, 0]
sensor1_data = data[:, 1]
sensor2_data = data[:, 2]
up = data[:, 3]
down = data[:, 4]

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

def calibrate(data):
    ADC_GAIN = 12
    ADC_sensitivity = 2420/((2**15) -1)
    return (data * ADC_sensitivity) / ADC_GAIN

# Define the high pass filter parameters
fs = 650
cutoff = 5

""" # Apply the high pass filter to the GSR data
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
sensor2_data = moving_average(sensor2_data, window_size) """

""" # calculate the derivative of the data
sensor1_data = np.gradient(sensor1_data)
sensor2_data = np.gradient(sensor2_data)
 """
sensor1_data = calibrate(sensor1_data)
sensor2_data = calibrate(sensor2_data)

#Filter the data

test = filter.generate_filter()
sensor1_data = filter.array_run(sensor1_data, test)
sensor2_data = filter.array_run(sensor2_data, test)






plt.figure()
plt.plot(timestamps, sensor1_data, label='Sensor 1')
plt.plot(timestamps, sensor2_data, label='Sensor 2')

# Change background color based on 'up' and 'down' values
for i in range(len(timestamps)):
    if up[i] == 1:
        plt.axvspan(timestamps[i], timestamps[i+1] if i+1 < len(timestamps) else timestamps[i], color='lightgreen', alpha=0.3)
    elif down[i] == 1:
        plt.axvspan(timestamps[i], timestamps[i+1] if i+1 < len(timestamps) else timestamps[i], color='pink', alpha=0.3)



plt.xlabel('Timestamp')
plt.ylabel('EMG Data')
plt.legend()
plt.show()


