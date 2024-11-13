import loadData
import matplotlib.pyplot as plt
import emg_signal

shimmer_data = loadData.loadShimmer(n=1)

# Plot 
""" plt.figure()
plt.plot(shimmer_data[:, 0], shimmer_data[:, 1], label='Sensor 1')
plt.plot(shimmer_data[:, 0], shimmer_data[:, 2], label='Sensor 2')
plt.legend()
plt.title('Shimmer Data')
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')
plt.show() """

# Filter
shimmer_signal = emg_signal.Signal()
shimmer_signal.set_signal(shimmer_data[:, 1], shimmer_data[:, 2])
filtered_data = shimmer_signal.get_filtered_signals()
control_data = shimmer_signal.get_control_signal()

plt.figure()
plt.plot(shimmer_data[:, 0], filtered_data[0], label='Sensor 1')
plt.plot(shimmer_data[:, 0], filtered_data[1], label='Sensor 2')
plt.plot(shimmer_data[:, 0], control_data, label='Control Signal')
plt.legend()
plt.title('Filtered Shimmer Data')
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')
plt.show()
