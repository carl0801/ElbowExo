import pickle
import matplotlib.pyplot as plt
import glob
import os
import numpy as np
import loadData

shimmerBiceps = loadData.loadShimmer(n=3)
shimmerTriceps = loadData.loadShimmer(n=2)


# Plot the data in subplots
""" plt.figure()
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
plt.show() """

# Calibrate shimemr data
def cal(data):
    data = 2420 / (2 ** 16 -1) * data
    data = data / 12
    #offset = np.mean(data)
    #data = data - offset
    #print(f"ADC-sensitivity: {2420 / (2 ** 15 -1)}")
    return data

# Make 2 subplots of the 2 sensors from shimmer
plt.figure(figsize=(14, 5))
plt.style.use('seaborn-v0_8-paper')
plt.subplot(2, 1, 1)
plt.plot(shimmerBiceps[:, 0], cal(shimmerBiceps[:, 1]))
plt.title('Measureing Biceps Data') 
plt.xlabel('Time [s]')
plt.ylabel('Value [mV]')
plt.xlim(12, 21)
#plt.ylim(-1.1, -0.75)
plt.subplot(2, 1, 2)
plt.plot(shimmerTriceps[:, 0], cal(shimmerTriceps[:, 2]), color='tab:orange')
plt.title('Measureing Triceps Data')
plt.xlabel('Time [s]')
plt.ylabel('Value [mV]')
plt.xlim(14, 23)
#plt.ylim(5.1, 5.4)
plt.tight_layout()
plt.savefig('shimmerSignal.png')
#plt.show()

# Make mel spectogram
""" from librosa.display import specshow
import librosa
X = librosa.stft(cal(shimmerData[:, 1]))
Xdb = librosa.amplitude_to_db(abs(X))
plt.figure(figsize=(14, 5))
specshow(Xdb, sr=650, x_axis='time', y_axis='hz')
plt.colorbar(format='%+2.0f dB')
plt.title('Mel Spectogram')
plt.tight_layout()
plt.style.use('seaborn-v0_8-paper')
plt.savefig('melSpectogram.png')  """