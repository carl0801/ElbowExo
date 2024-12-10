import matplotlib.pyplot as plt
from libraries import loadData, emg_signal
import librosa

signal = emg_signal.Signal()

shimmerBiceps = loadData.loadShimmer(n=1)
shimmerTriceps = loadData.loadShimmer(n=0)

signal.set_signal(shimmerBiceps[:, 1], shimmerBiceps[:, 2])
filtered_biceps = signal.get_filtered_signals()
filtered_biceps = filtered_biceps[0]
biceps_time = shimmerBiceps[:, 0]
biceps_mask = (biceps_time >= 12) & (biceps_time <= 21)
filtered_biceps = filtered_biceps[biceps_mask]
raw_biceps = signal.raw_signals[0, biceps_mask]
biceps_time = biceps_time[biceps_mask]
biceps_time -= biceps_time[0]

signal.set_signal(shimmerTriceps[:, 1], shimmerTriceps[:, 2])
filtered_triceps = signal.get_filtered_signals()
filtered_triceps = filtered_triceps[1]
triceps_time = shimmerTriceps[:, 0]
triceps_mask = (triceps_time >= 14) & (triceps_time <= 23)
filtered_triceps = filtered_triceps[triceps_mask]
raw_triceps = signal.raw_signals[1, triceps_mask]
triceps_time = triceps_time[triceps_mask]
triceps_time -= triceps_time[0]

# Plot
# Make 2 subplots of the 2 sensors from shimmer
""" plt.figure(figsize=(14, 5))
plt.style.use('seaborn-v0_8-paper')
plt.subplot(2, 1, 1)
plt.plot(biceps_time, raw_biceps, color='tab:blue')
plt.title('Measureing Biceps Data') 
plt.xlabel('Time [s]')
plt.ylabel('Value [mV]')
plt.subplot(2, 1, 2)
plt.plot(triceps_time, raw_triceps, color='tab:orange')
plt.title('Measureing Triceps Data')
plt.xlabel('Time [s]')
plt.ylabel('Value [mV]')
plt.tight_layout()
plt.savefig('shimmerSignal.png')
plt.show() """

# Make mel spectogram
fig, axs = plt.subplots(nrows=2, ncols=2, figsize=(12, 6), gridspec_kw={'height_ratios': [2, 1]})
plt.style.use('seaborn-v0_8-paper')
fig.suptitle('Frequencies of Raw Signals')

# Unfiltered signal bicep
ax = axs[0, 0]
X = librosa.stft(raw_biceps, n_fft=256)
Xdb = librosa.amplitude_to_db(abs(X))
librosa.display.specshow(Xdb, sr=650, x_axis='time', y_axis='hz', ax=ax)
ax.set_xlabel('Time [s]')
ax.set_title('Biceps - Unfiltered')

ax = axs[1, 0]
ax.plot(biceps_time, raw_biceps)
ax.set_xlabel('Time [s]')
ax.set_ylabel('Value [mV]')

# Unfiltered signal tricep
ax = axs[0, 1]
X = librosa.stft(raw_triceps, n_fft=256)
Xdb = librosa.amplitude_to_db(abs(X))
librosa.display.specshow(Xdb, sr=650, x_axis='time', y_axis='hz', ax=ax)
ax.set_xlabel('Time [s]')
ax.set_title('Triceps - Unfiltered')

ax = axs[1, 1]
ax.plot(triceps_time, raw_triceps)
ax.set_xlabel('Time [s]')
ax.set_ylabel('Value [mV]')

fig.tight_layout()

plt.savefig('shimmerSignal.png') 
plt.show()


fig, axs = plt.subplots(nrows=2, ncols=2, figsize=(12, 6), gridspec_kw={'height_ratios': [2, 1]})
plt.style.use('seaborn-v0_8-paper')
fig.suptitle('Frequencies of Filtered Signals')

# Filtered signal bicep
ax = axs[0, 0]
X = librosa.stft(filtered_biceps, n_fft=256)
Xdb = librosa.amplitude_to_db(abs(X))
librosa.display.specshow(Xdb, sr=650, x_axis='time', y_axis='hz', ax=ax)
ax.set_xlabel('Time [s]')
ax.set_title('Biceps - Filtered')

ax = axs[1, 0]
ax.plot(biceps_time, filtered_biceps)
ax.set_xlabel('Time [s]')
ax.set_ylabel('Value [mV]')

# Filtered signal tricep
ax = axs[0, 1]
X = librosa.stft(filtered_triceps, n_fft=256)
Xdb = librosa.amplitude_to_db(abs(X))
librosa.display.specshow(Xdb, sr=650, x_axis='time', y_axis='hz', ax=ax)
ax.set_xlabel('Time [s]')
ax.set_title('Triceps - Filtered')

ax = axs[1, 1]
ax.plot(triceps_time, filtered_triceps)
ax.set_xlabel('Time [s]')
ax.set_ylabel('Value [mV]')

fig.tight_layout()

plt.savefig('melSpectogramFiltVsNonfilt.png') 
plt.show()
