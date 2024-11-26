import filter
import loadData
import matplotlib.pyplot as plt
import emg_signal
import numpy as np

shimmer_data = loadData.loadShimmer(n=1)

# Filter
shimmer_signal = emg_signal.Signal()
shimmer_signal.set_signal(shimmer_data[:, 1], shimmer_data[:, 2])
print(shimmer_signal.sos)
print(np.asarray(shimmer_signal.raw_signals))
filtered_data = filter.sosfiltfilt(shimmer_signal.sos, np.asarray(shimmer_signal.raw_signals))

# plot
plt.figure()
plt.plot(shimmer_data[:, 0], shimmer_data[:, 1], label='Sensor 1')
plt.plot(shimmer_data[:, 0], shimmer_data[:, 2], label='Sensor 2')
plt.plot(shimmer_data[:, 0], filtered_data[0], label='Filtered Sensor 1')
plt.plot(shimmer_data[:, 0], filtered_data[1], label='Filtered Sensor 2')
plt.legend()
plt.title('Filtered Shimmer Data')
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')
plt.show()

