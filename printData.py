import pickle
import matplotlib.pyplot as plt
import glob
import os
import numpy as np
import loadData
from scipy.signal import butter, sosfiltfilt

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

def butter_bandpass(lowcut, highcut, fs, order=4):
    sos = butter(order, [lowcut, highcut], btype='bandpass', fs=fs, output='sos')
    return sos

def notch_filter(freq, fs, order=3):
    sos  = butter(order, [freq-1.5, freq+1.5], btype='bandstop', fs=fs, output='sos')
    return sos

def generate_sos(fs=650, lowcut=20.0, highcut=250.0, notch_freq=50.0):
    # butterworth bandpass filter
    sos_b = butter_bandpass(lowcut, highcut, fs)
    # notch filter
    sos_n = notch_filter(notch_freq, fs)
    # Test with more notch frq
    sos_n2 = notch_filter(notch_freq*2, fs)
    sos_n3 = notch_filter(notch_freq*3, fs)
    # Stack the sos matrices
    sos1 = np.vstack((sos_b, sos_n))
    sos2 = np.vstack((sos_b, sos_n, sos_n2, sos_n3))
    return sos1, sos2

""" # Make 2 subplots of the 2 sensors from shimmer
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
#plt.savefig('shimmerSignal.png')
plt.show() """

# Make mel spectogram
shimmerData = loadData.loadShimmer(n=7)
sos1, sos2 = generate_sos()
from librosa.display import specshow
import librosa
plt.figure(figsize=(16, 20))
plt.style.use('seaborn-v0_8-paper')

# Unfiltered signal
plt.subplot(4, 1, 1)
data = cal(shimmerData[:, 1])
X = librosa.stft(data)
Xdb = librosa.amplitude_to_db(abs(X))
specshow(Xdb, sr=650, x_axis='time', y_axis='hz')
plt.colorbar(format='%+2.0f dB')
plt.title('Mel Spectogram - Unfiltered Signal')

# Plot
plt.subplot(4, 1, 2)
plt.plot(shimmerData[:, 0], data)
plt.title('Unfiltered Signal') 
plt.xlabel('Time [s]')
plt.ylabel('Value [mV]')

# Filtered signal
plt.subplot(4, 1, 3)
data = sosfiltfilt(sos2, cal(shimmerData[:, 1]))
X = librosa.stft(data)
Xdb = librosa.amplitude_to_db(abs(X))
specshow(Xdb, sr=650, x_axis='time', y_axis='hz')
plt.colorbar(format='%+2.0f dB')
plt.title('Mel Spectogram - Filtered Signal')

# Plot
plt.subplot(4, 1, 4)
plt.plot(shimmerData[:, 0], data)
plt.title('Filtered Signal') 
plt.xlabel('Time [s]')
plt.ylabel('Value [mV]')


plt.tight_layout()

plt.savefig('melSpectogramFiltVsNonfilt.png') 
plt.show()