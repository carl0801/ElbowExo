import shimmer
import util
import numpy as np

TYPE = util.SHIMMER_GSRplus
PORT = "COM5"

# Initialize Shimmer
shimmer = shimmer.Shimmer3(TYPE, debug=True)
shimmer.connect(com_port=PORT, write_rtc=True, update_all_properties=True, reset_sensors=True)
shimmer.set_sampling_rate(512.0)
shimmer.set_enabled_sensors(util.SENSOR_LOW_NOISE_ACCELEROMETER)
shimmer.print_object_properties()

shimmer.start_bt_streaming()

# Initial buffer size (can be adjusted)
INITIAL_CAPACITY = 1000

# Pre-allocate numpy array to store the data
data = np.empty((INITIAL_CAPACITY, 6))  # Assuming 6 columns (timestamp, RTCstart, RTCcurrent, sensor1, sensor2, time_diff)
current_index = 0

# Dynamically resize function for the numpy array
def resize_array(arr, new_size):
    return np.resize(arr, (new_size, arr.shape[1]))

try:
    while True:
        n_of_packets, packets = shimmer.read_data_packet_extended(calibrated=False)
        if n_of_packets > 0:
            for packet in packets:
                # Calculate the time difference between RTCcurrent and RTCstart
                time_diff = packet[2] - packet[1]

                # Ensure the numpy array has enough space, dynamically resize if necessary
                if current_index >= data.shape[0]:
                    data = resize_array(data, data.shape[0] * 2)  # Double the size when more space is needed

                # Store the data (timestamp, RTCstart, RTCcurrent, sensor1, sensor2, time_diff)
                data[current_index, :] = [packet[0], packet[1], packet[2], packet[3], packet[4], time_diff]
                current_index += 1

except KeyboardInterrupt:
    shimmer.stop_bt_streaming()
    shimmer.disconnect(reset_obj_to_init=True)

    # Save only the filled portion of the numpy array to a .npz file
    np.savez('shimmer_data.npz', data=data[:current_index])
