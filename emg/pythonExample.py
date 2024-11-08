import emg_rust
import numpy as np
import scipy.signal as signal
import time
import loadData
import matplotlib.pyplot as plt

shimmerData, loadcellData = loadData.load(n=0)

# Example usage
fs = 650
order = 12
lowcut = 20
highcut = 250
sos_matrix = signal.butter(order, [lowcut, highcut], btype='bandpass', fs=fs, output='sos')

# Sample signal
x = shimmerData[:, 1]
t = shimmerData[:, 0]

# Apply rust filtfilt
x_multiple = np.array([x] * 100)
start = time.time()
for i in range(100):
    y1 = emg_rust.sosfiltfilt(sos_matrix, x)
print("Time:", time.time() - start)

# Apply scipy filtfilt
start = time.time()
for i in range(100):
    y2 = signal.sosfiltfilt(sos_matrix, x)
print("Time:", time.time() - start)

# Compare results
print()
print("Original:", x[:10])
print()
print("Rust:", y1[:10])
print()
print("Scipy:", y2[:10])
print() 
diff = np.abs(y1 - y2)
print("Difference:", np.sum(diff)/len(diff))
print("Max difference:", np.max(diff))

# Plot
plt.figure(figsize=(12, 6))
plt.plot(t, x, label="original", marker="x", alpha=0.5, linestyle="dashed")
plt.plot(t, y1, label="rust", marker="x", alpha=0.5, linestyle="dashed")
plt.plot(t, y2, label="scipy", marker="x", alpha=0.5, linestyle="dashed")
plt.xlabel("Time [s]")
plt.ylabel("EMG Signal")
plt.legend()

#plt.show()