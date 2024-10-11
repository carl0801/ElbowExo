import shimmer
import util
import numpy as np
import keyboard

TYPE = util.SHIMMER_ExG_0
PORT = "COM4"
run = True
moving_state = 0

# Number of samples to collect before stopping the data collection (1 = 1000 measurements)
sampletime = 25

# Initialize Shimmer
shimmer_device = shimmer.Shimmer3(TYPE, debug=False)
shimmer_device.connect(com_port=PORT, write_rtc=True, update_all_properties=True, reset_sensors=True)
shimmer_device.set_sampling_rate(650)
shimmer_device.set_enabled_sensors(util.SENSOR_ExG1_16BIT, util.SENSOR_ExG2_16BIT, util.SENSOR_BATTERY)
shimmer_device.exg_send_emg_settings(util.ExG_GAIN_12)
#shimmer_device.print_object_properties()
#print(shimmer_device.get_available_sensors())

shimmer_device.start_bt_streaming()

# Initial buffer size (can be adjusted)
INITIAL_CAPACITY = 1000

# Pre-allocate numpy array to store the data
data = np.empty((INITIAL_CAPACITY, 5))  # Assuming 3 columns (timestamp, sensor1, sensor2)
current_index = 0

# Dynamically resize function for the numpy array
def resize_array(arr, new_size):
    new_arr = np.empty((new_size, arr.shape[1]))
    new_arr[:arr.shape[0], :] = arr
    return new_arr



def battry_calibrate(data):
    calibrated = (data * (1/4095) * (3/1)) * 2
    # Find procentage of battery left with 0 = 3.2V and 100 = 4.167V
    calibrated = ((calibrated - 3.2) / (4.167 - 3.2)) * 100
    return calibrated

while run:
    n_of_packets, packets = shimmer_device.read_data_packet_extended(calibrated=False)
    if n_of_packets > 0:
        for packet in packets:
            # Ensure the numpy array has enough space, dynamically resize if necessary
            if current_index >= data.shape[0]:
                data = resize_array(data, data.shape[0] * 2)

            # Calculate the time stamp between RTCcurrent and RTCstart
            timestamp = packet[2] - packet[1]
            #print(packet)
            sensor1 = packet[5]
            sensor2 = packet[6]
            battery = battry_calibrate(packet[3])

            if keyboard.is_pressed('w'):
                active_movement_up = 1
                print(f"Sensor1: {sensor1}, Sensor2: {sensor2}, Battery: {battery:.2f}% \n")

            else:
                active_movement_up = 0
            
            if keyboard.is_pressed('s'):
                active_movement_down = 1
                print(f"Sensor1: {sensor1}, Sensor2: {sensor2}, Battery: {battery:.2f}% \n")

            else:
                active_movement_down = 0
            
            # Print the time left to the console
            print(f"\rTime left: {sampletime - timestamp}", end='', flush=True)

            # Store the data (timestamp, sensor1, sensor2)
            data[current_index, :] = [timestamp, sensor1, sensor2, active_movement_up, active_movement_down]
            current_index += 1

            if timestamp >= sampletime:
                run = False
           
                

print("\nData collection complete")
shimmer_device.stop_bt_streaming()
shimmer_device.disconnect(reset_obj_to_init=True)

# Save only the filled portion of the numpy array to a .npz file
np.savez('Htest.npz', data=data[:current_index])
print("Data saved")