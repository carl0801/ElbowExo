import shimmer
import util
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque

# Constants
TYPE = util.SHIMMER_GSRplus
PORT = "COM5"
MAX_DATA_POINTS = 5120  # Keep the last 10 seconds (assuming 512 Hz sampling rate)

# Initialize shimmer
shimmer = shimmer.Shimmer3(TYPE, debug=True)
shimmer.connect(com_port=PORT, write_rtc=True, update_all_properties=True, reset_sensors=True)
shimmer.set_sampling_rate(512.0)
shimmer.set_enabled_sensors(util.SENSOR_LOW_NOISE_ACCELEROMETER)
shimmer.print_object_properties()

shimmer.start_bt_streaming()

# Data storage (deque is optimized for fast appends and pops)
time_stamps = deque(maxlen=MAX_DATA_POINTS)
sensordata1 = deque(maxlen=MAX_DATA_POINTS)
sensordata2 = deque(maxlen=MAX_DATA_POINTS)

# Initialize plot
plt.ion()  # Enable interactive mode for dynamic plotting
fig, ax = plt.subplots()
line1, = ax.plot([], [], label="Sensor 1 Data", color="blue")
line2, = ax.plot([], [], label="Sensor 2 Data", color="red")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Sensor Data")
ax.legend()

# Initial x and y limits
ax.set_xlim(0, 10)  # Show the last 10 seconds of data
ax.set_ylim(-1, 1)  # Placeholder for y-axis, will be updated based on actual data

# Update function for the plot
def update_plot(frame):
    if time_stamps and sensordata1 and sensordata2:
        # Adjust the x-axis to show the last 10 seconds of data
        ax.set_xlim(max(0, time_stamps[-1] - 10), time_stamps[-1] + 1)
        # Adjust y-axis based on the data range
        ax.set_ylim(min(min(sensordata1), min(sensordata2)) - 0.1, max(max(sensordata1), max(sensordata2)) + 0.1)
        
        # Set the data for both lines to show the recent dataset
        line1.set_data(time_stamps, sensordata1)
        line2.set_data(time_stamps, sensordata2)
        
    return line1, line2

# Start live plot animation, lower interval (refresh every 100 ms)
ani = FuncAnimation(fig, update_plot, interval=100, blit=False)

# Stream data from Shimmer sensor
try:
    while True:
        n_of_packets, packets = shimmer.read_data_packet_extended(calibrated=True)
        if n_of_packets > 0:
            for packet in packets:
                # Calculate the time difference between timeRTCcurrent and timeRTCstart
                time_diff = packet[2] - packet[1]
                time_stamps.append(time_diff)

                # Extract sensor1 and sensor2 data from the packet
                sensordata1.append(packet[3])  # Assuming sensor1 is at index 3
                sensordata2.append(packet[4])  # Assuming sensor2 is at index 4

                # Update the plot at a slower rate to avoid crashes
                plt.pause(0.01)  # Increase the pause slightly to reduce load

except KeyboardInterrupt:
    # Stop streaming and disconnect
    shimmer.stop_bt_streaming()
    shimmer.disconnect(reset_obj_to_init=True)

    # Optionally save the last MAX_DATA_POINTS data to a file
    data_to_save = {
        "timestamps": list(time_stamps),
        "sensor1": list(sensordata1),
        "sensor2": list(sensordata2),
    }
    np.savez('shimmer_data.npz', **data_to_save)

# Close the plot after exiting
plt.ioff()
plt.show()
