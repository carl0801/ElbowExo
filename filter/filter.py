import numpy as np
from scipy.signal import butter, sosfiltfilt

def calibrate(data):
    # ADC-sensitivity = 2420 / (2 ** 15 -1)
    """
    Calibrate the input data to mV unit.

    The function adjusts the input data by applying a scaling factor determined
    by the ADC sensitivity and further divides the result by the gain factor.

    Parameters
    ----------
    data : array-like
        The raw data to be calibrated.

    Returns
    -------
    array-like
        The calibrated data.
    """
    data = 2420 / (2 ** 16 -1) * data
    data = data / 12
    return data

def butter_bandpass(lowcut, highcut, fs, order=4):
    sos = butter(order, [lowcut, highcut], btype='bandpass', fs=fs, output='sos')
    return sos

def notch_filter(freq, fs, order=5):
    sos  = butter(order, [freq-2.0, freq+2.0], btype='bandstop', fs=fs, output='sos')
    return sos

def combine_signals(signals, multiplier=3.0):
    """
    Combine the two signals into a single signal.

    Parameters
    ----------
    signals : array_like
        The two signals to be combined. The first signal is the raw signal and
        the second signal is the noise signal.
    multiplier : float, optional
        The multiplier for the second signal. Defaults to 3.0.

    Returns
    -------
    signal : array_like
        The combined signal.
    """
    signals = np.abs(signals)
    signal = signals[0] - signals[1] * multiplier
    return signal

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

def run(sensor1, sensor2, sos=generate_sos(), window=0, threshold=5.0, multiplier=3.0, convolve_window_size=65*5):    
    """
    Filter the EMG signals from two sensors, combine them, apply a threshold and then
    take the moving average.

    Parameters
    ----------
    sensor1 : array_like
        The data from sensor 1
    sensor2 : array_like
        The data from sensor 2
    sos : array_like
        The second-order sections for filtering EMG data
    window : int
        The number of data points to average
    threshold : float
        The minimum absolute value of the data
    multiplier : float
        The multiplier for the second sensor
    convolve_window_size : int
        The size of the window for the moving average

    Returns
    -------
    signal : array_like
        The filtered and combined signal
    """
    # Calibrate
    sensor1 = calibrate(sensor1)
    sensor2 = calibrate(sensor2)
    signals = np.hstack((sensor1, sensor2))
    # Filter
    signals = sosfiltfilt(sos, signals)
    # Combine the sensors
    signal = combine_signals(signals, multiplier)
    # Threshold
    signal = np.where(np.abs(signal) > threshold, signal, 0)
    # Moving average
    signal = np.convolve(signal, np.ones(convolve_window_size)/convolve_window_size, mode='same')
    # Return the mean of the last window values
    if window != 0:
        value = np.mean(signal[window:])
        return value

    return signal
    
    
    

if __name__ == '__main__':
    import time
    import loadData
    import matplotlib.pyplot as plt

    # Load the data from the .npz file
    data, loadcell = loadData.load(n=5)

    # Extract the timestamps and the GSR data
    timestamps = data[:, 0]
    t = timestamps
    sensor1_data = data[:, 1]
    sensor2_data = data[:, 2]
    fs = 650

    # Generate the filter coefficients
    sos = generate_sos(fs=fs)

    # Apply the filter
    start = time.time()
    signal = run(sensor1_data, sensor2_data, sos)
    end = time.time()
    samples = len(sensor1_data)
    print('Time taken to filter the signal: %.2f s' % (end - start))
    print('Time per sample: %.2f ms' % ((end - start) / samples * 1000))
    print('Samples per second: %.2f' % (1 / ((end - start) / samples)))

    # Plotting the signal and loadcell on different y-axes twinx
    fig, ax1 = plt.subplots()
    ax1.set_xlabel('Time [s]')
    ax1.set_ylabel('EMG Signal')
    ax1.plot(t, signal, color='tab:red', label='EMG')
    ax1.tick_params(axis='y', labelcolor='tab:red')
    ax2 = ax1.twinx()
    ax2.set_ylabel('Loadcell Value')
    ax2.plot(loadcell[:, 0], loadcell[:, 1], color='tab:blue', label='Loadcell')
    ax2.tick_params(axis='y', labelcolor='tab:blue')
    fig.tight_layout()
    plt.show()
    
    