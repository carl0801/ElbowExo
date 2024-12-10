import pickle
import glob
import os
import numpy as np
import time

def load(n=0):
    # Find files with the highest number
    files = glob.glob('data/[0-9.]*-shimmer.pkl') + glob.glob('data/[0-9.]*-loadcell.pkl')
    files.sort(key=lambda x: list(map(float, os.path.splitext(os.path.basename(x))[0].split('-')[0].split('.'))), reverse=True)
    # The nth latest reading
    data1 = pickle.load(open(files[n*2], 'rb'))
    data2 = pickle.load(open(files[n*2+1], 'rb'))
    if len(data1[0]) > len(data2[0]):
        shimmerData = data1
        loadcellData = data2
    else:
        shimmerData = data2
        loadcellData = data1
    shimmerData = np.array(shimmerData)
    loadcellData = np.array(loadcellData, dtype=float)

    # Shimmer data is stored in an array where each entry contain (time, sensor1, sensor2)
    # Loadcell data is stored in an array where each entry contain (time, sensor)
    # Shimmer time is in seconds, and loadcell is in miliseconds, but the clock they oprate after is not the same
    # They start at different times, but the readings end at the same time, so that is how they should be calibrate

    loadcellData[:, 0] = loadcellData[:, 0] / 1000

    # Get the time of the last data point
    last_time_shimmer = shimmerData[-1][0]
    last_time_loadcell = loadcellData[-1][0]

    # The time difference is the difference between the last time of the two systems
    time_diff = last_time_loadcell - last_time_shimmer

    # Calibrate the time of the loadcell
    loadcellData[:, 0] = loadcellData[:, 0] - time_diff

    # Make sure shimmer data is a signed int and there is no overflow
    shimmerData[:, 1] = np.int16(shimmerData[:, 1])
    shimmerData[:, 2] = np.int16(shimmerData[:, 2])

    return shimmerData, loadcellData

def loadShimmer(n=0):
    # Find files with the highest number
    files = glob.glob('data/[0-9.]*-shimmer.pkl')
    files.sort(key=lambda x: list(map(float, os.path.splitext(os.path.basename(x))[0].split('-')[0].split('.'))), reverse=True)
    # The nth latest reading
    shimmerData = pickle.load(open(files[n], 'rb'))
    shimmerData = np.array(shimmerData)

    # Make sure shimmer data is a signed int and there is no overflow
    shimmerData[:, 1] = np.int16(shimmerData[:, 1])
    shimmerData[:, 2] = np.int16(shimmerData[:, 2])

    return shimmerData

class Shimmer3:
    def __init__(self, TYPE, debug=False):
        self.n = 0
        self.data = loadShimmer(self.n)
        self.idx = 0
        self.last_time = time.time()
        self.sampling_rate = 650
    def connect(self, com_port, write_rtc=True, update_all_properties=True, reset_sensors=True):
        pass
    def set_sampling_rate(self, sampling_rate):
        self.sampling_rate = sampling_rate
    def set_enabled_sensors(self, *args):
        pass
    def start_bt_streaming(self):
        pass
    def stop_bt_streaming(self):
        pass
    def disconnect(self, reset_obj_to_init=True):
        pass
    def read_data_packet_extended(self):
        # Define how many packets to read in one call (simulating the real sensor behavior)
        time_since_last_read = time.time() - self.last_time
        packets_per_read = int(time_since_last_read * self.sampling_rate)
        if packets_per_read != 0:
            self.last_time = time.time()
        else: 
            return 0, []        
        # Check if there’s enough data remaining
        if self.idx >= len(self.data):
            self.n += 1
            self.data = loadShimmer(self.n)
            self.idx = 0
            return 0, []  # No more data to read
        # Get a slice of the data starting from self.idx
        end_idx = min(self.idx + packets_per_read, len(self.data))
        packets = self.data[self.idx:end_idx]
        # Update self.idx to reflect the new reading position
        self.idx = end_idx
        # Format packets to have the same structure as the real sensor output
        formatted_packets = [
            [packet[0], 0, 0, packet[1], packet[2]]  # Adjust structure as needed to match real sensor output
            for packet in packets
        ]
        # Return the number of packets and the packets themselves
        return len(formatted_packets), formatted_packets


AF_INET = 0
SOCK_STREAM = 0
class socket:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connected = False

    def connect(self, address):
        print(f"Connecting to {address}... (Dummy Connection)")
        self.connected = True

    def sendall(self, data):
        if self.connected:
            # Decode and print the data to simulate sending it
            print(f"Sending velocity: {round(float(data.decode('utf-8').strip()), 2)}")
        else:
            print("Not connected. Cannot send data.")

    def close(self):
        if self.connected:
            print("Closing the dummy connection.")
            self.connected = False
        else:
            print("Connection is already closed.")