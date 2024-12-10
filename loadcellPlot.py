from libraries import loadData, emg_signal
import matplotlib.pyplot as plt

shimmerData, loadcellData = loadData.load(n=5)
signal = emg_signal.Signal()

signal.set_signal(shimmerData[:, 1], shimmerData[:, 2])
filtered_signals = signal.get_filtered_signals()
control_signal = signal.get_control_signal()

# Plot
fig, axs = plt.subplots(2, 1, figsize=(8, 6), gridspec_kw={'height_ratios': [3, 1]})

ax1 = axs[0]
ax2 = ax1.twinx()
ax3 = axs[1]

loadcell_line, = ax1.plot(loadcellData[:, 0], -loadcellData[:, 1], 'tab:green', label='Loadcell')
control_signal_line, = ax2.plot(shimmerData[:, 0], control_signal, 'tab:red', label='Control Signal')

ax1.set_xlabel('Time [s]')
ax1.set_ylabel('Loadcell [g]', color='tab:green')
ax2.set_ylabel('Control Signal [mV]', color='tab:red')

ax1.tick_params(axis='y', colors='tab:green')
ax2.tick_params(axis='y', colors='tab:red')

ax1.legend(handles=[loadcell_line, control_signal_line])

ax1_ylim = ax1.get_ylim()
ax2_ylim = ax2.get_ylim()
# Find scaling factor
scalefactor_min = ax2_ylim[0] / ax1_ylim[0]
scalefactor_max = ax2_ylim[1] / ax1_ylim[1]
scalefactor = min(scalefactor_min, scalefactor_max)

# Scale ax2
ax2.set_ylim(ax1_ylim[0] * scalefactor, ax1_ylim[1] * scalefactor)

ax3.plot(shimmerData[:, 0], filtered_signals[0], 'tab:blue', label='Biceps Signal')
ax3.plot(shimmerData[:, 0], filtered_signals[1], 'tab:orange', label='Triceps Signal')
ax3.set_xlabel('Time [s]')
ax3.set_ylabel('Filtered Signal [mV]')
ax3.legend(loc='upper right')
ax3.title.set_text('Filtered EMG Signals')

plt.tight_layout()
plt.title('Initial Validation of Muscle Control Method')
plt.tight_layout()
plt.savefig('controlValidation.png')
plt.show()
