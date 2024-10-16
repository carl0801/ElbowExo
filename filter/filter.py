import numpy as np
from scipy.signal import butter, filtfilt, iirnotch

def butter_bandpass(lowcut, highcut, fs, order=6):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def notch_filter(freq, fs, quality_factor=30):
    nyq = 0.5 * fs
    notch_freq = freq / nyq
    b, a = iirnotch(notch_freq, quality_factor)
    return b, a

def moving_average_filter(data, window_size):
    return np.convolve(data, np.ones(window_size)/window_size, mode='same')

def generate_filter(fs=650, lowcut=20.0, highcut=250.0, notch_freq=50.0):
    # butterworth bandpass filter
    b_b, b_a = butter_bandpass(lowcut, highcut, fs)
    # notch filter
    n_b, n_a = notch_filter(notch_freq, fs)
    return [b_b, b_a, n_b, n_a]

def filter_emg_data(data, coeff=generate_filter(), threshold=10.0, window_size=200):
    # Step 1: Bandpass filter between 20 Hz and 250 Hz
    filtered_data = filtfilt(coeff[0], coeff[1], data)
    
    # Step 2: Notch filter around 50 Hz
    filtered_data = filtfilt(coeff[2], coeff[3], filtered_data)

    # Step 3: threshold above or below value
    filtered_data = np.where(np.abs(filtered_data) > threshold, filtered_data, 0)

    # Step 4: Abs and moving average
    filtered_data = np.abs(filtered_data)
    filtered_data = moving_average_filter(filtered_data, window_size)

    return filtered_data

def combine_sensors(sensor1, sensor2, multiplier=2.5):
    return sensor1 - multiplier * sensor2

def run(sensor1, sensor2, filter=generate_filter()):
    filtered_sensor1 = filter_emg_data(sensor1, filter)
    filtered_sensor2 = filter_emg_data(sensor2, filter)
    combined_sensor = combine_sensors(filtered_sensor1, filtered_sensor2)
    return combined_sensor
    

if __name__ == '__main__':
    import time
    import loadData
    import matplotlib.pyplot as plt
    # Load the data from the .npz file
    data, _ = loadData.load(n=0)

    # Extract the timestamps and the GSR data
    timestamps = data[:, 0]
    sensor1_data = data[:, 1]
    sensor2_data = data[:, 2]
    t = timestamps

    # Generate the filter coefficients
    filter = generate_filter()

    # Apply the filter
    start = time.time()
    signal = run(sensor1_data, sensor2_data, filter)
    end = time.time()
    samples = len(sensor1_data)
    print('Time taken to filter the signal: %.2f s' % (end - start))
    print('Time per sample: %.2f ms' % ((end - start) / samples * 1000))
    print('Samples per second: %.2f' % (1 / ((end - start) / samples)))

    # Plotting the results
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 1, 1)
    plt.plot(t, sensor1_data, label='EMG Signal 1')
    plt.plot(t, sensor2_data, label='EMG Signal 2')
    plt.title('Original EMG Signal with Noise')
    plt.subplot(2, 1, 2)
    plt.plot(t, signal, label='Filtered Signal')    
    plt.title('Filtered EMG Signal')
    plt.xlabel('Time [s]')
    plt.tight_layout()
    plt.legend()
    plt.show()