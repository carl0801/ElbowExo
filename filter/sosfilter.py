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

def filter_emg_data(data, coeff=generate_filter(), threshold=10.0, window_size=200):
    # Step 1: Bandpass filter between 20 Hz and 250 Hz
    filtered_data = sosfiltfilt(coeff[0], data)
    # Step 2: Notch filter around 50 Hz
    filtered_data = sosfiltfilt(coeff[1], filtered_data)
    return filtered_data

def combine_sensors(sensor1, sensor2, multiplier=2.5):
    return sensor1 - multiplier * sensor2

def run(sensor1, sensor2, filter=generate_filter()):
    filtered_sensor1 = filter_emg_data(sensor1, filter)
    filtered_sensor2 = filter_emg_data(sensor2, filter)
    return filtered_sensor1, filtered_sensor2
    

if __name__ == '__main__':
    import time
    import loadData
    import matplotlib.pyplot as plt
    from matplotlib.widgets import SpanSelector

    # Load the data from the .npz file
    data, _ = loadData.load(n=5)

    # Extract the timestamps and the GSR data
    timestamps = data[:, 0]
    t = timestamps
    sensor1_data = data[:, 1]
    sensor2_data = data[:, 2]
    fs = 650

    # Function to compute FFT and plot the histogram
    def fft_data(signal_data, fs):
        # Perform FFT
        N = len(signal_data)
        fft_result = np.fft.fft(signal_data)
        fft_magnitude = np.abs(fft_result[:N // 2])  # Magnitude of FFT (first half)
        
        # Create frequency bins
        freqs = np.fft.fftfreq(N, 1 / fs)[:N // 2]  # Frequencies corresponding to FFT
        
        return freqs, fft_magnitude
    
    def plot_fft_histogram(sensor1_data, sensor2_data, fs, ax):
        # Clear the current axis to update the plot
        ax.cla()
        
        freqs1, fft_magnitude1 = fft_data(sensor1_data, fs)
        freqs2, fft_magnitude2 = fft_data(sensor2_data, fs)
        
        # Plot histogram of frequencies
        ax.hist(freqs1, weights=fft_magnitude1, bins=200, edgecolor='k', alpha=0.7, label='Sensor 1')
        ax.hist(freqs2, weights=fft_magnitude2, bins=200, edgecolor='k', alpha=0.7, label='Sensor 2')
        
        ax.set_title('Frequency Distribution')
        ax.set_xlabel('Frequency (Hz)')
        ax.set_yscale('log')
        ax.set_ylabel('Magnitude')
        ax.grid(True)
        ax.legend()
        
        # Redraw the updated figure
        plt.draw()

    def plot_signals(sensor1_data, sensor2_data, fs):
        signal1, signal2 = run(sensor1_data, sensor2_data)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 10))
        
        # Plot the signals in the top axis (ax1)
        ax1.plot(t, signal1, label='Sensor 1')
        ax1.plot(t, signal2, label='Sensor 2')
        ax1.set_title('Sensor Data')
        ax1.legend()
        
        # Initialize interactive mode
        #plt.ion()
        
        def onselect(xmin, xmax):
            start_index = int(xmin * fs)
            end_index = int(xmax * fs)
            print(f"Selected index range: {start_index} to {end_index}")
            
            # Update the FFT histogram in the bottom axis (ax2)
            print(len(sensor1_data[start_index:end_index]))
            print(len(sensor2_data[start_index:end_index]))
            print(len(sensor1_data))
            print(len(sensor2_data))
            plot_fft_histogram(signal1[start_index:end_index], signal2[start_index:end_index], fs, ax2)

        # Add the SpanSelector for selecting a range on the top axis
        span = SpanSelector(ax1, onselect, 'horizontal', useblit=True, interactive=True)
        
        plt.show()

    # Example usage (assuming you have sensor1_data, sensor2_data, and fs):
    plot_signals(sensor1_data, sensor2_data, fs)