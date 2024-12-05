import numpy as np
from scipy.signal import butter, sosfiltfilt

def butter_bandpass(lowcut, highcut, fs, order=4):
    sos = butter(order, [lowcut, highcut], btype='bandpass', fs=fs, output='sos')
    return sos

def notch_filter(freq, fs, order=5):
    sos  = butter(order, [freq-2.0, freq+2.0], btype='bandstop', fs=fs, output='sos')
    return sos

def generate_sos(fs=650, lowcut=20.0, highcut=250.0, notch_freq=50.0):
    """
    Generate second-order sections for filtering EMG data.

    Parameters
    ----------
    fs : int
        Sampling frequency (Hz).
    lowcut : float
        Lower cutoff frequency of the bandpass filter (Hz).
    highcut : float
        Upper cutoff frequency of the bandpass filter (Hz).
    notch_freq : float
        Frequency at which the notch filter is applied (Hz).

    Returns
    -------
    sos : array-like
        Second-order sections for filtering EMG data.
    """
    # butterworth bandpass filter
    sos_b = butter_bandpass(lowcut, highcut, fs)
    # notch filter
    sos_n = notch_filter(notch_freq, fs)
    # Stack the sos matrices
    sos = np.vstack((sos_b, sos_n))
    return sos
    

class Signal:
    def __init__(self, fs=650, lowcut=20.0, highcut=250.0, notch_freq=50.0, window=65, threshold=0.2, multiplier_biceps=1.0, multiplier_triceps=1.0, convolve_window_size=65*4):
        self.fs = fs
        self.lowcut = lowcut
        self.highcut = highcut
        self.notch_freq = notch_freq
        self.window = window
        self.threshold = threshold
        self.multiplier_biceps = multiplier_biceps
        self.multiplier_triceps = multiplier_triceps
        self.convolve_window_size = convolve_window_size
        self.sos = generate_sos(fs=self.fs, lowcut=self.lowcut, highcut=self.highcut, notch_freq=self.notch_freq)
        self.raw_signals = None
        self.filtered_signals = None
        self.control_signal = None
        self.control_value = None

    def set_multipliers(self, multiplier_biceps, multiplier_triceps):
        self.multiplier_biceps = multiplier_biceps
        self.multiplier_triceps = multiplier_triceps

    def set_signal(self, sensor1_data, sensor2_data):
        data = np.vstack((sensor1_data, sensor2_data))
        # Calibrate (mV value / max value * raw value) / gain
        self.raw_signals = (2420 / (2 ** 16 -1) * data) / 12

    def filter(self):
        # Filter
        self.filtered_signals = sosfiltfilt(self.sos, self.raw_signals)

    def control(self):
        # Combine the sensors
        control_signals = np.abs(self.filtered_signals)
        control_signal = control_signals[0] * self.multiplier_biceps - control_signals[1] * self.multiplier_triceps
        # Threshold
        control_signal = np.where(np.abs(control_signal) > self.threshold, control_signal, 0)
        # Moving average
        control_signal = np.convolve(control_signal, np.ones(self.convolve_window_size)/self.convolve_window_size, mode='same')
        # Try to get closer to peak value (from mean to max on sinusodial wave)
        self.control_signal = control_signal / 0.637
        # Return the mean of the last window values
        self.control_value = np.mean(control_signal[-self.window:])
        
    def get_control_value(self):
        self.filter()
        self.control()
        return self.control_value

    def get_control_signal(self):
        self.filter()
        self.control()
        return self.control_signal

    def get_filtered_signals(self):
        self.filter()
        return self.filtered_signals   
    