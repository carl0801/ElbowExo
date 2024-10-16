import socket
import shimmer
import util
import numpy as np
import threading
import filter
import myMain
import time
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
import keyboard

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

# Initialize lists to store received data as NumPy arrays
sensor1_data = np.array([])
sensor2_data = np.array([])

last_movement = 'rest'
def classify(sensor1, sensor2):
    global keyhandle, last_movement
    threshold = 6
    # rolling variance
    window_size = 100
    variance1 = np.var(sensor1[-window_size:])
    variance2 = np.var(sensor2[-window_size:])
    diff = variance1 - variance2
    if diff > threshold:
        if last_movement != 'up':
            myMain.velocity_control(keyhandle, 1000)
            #time.sleep(0.5)
            print('Moving up')
        last_movement = 'up'
        return 'up'
    elif diff < -threshold+5:
        if last_movement != 'down':
            myMain.velocity_control(keyhandle, -1000)
            #time.sleep(0.5)
            print('Moving down')
        last_movement = 'down'
        return 'down'
    else:
        if last_movement != 'rest':
            myMain.velocity_control(keyhandle, 0)
            #time.sleep(0.5)
            print('Resting')
        last_movement = 'rest'
        return 'rest'
    
def filtering(sensor1_data, sensor2_data):
    global Filter
    sensor1_data_filtered = filter.array_run(sensor1_data, Filter)
    sensor2_data_filtered = filter.array_run(sensor2_data, Filter)
    return sensor1_data_filtered, sensor2_data_filtered

def data_collection():
    global sensor1_data, sensor2_data
    try:
        while True:
            n_of_packets, packets = shimmer.read_data_packet_extended()
            if n_of_packets > 0:
                for packet in packets:
                    sensor1 = packet[3]
                    sensor2 = packet[4]

                    # Append data to NumPy arrays
                    sensor1_data = np.append(sensor1_data, sensor1)
                    sensor2_data = np.append(sensor2_data, sensor2)

                    if len(sensor1_data) > 1000:
                        sensor1_data = sensor1_data[-1000:]
                        sensor2_data = sensor2_data[-1000:]
    except KeyboardInterrupt:
        shimmer.stop_bt_streaming()
        shimmer.disconnect(reset_obj_to_init=True)
        myMain.stop_motor(keyhandle)

# Run the data collection in a separate thread
data_thread = threading.Thread(target=data_collection)
data_thread.daemon = True
data_thread.start()

# filter the data and classify the movement
def update():
    global sensor1_data, sensor2_data
    sensor1_data_filtered, sensor2_data_filtered = filtering(sensor1_data, sensor2_data)
    classify(sensor1_data_filtered, sensor2_data_filtered)

# set up update loop
while True:
    if len(sensor1_data) > 100:
        update()
        time.sleep(0.02)  # Update every 20 ms for more frequent processing
    if keyboard.is_pressed('q'):
        myMain.stop_motor(keyhandle)
        shimmer.stop_bt_streaming()
        shimmer.disconnect(reset_obj_to_init=True)
        #stop other threads
        data_thread.join()
        time.sleep(1)
        break
    
