import loadData
import matplotlib.pyplot as plt
import filter

shimmer_data = loadData.loadShimmer(n=2)

# Plot 
""" plt.figure()
plt.plot(shimmer_data[:, 0], shimmer_data[:, 1], label='Sensor 1')
#plt.plot(shimmer_data[:, 0], shimmer_data[:, 2], label='Sensor 2')
plt.legend()
plt.title('Shimmer Data')
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')
plt.show() """

# Filter
filter_obj = filter.Filter()
filtered_data = filter_obj.run(shimmer_data[:, 1], shimmer_data[:, 2])

plt.figure()
plt.plot(shimmer_data[:, 0], filtered_data[0], label='Sensor 1')
plt.plot(shimmer_data[:, 0], filtered_data[1], label='Sensor 2')
plt.legend()
plt.title('Filtered Shimmer Data')
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')
plt.show()
