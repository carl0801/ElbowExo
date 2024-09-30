import matplotlib.pyplot as plt
import numpy as np


# Load the data from the .npz file
data = np.load('shimmer_data.npz')['data']

# Extract the timestamps and the GSR data
timestamps = data[:, 0]
timeRTCstart = data[:, 1]
timeRTCcurrent = data[:, 2]
sensor1_data = data[:, 3]
sensor2_data = data[:, 4]


# Plot the GSR data, GSR stands for Galvanic Skin Response
plt.figure()
plt.plot(timestamps, sensor1_data, label='Sensor 1')
plt.plot(timestamps, sensor2_data, label='Sensor 2')

plt.xlabel('Timestamp')
plt.ylabel('GSR Data')
plt.legend()
plt.show()



