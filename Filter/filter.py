import numpy as np
from scipy.signal import firwin, lfilter, freqz
import matplotlib.pyplot as plt

# Generate filter coefficients
def generate_filter(fs=512, lowcut=20.0, highcut=250.0, notch_freq=50.0, numtaps=101):
    # Filter parameters
    #fs = 512  # Sampling frequency (1 kHz)
    #lowcut = 20.0  # Lower cutoff frequency for band-pass
    #highcut = 250.0  # Upper cutoff frequency for band-pass
    #notch_freq = 50.0  # Notch frequency
    #numtaps = 101  # Number of filter coefficients (taps)

    # Design the FIR band-pass filter
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq

    # Create the band-pass filter coefficients
    b_bp = firwin(numtaps, [low, high], pass_zero=False)

    # Design a notch filter for 50 Hz
    notch_width = 1.0  # Width of the notch around 50 Hz
    notch_low = (notch_freq - notch_width) / nyq
    notch_high = (notch_freq + notch_width) / nyq

    # Create the notch filter coefficients
    b_notch = firwin(numtaps, [notch_low, notch_high], pass_zero=True)

    # Combine the filters in series (using convolution)
    return np.convolve(b_bp, b_notch)

# Plot the frequency response of the filter
def plot_frequency_response(filter, fs=512, lowcut=20.0, highcut=250.0, notch_freq=50.0):
    # Frequency response
    w, h = freqz(filter, worN=1024)
    plt.figure(figsize=(8, 4))
    plt.plot(0.5 * fs * w / np.pi, np.abs(h), 'b')
    plt.title('Combined FIR Band-Pass and Notch Filter Frequency Response')
    plt.xlabel('Frequency [Hz]')
    plt.ylabel('Gain')
    plt.grid()
    plt.axvline(lowcut, color='green', linestyle='--')
    plt.axvline(highcut, color='green', linestyle='--')
    plt.axvline(notch_freq, color='red', linestyle='--')
    plt.xlim(0, 500)
    plt.show()

# Use a filter on a signal using block processing
def filter_data(data, filter=generate_filter(), windowsize=100):
    transient_response_length = int(len(filter) * 1.5)
    # Check if the data is smaller than the windowsize + transient response length
    if len(data) < windowsize + transient_response_length:
        print('Window size is too large to avoid transients')
        filtered_data = lfilter(filter, 1.0, data)
        return filtered_data
    else:
        filtered_data = lfilter(filter, 1.0, data[-windowsize-transient_response_length:])
        # Return the newset filtered data in windowsize
        return filtered_data[-windowsize:]

# Take abs and mean of the data
def process_data(data):
    # Find offset
    offset = np.mean(data)
    data = data - offset
    # Abs the data
    data = np.abs(data)
    # Avarage the data
    data = np.mean(data)
    return data

# Run filter and process data
def run(data, filter, windowsize=100):
    filtered_data = filter_data(data, filter, windowsize)
    processed_data = process_data(filtered_data)
    return processed_data

# 
def array_run(data, filter, windowsize=100):
    data_processed = []
    transient_response_length = int(len(filter) * 1.5)
    for i in range(len(data)):
        if i < windowsize + transient_response_length:
            data_processed.append(0)
            continue
        filtered_data = filter_data(data[:i], filter, windowsize)
        processed_data = process_data(filtered_data)
        data_processed.append(processed_data)
    data_processed = np.array(data_processed)
    return data_processed


if __name__ == '__main__':
    import time
    # Example usage: Generate a sample EMG signal
    # Load the data from the .npz file
    data = np.load('shimmer_data5.npz')['data']

    # Extract the timestamps and the GSR data
    timestamps = data[:, 0]
    sensor1_data = data[:, 1]
    sensor2_data = data[:, 2]
    t = timestamps

    # Generate the filter coefficients
    filter = generate_filter()

    # Apply the combined FIR filter
    start = time.time()
    filtered_signal1 = array_run(sensor1_data, filter)
    filtered_signal2 = array_run(sensor2_data, filter)
    end = time.time()
    print('Time taken to filter the signal: %.2f s' % (end - start))
    samples = len(sensor1_data)
    print('Time per sample: %.2f ms' % ((end - start) / samples * 1000))
    print('Samples per second: %.2f' % (1 / ((end - start) / samples)))

    # Plotting the results
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 1, 1)
    plt.plot(t, sensor1_data, label='EMG Signal 1')
    plt.plot(t, sensor2_data, label='EMG Signal 2')
    plt.title('Original EMG Signal with Noise')
    plt.subplot(2, 1, 2)
    plt.plot(t[-len(filtered_signal1):], filtered_signal1, label='Filtered Signal 1')
    plt.plot(t[-len(filtered_signal2):], filtered_signal2, label='Filtered Signal 2')
    plt.title('Combined FIR Filtered Signal')
    plt.xlabel('Time [s]')
    plt.tight_layout()
    plt.legend()
    plt.show()
