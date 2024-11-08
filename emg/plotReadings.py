import matplotlib.pyplot as plt
import loadData

shimmerData, loadcellData = loadData.load(n=0)

# Plot the data with differnt y-axes in same plot
fig, ax1 = plt.subplots()
ax1.set_xlabel('Time [s]')
ax1.set_ylabel('EMG Signal')
ax1.plot(shimmerData[:, 0], shimmerData[:, 1], color='tab:red', label='Shimmer 1')
ax1.plot(shimmerData[:, 0], shimmerData[:, 2], color='tab:red', label='Shimmer 2')
ax1.tick_params(axis='y', labelcolor='tab:red')
ax2 = ax1.twinx()
ax2.set_ylabel('Loadcell Value')
ax2.plot(loadcellData[:, 0], loadcellData[:, 1], color='tab:blue', label='Loadcell')
ax2.tick_params(axis='y', labelcolor='tab:blue')
fig.tight_layout()
plt.show()