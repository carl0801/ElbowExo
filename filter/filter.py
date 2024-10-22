import numpy as np
from scipy.signal import butter, sosfiltfilt

def butter_bandpass(lowcut, highcut, fs, order=6):
    sos = butter(order, [lowcut, highcut], btype='bandpass', fs=fs, output='sos')
    return sos

def notch_filter(freq, fs, order=5):
    sos  = butter(order, [freq-2.0, freq+2.0], btype='bandstop', fs=fs, output='sos')
    return sos

def generate_filter(fs=650, lowcut=20.0, highcut=250.0, notch_freq=50.0):
    # butterworth bandpass filter
    sos_b = butter_bandpass(lowcut, highcut, fs)
    # notch filter
    sos_n = notch_filter(notch_freq, fs)
    return [sos_b, sos_n]

def filter_emg_data(data, coeff=generate_filter()):
    # Bandpass filter between 20 Hz and 250 Hz
    filtered_data = sosfiltfilt(coeff[0], data)
    # Notch filter around 50 Hz
    filtered_data = sosfiltfilt(coeff[1], filtered_data)
    # Abs
    filtered_data = np.abs(filtered_data)
    return filtered_data

def combine_sensors(sensor1, sensor2, multiplier=3.0):
    return sensor1 - multiplier * sensor2

def run(sensor1, sensor2, filter=generate_filter(), single_window=0, threshold=5.0, multiplier=3.0, window_size=300):
    """
    This function takes in the sensor data, filters it, combines it, 
    thresholds it, and then takes the moving average. If single_window is 
    not equal to 0, it will return the mean of the last "single_window" 
    values of the filtered data. Otherwise it will return the entire
    filtered data. 

    Parameters
    ----------
    sensor1 : array
        The data from sensor 1
    sensor2 : array
        The data from sensor 2
    filter : list
        The coefficients for the filter
    single_window : int
        The number of data points to average
    threshold : float
        The minimum absolute value of the data
    multiplier : float
        The multiplier for the second sensor
    window_size : int
        The size of the window for the moving average

    Returns
    -------
    filtered_data : array
        The filtered data
    """
    filtered_sensor1 = filter_emg_data(sensor1, filter)
    filtered_sensor2 = filter_emg_data(sensor2, filter)
    # combine the sensors
    combined_sensor = combine_sensors(filtered_sensor1, filtered_sensor2, multiplier)
    # threshold
    combined_sensor = np.where(np.abs(combined_sensor) > threshold, combined_sensor, 0)
    # moving average
    combined_sensor = np.convolve(combined_sensor, np.ones(window_size)/window_size, mode='same')
    if single_window != 0:
        value = np.mean(combined_sensor[single_window:])
        return value

    return combined_sensor
    
    
    

if __name__ == '__main__':
    import time
    import loadData
    import matplotlib.pyplot as plt

    # Load the data from the .npz file
    data, loadcell = loadData.load(n=0)

    # Extract the timestamps and the GSR data
    timestamps = data[:, 0]
    t = timestamps
    sensor1_data = data[:, 1]
    sensor2_data = data[:, 2]
    fs = 650

    # Generate the filter coefficients
    filter = generate_filter(fs=fs)

    # Apply the filter
    start = time.time()
    signal = run(sensor1_data, sensor2_data, filter)
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
    
    