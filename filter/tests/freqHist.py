import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk

# Simulated example data (replace this with your actual data)
fs = 650  # Sampling frequency
t = np.linspace(0, 10, fs * 10)  # 10 seconds of data
sensor1_data = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 50 * t)
sensor2_data = np.cos(2 * np.pi * 10 * t) + 0.3 * np.sin(2 * np.pi * 80 * t)

# Function to compute FFT and plot the histogram
def plot_fft_histogram(signal_data, fs, title, ax):
    ax.clear()
    N = len(signal_data)
    fft_result = np.fft.fft(signal_data)
    fft_magnitude = np.abs(fft_result[:N // 2])  # Magnitude of FFT (first half)
    freqs = np.fft.fftfreq(N, 1 / fs)[:N // 2]  # Frequencies corresponding to FFT
    
    # Plot histogram of frequencies
    ax.hist(freqs, weights=fft_magnitude, bins=50, edgecolor='k', alpha=0.7)
    ax.set_title(f'Frequency Distribution - {title}')
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Magnitude')
    ax.grid(True)

# Function to plot the time-domain signal
def plot_signal(ax):
    ax.clear()
    ax.plot(t, sensor1_data, label="Sensor 1")
    ax.plot(t, sensor2_data, label="Sensor 2", alpha=0.7)
    ax.set_title('Sensor Signals')
    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('Amplitude')
    ax.legend()
    ax.grid(True)

# Update the frequency histogram based on the selected range
def update_histogram():
    start_time = float(start_entry.get())
    end_time = float(end_entry.get())
    
    # Convert time to index
    start_index = int(start_time * fs)
    end_index = int(end_time * fs)
    
    # Ensure the indices are valid
    if start_index < 0 or end_index > len(sensor1_data) or start_index >= end_index:
        print("Invalid range. Please check your start and end times.")
        return
    
    # Update the histogram
    plot_fft_histogram(sensor1_data[start_index:end_index], fs, f'Sensor 1 ({start_time}-{end_time}s)', hist_ax)
    canvas_hist.draw()

# Create the GUI window
root = tk.Tk()
root.title("Signal Analysis GUI")

# Create the plot areas
fig, (signal_ax, hist_ax) = plt.subplots(2, 1, figsize=(6, 6))

# Embed the signal plot
canvas_signal = FigureCanvasTkAgg(fig, master=root)
canvas_signal.get_tk_widget().grid(row=0, column=0, columnspan=2)

# Initial plot of the signals
plot_signal(signal_ax)

# Embed the histogram plot
canvas_hist = FigureCanvasTkAgg(fig, master=root)
canvas_hist.get_tk_widget().grid(row=1, column=0, columnspan=2)

# Create start and end time input fields
tk.Label(root, text="Start Time (s):").grid(row=2, column=0)
start_entry = tk.Entry(root)
start_entry.grid(row=2, column=1)

tk.Label(root, text="End Time (s):").grid(row=3, column=0)
end_entry = tk.Entry(root)
end_entry.grid(row=3, column=1)

# Create a button to update the histogram
update_button = tk.Button(root, text="Update Histogram", command=update_histogram)
update_button.grid(row=4, column=0, columnspan=2)

# Run the GUI event loop
root.mainloop()
