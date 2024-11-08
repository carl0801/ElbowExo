import matplotlib.pyplot as plt
import numpy as np
import filter

# Load the data from the .npz file
data = np.load('RawMeasurements\BevægelseVertikaltFlexEx.npz')['data']

# Extract the timestamps and the GSR data
timestamps = data[:, 0]
sensor1_data = data[:, 1]
sensor2_data = data[:, 2]
up = data[:, 3]
down = data[:, 4]

# Define the high pass filter parameters
fs = 650
cutoff = 5

test = filter.generate_filter(fs=650)
sensor_data = filter.run(sensor1_data,sensor2_data, test)
 

plt.figure()
plt.plot(timestamps, sensor_data, label='Sensor 1')
#plt.plot(timestamps, sensor2_data, label='Sensor 2')

""" # Change background color based on 'up' and 'down' values
for i in range(len(timestamps)):
    if up[i] == 1:
        plt.axvspan(timestamps[i], timestamps[i+1] if i+1 < len(timestamps) else timestamps[i], color='lightgreen', alpha=0.3)
    elif down[i] == 1:
        plt.axvspan(timestamps[i], timestamps[i+1] if i+1 < len(timestamps) else timestamps[i], color='pink', alpha=0.3)
 """


plt.xlabel('Timestamp')
plt.ylabel('EMG Data')
plt.legend()
plt.show()


