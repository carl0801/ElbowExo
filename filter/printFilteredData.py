import pickle
import matplotlib.pyplot as plt
import glob
import os
import numpy as np
import filter
import loadData

shimmerData, loadcellData = loadData.load(n=5)

# Filter the data
coefficients = filter.generate_filter()
filtered_signal = filter.run(shimmerData[:, 1], shimmerData[:, 2], coefficients)

# Plot the data with differnt y-axes in same plot
fig, ax1 = plt.subplots()
ax1.set_xlabel('Time [s]')
ax1.set_ylabel('EMG Signal')
ax1.plot(shimmerData[:, 0], filtered_signal, color='tab:red', label='Shimmer')
ax1.tick_params(axis='y', labelcolor='tab:red')
ax2 = ax1.twinx()
ax2.set_ylabel('Loadcell Value')
ax2.plot(loadcellData[:, 0], loadcellData[:, 1], color='tab:blue', label='Loadcell')
ax2.tick_params(axis='y', labelcolor='tab:blue')
fig.tight_layout()
plt.show()