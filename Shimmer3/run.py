import numpy as np
import time
import threading
import myMain
import filter
import matplotlib.pyplot as plt
import socket

# Load the data from the .npz file
data = np.load('RawMeasurements\BevægelseVertikaltFlexEx.npz')['data']

# Extract the timestamps and the sensor data
timestamps = data[:, 0]
sensor1_data = data[:, 1]
sensor2_data = data[:, 2]
up = data[:, 3]
down = data[:, 4]

#keyhandle = myMain.init()
#if keyhandle is not None:
  ##  print('Connected to EPOS4')
Filter = filter.generate_filter(fs=650)

time.sleep(4)
start_time = time.time()

# Preallocate fixed-size buffer with 1000 samples
buffer_size = 1000
sensor1_buffer = np.zeros(buffer_size)
sensor2_buffer = np.zeros(buffer_size)

# Circular buffer indices
sensor_idx = 0

last_movement = 'rest'

# Preallocate filtered data arrays
sensor1_data_filtered = np.zeros(buffer_size)
sensor2_data_filtered = np.zeros(buffer_size)

# Lock to handle threading
data_lock = threading.Lock()

# Variable to store the current velocity
current_velocity = 0

HOST = '192.168.4.22'  # Updated to match the ESP32 IP, if set to `local_ip`
PORT = 80   

# Socket initialization - Keep this socket open for use by all threads
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

#define a function that sends the velocity to the motor over serial
def sendvelocity(velocity):
    velocity = str(velocity) + '\n'
    sock.sendall(velocity.encode('utf-8'))
    
    

def update():
    global sensor1_data_filtered, sensor2_data_filtered, Filter, current_velocity
    #print("updating.")
    with data_lock:
        sensor_mean = filter.run(sensor1_data, sensor2_data, Filter, single_window=300)
        if abs(sensor_mean) > 1:
            limited_speed = 100*sensor_mean
            # restrict speed to 2500 rpm
            if limited_speed > 2000:
                limited_speed = 2000
            elif limited_speed < -2000:
                limited_speed = -2000
            current_velocity = limited_speed
            sendvelocity(limited_speed)
            #print(limited_speed)
            #myMain.velocity_control(keyhandle, int(limited_speed))
        else:
            sendvelocity(0)

            #myMain.velocity_control(keyhandle, 0)

def data_collection():
    global sensor1_data, sensor2_data, sensor_idx, current_velocity
    try:
        for i in range(len(timestamps)):
            # Remove unnecessary delay
            # time_delay = (timestamps[i] - timestamps[i - 1]) / 650 if i > 0 else 0
            # time.sleep(time_delay)
            
            with data_lock:
                sensor1_buffer[sensor_idx % buffer_size] = sensor1_data[i]
                sensor2_buffer[sensor_idx % buffer_size] = sensor2_data[i]
                sensor_idx += 1
            
            if i >= 100:
                update()
                # Print timestamp and speed
                print(f"Timestamp: {timestamps[i]}, Speed: {current_velocity}")
    except KeyboardInterrupt:
        #myMain.stop_motor(keyhandle)
        print('Motor stopped')



# Run the data collection in a separate thread
data_thread = threading.Thread(target=data_collection)
data_thread.daemon = True
data_thread.start()


if __name__ == '__main__':
    while True:
        time.sleep(1)