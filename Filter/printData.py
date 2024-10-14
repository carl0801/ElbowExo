import pickle
import matplotlib.pyplot as plt
import glob
import os
import numpy as np

# Find files with the highest number
files = glob.glob('data/[0-9.]*-shimmer.pkl') + glob.glob('data/[0-9.]*-loadcell.pkl')
files.sort(key=lambda x: list(map(float, os.path.splitext(os.path.basename(x))[0].split('-')[0].split('.'))), reverse=True)
data1 = pickle.load(open(files[0], 'rb'))
data2 = pickle.load(open(files[1], 'rb'))
if len(data1[0]) > len(data2[0]):
    shimmerData = data1
    loadcellData = data2
else:
    shimmerData = data2
    loadcellData = data1
shimmerData = np.array(shimmerData)
loadcellData = np.array(loadcellData, dtype=float)

# Shimmer data is stored in an array where each entry contain (time, sensor1, sensor2)
# Loadcell data is stored in an array where each entry contain (time, sensor)
# Shimmer time is in seconds, and loadcell is in miliseconds, but the clock they oprate after is not the same
# They start at different times, but the readings end at the same time, so that is how they should be calibrate

loadcellData = loadcellData / 1000

# Get the time of the last data point
last_time_shimmer = shimmerData[-1][0]
last_time_loadcell = loadcellData[-1][0]

# The time difference is the difference between the last time of the two systems
time_diff = last_time_loadcell - last_time_shimmer

# Calibrate the time of the loadcell
loadcellData[:, 0] = loadcellData[:, 0] - time_diff

# Print length
print(len(shimmerData))
print(len(loadcellData))

# Print last 10 entries
print(shimmerData[-10:])
print(loadcellData[-10:])

# Plot the data in subplots
plt.figure()
plt.subplot(2, 1, 1)
plt.plot(shimmerData[:, 0], shimmerData[:, 1])
plt.plot(shimmerData[:, 0], shimmerData[:, 2])
plt.title('Shimmer Data')
plt.xlabel('Time [s]')
plt.ylabel('Sensor Values')
plt.subplot(2, 1, 2)
plt.plot(loadcellData[:, 0], loadcellData[:, 1])
plt.title('Loadcell Data')
plt.xlabel('Time [s]')
plt.ylabel('Sensor Value')
plt.show()