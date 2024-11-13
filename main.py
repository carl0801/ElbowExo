import util
import numpy as np
import threading
import time
import serial 
import subprocess
import os

import emg_signal
import loadData as shimmerLib
import loadData as socket


platform = "windows" # linux or windows

# Connect to Shimmer
if platform == "linux":
    def run_command(command):
        try:
            print(f"Running: {command}")
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(result.stdout.decode())
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stderr.decode()}")

    # Function to wait for /dev/rfcomm0 to appear
    def wait_for_rfcomm(port, timeout=15):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if os.path.exists(port):
                print(f"{port} is now available.")
                return True
            time.sleep(0.5)  # Poll every 0.5 seconds
        print(f"Timeout: {port} did not appear within {timeout} seconds.")
        return False

    # Make rfcomm port
    mac_address = '00:06:66:FB:4C:BE'
    rfport_thread = threading.Thread(target=run_command, args=(f'sudo rfcomm connect /dev/rfcomm0 {mac_address}',))
    rfport_thread.start()

    # Wait until /dev/rfcomm0 exists, then change permissions
    if wait_for_rfcomm("/dev/rfcomm0"):
        run_command('sudo chmod 666 /dev/rfcomm0')
    else:
        print("Failed to find /dev/rfcomm0")
        
    PORT = "/dev/rfcomm0"

elif platform == "windows":
    PORT = "COM7"

# Initialize Shimmer
TYPE = util.SHIMMER_ExG_0
shimmer = shimmerLib.Shimmer3(TYPE, debug=True)
shimmer.connect(com_port=PORT, write_rtc=True, update_all_properties=True, reset_sensors=True)
shimmer.set_sampling_rate(650)
shimmer.set_enabled_sensors(util.SENSOR_ExG1_16BIT, util.SENSOR_ExG2_16BIT)
shimmer.start_bt_streaming()

shimmerSignal = emg_signal.Signal()

# Preallocate fixed-size buffer with 1000 samples
buffer_size = 650*8
sensor1_data = np.zeros(buffer_size)
sensor2_data = np.zeros(buffer_size)
sensor_idx = 0
start_time = time.time()

# Lock to handle threading
data_lock = threading.Lock()

HOST = '192.168.4.22'  # Updated to match the ESP32 IP, if set to `local_ip`
PORT = 80   

# Socket initialization - Keep this socket open for use by all threads
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

#define a function that sends the velocity to the motor over serial
def sendvelocity(velocity):
    velocity = str(velocity) + '\n'
    sock.sendall(velocity.encode('utf-8'))

# Function to get the data as a contiguous, ordered array for filtering
def get_sequential_data(buffer, start_index):
    return np.concatenate((buffer[start_index:], buffer[:start_index]))
    
def update():
    with data_lock:
        sensor1_sequential = get_sequential_data(sensor1_data, sensor_idx)
        sensor2_sequential = get_sequential_data(sensor2_data, sensor_idx)
        shimmerSignal.set_signal(sensor1_sequential, sensor2_sequential)
        control_value = shimmerSignal.get_control_value()
        limited_speed = 7000*control_value
        # restrict speed to 2500 rpm
        if limited_speed > 2000:
            limited_speed = 2000
        elif limited_speed < -2000:
            limited_speed = -2000
        sendvelocity(limited_speed)


def data_collection():
    global sensor1_data, sensor2_data, sensor_idx
    try:
        while True:
            n_of_packets, packets = shimmer.read_data_packet_extended()
            if n_of_packets > 0:
                with data_lock:
                    # Extract sensor1 and sensor2 data for all packets at once
                    sensor1_values = np.array([packet[3] for packet in packets])
                    sensor2_values = np.array([packet[4] for packet in packets])
                    num_new = len(sensor1_values)

                    # Insert new data in circular fashion
                    for i in range(num_new):
                        sensor1_data[(sensor_idx + i) % buffer_size] = sensor1_values[i]
                        sensor2_data[(sensor_idx + i) % buffer_size] = sensor2_values[i]

                    # Update index to the next write position in the circular buffer
                    sensor_idx = (sensor_idx + num_new) % buffer_size

    except KeyboardInterrupt:
        shimmer.stop_bt_streaming()
        shimmer.disconnect(reset_obj_to_init=True)

def timer_update():
    update_freq = 10 # Hz
    total_updates = update_freq
    timer_update_start = time.time()
    sleep_time = 1/update_freq
    # Wait 1 second for data to be collected
    time.sleep(1)
    while True:
        update()
        total_updates += 1
        time.sleep(sleep_time)
        current_freq = total_updates / (time.time() - timer_update_start)
        # Update sleep time based on current frequency
        if current_freq > update_freq:
            sleep_time += 0.01
        elif current_freq < update_freq:
            sleep_time -= 0.01
        if sleep_time < 0.01:
            sleep_time = 0.0
        

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
