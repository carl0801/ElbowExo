import socket
import shimmer
import util
import numpy as np
import threading
import filter
#import myMain
import time
import serial 
from pywifi import PyWiFi, const, Profile

# Automatically connect PC to the ESP32 Wi-Fi
def connect_to_wifi(ssid, password):
    wifi = PyWiFi()
    iface = wifi.interfaces()[0]  # Get the first wireless interface

    iface.disconnect()
    time.sleep(1)  # Wait for a second to ensure disconnection

    profile = Profile()
    profile.ssid = ssid
    profile.auth = const.AUTH_ALG_OPEN
    profile.akm.append(const.AKM_TYPE_WPA2PSK)
    profile.cipher = const.CIPHER_TYPE_CCMP
    profile.key = password

    # Check if the profile already exists
    existing_profiles = iface.network_profiles()
    for existing_profile in existing_profiles:
        if existing_profile.ssid == ssid:
            iface.remove_network_profile(existing_profile)
            break

    tmp_profile = iface.add_network_profile(profile)  # Add the new profile

    iface.connect(tmp_profile)  # Connect to the network
    time.sleep(10)  # Wait for 10 seconds to ensure connection

    if iface.status() == const.IFACE_CONNECTED:
        print(f'Connected to {ssid}')
        return True
    else:
        print(f'Could not connect to {ssid}')
        return False

# Connect to the ESP32 Wi-Fi
ssid = 'ESP32_Hotspot'
password = '12345678'
if not connect_to_wifi(ssid, password):
    raise Exception('Failed to connect to Wi-Fi')

TYPE = util.SHIMMER_ExG_0
PORT = "COM7"

sensor_idx = 1

# Initialize Shimmer
shimmer = shimmer.Shimmer3(TYPE, debug=True)
shimmer.connect(com_port=PORT, write_rtc=True, update_all_properties=True, reset_sensors=True)
shimmer.set_sampling_rate(650)
shimmer.set_enabled_sensors(util.SENSOR_ExG1_16BIT, util.SENSOR_ExG2_16BIT)
shimmer.start_bt_streaming()

Filter = filter.generate_filter(fs=650)

# Preallocate fixed-size buffer with 1000 samples
buffer_size = 1000
sensor1_data = np.zeros(buffer_size)
sensor2_data = np.zeros(buffer_size)

# Preallocate filtered data arrays
sensor1_data_filtered = np.zeros(buffer_size)
sensor2_data_filtered = np.zeros(buffer_size)

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
    
def update():
    global sensor1_data_filtered, sensor2_data_filtered, Filter
    with data_lock:
        sensor_mean = filter.run(sensor1_data, sensor2_data, Filter, single_window=200)
        if abs(sensor_mean) > 1:
            limited_speed = 100*sensor_mean
            # restrict speed to 2500 rpm
            if limited_speed > 2000:
                limited_speed = 2000
            elif limited_speed < -2000:
                limited_speed = -2000
            sendvelocity(limited_speed)
            print(limited_speed)
        else:
            sendvelocity(0)

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

def timer_update():
    while True:
        update()
        time.sleep(0.1)  # Update every 20 ms for more frequent processing

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
