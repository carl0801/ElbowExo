import numpy as np

# Load the data from the .npz file
data = np.load('shimmer_data4.npz')['data']

print('Data shape:', data.shape)

# Extract the timestamps and the GSR data
timestamps = data[:, 0]
sensor1_data = data[:, 1]
sensor2_data = data[:, 2]

# Find difference between timestamps
t = np.diff(timestamps)

print(timestamps)
# Print info
print('Time shape:', t.shape)
std = np.std(t)
print('Time std:', std)
print('Time mean:', np.mean(t))
print('Time min:', np.min(t))
print('Time max:', np.max(t))


