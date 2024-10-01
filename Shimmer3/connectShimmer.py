import shimmer
import util
import numpy as np

TYPE = util.SHIMMER_ExG_0
PORT = "COM4"
run = True

# Number of samples to collect before stopping the data collection (1 = 1000 measurements)
samples = 15

# Initialize Shimmer
shimmer_device = shimmer.Shimmer3(TYPE, debug=True)
shimmer_device.connect(com_port=PORT, write_rtc=True, update_all_properties=True, reset_sensors=True)
shimmer_device.set_sampling_rate(512)
shimmer_device.set_enabled_sensors(util.SENSOR_ExG1_16BIT, util.SENSOR_ExG2_16BIT)
shimmer_device.print_object_properties()
print(shimmer_device.get_available_sensors())

shimmer_device.start_bt_streaming()

# Initial buffer size (can be adjusted)
INITIAL_CAPACITY = 1000

# Pre-allocate numpy array to store the data
data = np.empty((INITIAL_CAPACITY, 3))  # Assuming 3 columns (timestamp, sensor1, sensor2)
current_index = 0

# Dynamically resize function for the numpy array
def resize_array(arr, new_size):
    new_arr = np.empty((new_size, arr.shape[1]))
    new_arr[:arr.shape[0], :] = arr
    return new_arr

while run:
    n_of_packets, packets = shimmer_device.read_data_packet_extended()
    if n_of_packets > 0:
        for packet in packets:
            # Ensure the numpy array has enough space, dynamically resize if necessary
            if current_index >= data.shape[0]:
                data = resize_array(data, data.shape[0] * 2)

            # Calculate the time stamp between RTCcurrent and RTCstart
            timestamp = packet[2] - packet[1]
            sensor1 = packet[3]
            sensor2 = packet[4]

            # Store the data (timestamp, sensor1, sensor2)
            data[current_index, :] = [timestamp, sensor1, sensor2]
            current_index += 1

            if current_index % 1000 == 0:
                print(packet)
                print(f"Timestamp: {timestamp}, Sensor1: {sensor1}, Sensor2: {sensor2}")
                samples -= 1
            elif samples == 0:
                run = False
                

print("Data collection complete")
shimmer_device.stop_bt_streaming()
shimmer_device.disconnect(reset_obj_to_init=True)

# Save only the filled portion of the numpy array to a .npz file
np.savez('shimmer_data6.npz', data=data[:current_index])
print("Data saved to shimmer_data7.npz")