import socket
import filter
import shimmer
import util
import numpy as np
import threading
import time
import serial 
import subprocess

is_connected = True # Bypass conencting to esp hotspot
platform = "linux" # linux of windows

if is_connected:
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
if not is_connected:
    if not connect_to_wifi(ssid, password):
        raise Exception('Failed to connect to Wi-Fi')

if platform == "linux":
    def run_command(command):
        try:
            print(command)
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(result.stdout.decode())
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stderr.decode()}")
    # Make rfcomm port
    mac_address = '00:06:66:FB:4C:BE'
    rfport_thread = threading.Thread(target=run_command, args=(f'sudo rfcomm connect /dev/rfcomm0 {mac_address}',))
    rfport_thread.start()
    time.sleep(5)
    run_command('sudo chmod 666 /dev/rfcomm0')
    PORT = "/dev/rfcomm0"

elif platform == "windows":
    PORT = "COM7"

TYPE = util.SHIMMER_ExG_0

sensor_idx = 1

# Initialize Shimmer
shimmer = shimmer.Shimmer3(TYPE, debug=True)
shimmer.connect(com_port=PORT, write_rtc=True, update_all_properties=True, reset_sensors=True)
shimmer.set_sampling_rate(650)
shimmer.set_enabled_sensors(util.SENSOR_ExG1_16BIT, util.SENSOR_ExG2_16BIT)
shimmer.start_bt_streaming()

Filter = filter.Filter(window=65, debug=True)

# Preallocate fixed-size buffer with 1000 samples
buffer_size = 650*8
sensor1_data = np.zeros(buffer_size)
sensor2_data = np.zeros(buffer_size)

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
    with data_lock:
        sensor_mean = Filter.run(sensor1_data, sensor2_data)
        limited_speed = 700*sensor_mean
        # restrict speed to 2500 rpm
        if limited_speed > 2000:
            limited_speed = 2000
        elif limited_speed < -2000:
            limited_speed = -2000
        sendvelocity(limited_speed)
        print(limited_speed)
        time.sleep(0.05)

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
