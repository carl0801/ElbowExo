import socket
import shimmer
import util
import numpy as np
import threading
import filter
import myMain
import time
# import a fil

TYPE = util.SHIMMER_ExG_0
PORT = "COM5"

# Initialize Shimmer
shimmer = shimmer.Shimmer3(TYPE, debug=True)
shimmer.connect(com_port=PORT, write_rtc=True, update_all_properties=True, reset_sensors=True)
shimmer.set_sampling_rate(650)
shimmer.set_enabled_sensors(util.SENSOR_ExG1_16BIT, util.SENSOR_ExG2_16BIT)

shimmer.start_bt_streaming()

keyhandle = myMain.init()

Filter = filter.generate_filter(fs=650)

# Preallocate fixed-size buffer with 1000 samples
buffer_size = 1000
sensor1_data = np.zeros(buffer_size)
sensor2_data = np.zeros(buffer_size)

# Circular buffer indices
sensor_idx = 0

last_movement = 'rest'

# Preallocate filtered data arrays
sensor1_data_filtered = np.zeros(buffer_size)
sensor2_data_filtered = np.zeros(buffer_size)

# Lock to handle threading
data_lock = threading.Lock()

def classify(sensor1, sensor2):
    global keyhandle, last_movement
    threshold = 6
    window_size = 100
    # Calculate variance over the window size
    variance1 = np.var(sensor1[-window_size:])
    variance2 = np.var(sensor2[-window_size:])
    diff = variance1 - variance2

    if diff > threshold:
        if last_movement != 'up':
            myMain.velocity_control(keyhandle, 1000)
            print('Moving up')
        last_movement = 'up'
        return 'up'
    elif diff < -threshold + 5:
        if last_movement != 'down':
            myMain.velocity_control(keyhandle, -1000)
            print('Moving down')
        last_movement = 'down'
        return 'down'
    else:
        if last_movement != 'rest':
            myMain.velocity_control(keyhandle, 0)
            print('Resting')
        last_movement = 'rest'
        return 'rest'

def update():
    global sensor1_data_filtered, sensor2_data_filtered, Filter
    with data_lock:
        sensor1_data_filtered[:] = filter.array_run2(sensor1_data, Filter)
        sensor2_data_filtered[:] = filter.array_run2(sensor2_data, Filter)
    classify(sensor1_data_filtered, sensor2_data_filtered)

def data_collection():
    global sensor1_data, sensor2_data, sensor_idx
    try:
        while True:
            n_of_packets, packets = shimmer.read_data_packet_extended()
            if n_of_packets > 0:
                with data_lock:
                    for packet in packets:
                        sensor1 = packet[3]
                        sensor2 = packet[4]
                        
                        # Insert data into circular buffer
                        sensor1_data[sensor_idx % buffer_size] = sensor1
                        sensor2_data[sensor_idx % buffer_size] = sensor2
                        sensor_idx += 1
    except KeyboardInterrupt:
        shimmer.stop_bt_streaming()
        shimmer.disconnect(reset_obj_to_init=True)
        myMain.stop_motor(keyhandle)

def timer_update():
    while True:
        update()
        time.sleep(0.02)  # Update every 20 ms for more frequent processing

# Run the data collection in a separate thread
data_thread = threading.Thread(target=data_collection)
data_thread.daemon = True
data_thread.start()

# Timer thread for updating and classification
timer_thread = threading.Thread(target=timer_update)
timer_thread.daemon = True
timer_thread.start()

if __name__ == '__main__':
    while True:
        time.sleep(1)
