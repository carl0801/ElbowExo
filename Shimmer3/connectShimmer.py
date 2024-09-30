import shimmer
import util
import numpy as np

TYPE = util.SHIMMER_ExG_0
PORT = "COM5"

# Initialize Shimmer
shimmer = shimmer.Shimmer3(TYPE, debug=True)
shimmer.connect(com_port=PORT, write_rtc=True, update_all_properties=True, reset_sensors=True)
shimmer.set_sampling_rate(512)
shimmer.set_enabled_sensors(util.SENSOR_ExG1_16BIT, util.SENSOR_ExG2_16BIT)
shimmer.print_object_properties()
print(shimmer.get_available_sensors())

shimmer.start_bt_streaming()

# Initial buffer size (can be adjusted)
INITIAL_CAPACITY = 1000

# Pre-allocate numpy array to store the data
data = np.empty((INITIAL_CAPACITY, 3))  # Assuming 6 columns (timestamp, RTCstart, RTCcurrent, sensor1, sensor2, time_diff)
current_index = 0

# Dynamically resize function for the numpy array
def resize_array(arr, new_size):
    return np.resize(arr, (new_size, arr.shape[1]))

try:
    while True:
        n_of_packets, packets = shimmer.read_data_packet_extended() #calibrated=False)
        if n_of_packets > 0:
            for packet in packets:
                # Ensure the numpy array has enough space, dynamically resize if necessary
                if current_index >= data.shape[0]:
                    data = resize_array(data, data.shape[0] + 2000)

                # Calculate the time stamp between RTCcurrent and RTCstart
                timestamp = packet[2] - packet[1]
                sensor1 = packet[3]
                sensor2 = packet[4]

                # Store the data (timestamp, RTCstart, RTCcurrent, sensor1, sensor2, time_diff)
                data[current_index, :] = [timestamp, sensor1, sensor2]
                current_index += 1

                if current_index % 1000 == 0:
                    print(packet)
                    print(f"Timestamp: {timestamp}, Sensor1: {sensor1}, Sensor2: {sensor2}")
                elif current_index == 2001:
                    #interrupt the loop
                    raise KeyboardInterrupt

except KeyboardInterrupt:
    print("KeyboardInterrupt")
    shimmer.stop_bt_streaming()
    shimmer.disconnect(reset_obj_to_init=True)

    # Save only the filled portion of the numpy array to a .npz file
    np.savez('shimmer_data6.npz', data=data[:current_index])
