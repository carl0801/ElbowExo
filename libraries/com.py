import libraries.shimmer as shimmer
import libraries.util as util
import libraries.emg_signal as filter
import serial
import threading
import numpy as np
import time
import serial.tools.list_ports
import subprocess
import platform
import struct

def open_windows_bluetooth_settings():
        if platform.system() == "Windows":
            subprocess.run(["start", "ms-settings:bluetooth"], shell=True)
        else:
            print("This feature is only supported on Windows.")


class ReadLine:
    def __init__(self, s):
        self.buf = bytearray()
        self.s = s
        self.buf = bytearray()
        self.s = s
        self.start_byte = 0xff
        self.end_byte = 0x0a
        self.ack_byte = 0x06
        self.chk_byte = 0x0202
        self.ack_pack = struct.pack('<BBHB', self.start_byte, self.ack_byte, self.chk_byte, self.end_byte)
        self.data_request_pack = struct.pack('<BBHB', self.start_byte, 0x02, self.chk_byte, self.end_byte)
        self.pos_offset = 5000
        self.ack = False
        self.checksum = 0
        
    def readline(self):
        while True:
            # Check for patterns in the buffer
            data_start = self.buf.find(b"\xff\xff")
            ack_start = self.buf.find(b"\xff\x06")
            newline_pos = self.buf.find(b"\n")

            # Handle data packet
            if data_start != -1 and len(self.buf) >= data_start + 10:
                if self.buf[data_start + 9:data_start + 10] == b"\n":
                    # Valid data packet
                    packet = self.buf[data_start:data_start + 10]
                    del self.buf[:data_start + 10]  # Remove processed packet
                    packet = self._process_packet(packet, 0)
                    if packet is not None:
                        return packet
                    else:
                        return None

            # Handle ACK packet
            if ack_start != -1 and len(self.buf) >= ack_start + 5:
                if self.buf[ack_start + 4:ack_start + 5] == b"\n":
                    # Valid ACK packet
                    packet = self.buf[ack_start:ack_start + 5]
                    del self.buf[:ack_start + 5]  # Remove processed packet
                    packet = self._process_packet(packet, 1)
                    if packet is not None:
                        return "ACK"
                    else:
                        return None

            # Handle string (if no potential packet found or enough bytes aren't present)
            if newline_pos != -1:
                if (data_start == -1 or newline_pos < data_start) and \
                   (ack_start == -1 or newline_pos < ack_start):
                    # Valid string (not part of a data or ACK packet)
                    string = self.buf[:newline_pos + 1].decode("utf-8")
                    del self.buf[:newline_pos + 1]  # Remove processed string
                    return string

            # If no newline or full packet is found, read more data
            self._read_more()

    def _read_more(self):
        """Read more data from the serial port."""
        i = max(1, min(200, self.s.in_waiting))
        data = self.s.read(i)
        self.buf.extend(data)
        
    def _verify_checksum(self, packet):
        """Helper method to verify 2-byte checksum of packet."""
        value1 = packet[3]
        value2, value3 = struct.unpack('<hh', packet[4:8])
        
        checksum = value1
        checksum ^= (value2 & 0xFF)       # XOR lower byte of value2
        checksum ^= ((value2 >> 8) & 0xFF) # XOR upper byte of value2
        checksum ^= (value3 & 0xFF)       # XOR lower byte of value3
        checksum ^= ((value3 >> 8) & 0xFF) # XOR upper byte of value3
        
        if checksum == struct.unpack('<H', packet[8:10]):
            return True
        return False
    
    def _process_packet(self, packet, t):
        """Helper method to process a packet based on its type."""
        match t:
            case 0:
                # calculate parity to check if packet is valid
                if True:#self._verify_checksum(packet):
                    self.r = packet
                    self.last_checksum = struct.unpack('<H', packet[8:10])
                    self.buf = self.buf[10:]
                    return packet
                else:
                    return None
            case 1:
                if True:#packet[2:4] == self.last_checksum.to_bytes(2, byteorder='little'):
                    return "ACK"
                else:
                    return None

    
    # Function to create a packet with the 3 validity bits, 5 boolean values, and velocity(int16_t)
    def send_packet(self, mot_en, mot_stl, enc_rst, velocity):
        
        bool_byte = 0x00000010
        bool_byte |= mot_en << 4
        bool_byte |= mot_stl << 3
        bool_byte |= enc_rst << 2
        # Create the byte packet
        packet = struct.pack('<BBhB', self.start_byte, bool_byte, velocity, self.end_byte)
        if self.s and self.s.is_open:
            self.s.write(packet)

    def send_ack(self):
        if self.s and self.s.is_open:
            self.s.write(self.ack_pack)

    def read_data(self):
        data = self.readline()
        # if second byte is also a start byte, it is a data packet
        if data is not None:
            try:
                if data[1] == self.start_byte:
                    self.send_ack()
                    return self.unpack_data(data)
                elif data[1] == self.ack_byte:
                    self.ack = True
                else:
                    print("Invalid data packet received: ", data)
            except IndexError:
                print("Invalid data packet received: ", data)
        else:
            return None

    def unpack_data(self, data):
        
        try:
            # Unpack the data
            start, type_byte, bool_byte, velocity, position, checksum, end = struct.unpack('<BBBhhhB', data)
            # Extract the boolean values
            mot_en = (bool_byte >> 4) & 0x01
            mot_stl = (bool_byte >> 3) & 0x01
            enc_rst = (bool_byte >> 2) & 0x01
            return mot_en, mot_stl, enc_rst, velocity, position-self.pos_offset, checksum
        except struct.error:
            print("Error unpacking data. Length of data: ", len(data), "Data: ", data)
            
    def send_data_request(self):
        if self.s and self.s.is_open:
            self.s.write(self.data_request_pack)
            
    def reset_encoder(self):
        self.send_packet(0, 0, 1, 0)
        if self.s and self.s.is_open:
            pass


class SerialCommunication:
    def __init__(self):
        self.port = None
        self.port_name = None
        self.reader = None

        # Device's specific IDs or keyword
        self.vendor_id = "1A86"  
        self.product_id = "7523"  

        self.baud = 115200#460800 #
        self.start_byte = 0x8e
        self.end_byte = 0x0a
        self.ack_pack = struct.pack('@BBB', self.start_byte, 0x01, self.end_byte)
        self.data_request_pack = struct.pack('@BBB', self.start_byte, 0x02, self.end_byte)

    def find_device(self, vendor_id=None, product_id=None, keyword=None):
        """
        Find the COM port of a device by vendor ID, product ID, or keyword in the description.

        Args:
            vendor_id (str): USB Vendor ID (optional).
            product_id (str): USB Product ID (optional).
            keyword (str): A keyword to search in the port description (optional).

        Returns:
            str: The COM port name if found, otherwise None.
        """
        ports = serial.tools.list_ports.comports()

        for port in ports:
            # Check Vendor ID and Product ID
            if vendor_id and product_id:
                if (port.vid == int(vendor_id, 16)) and (port.pid == int(product_id, 16)):
                    return port.device
            
            # Check for a keyword in the description
            if keyword and keyword.lower() in port.description.lower():
                return port.device
        
        return None

    def connect(self):
        try:
            self.port_name = self.find_device(vendor_id=self.vendor_id, product_id=self.product_id)
            if not self.port_name:
                #print("ESP32 not found.")
                return False
            self.port = serial.Serial(self.port_name, baudrate=self.baud, timeout=1)
            self.port.set_buffer_size(rx_size=50, tx_size=50)
            self.rl = ReadLine(self.port)
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def disconnect(self):
        if self.port and self.port.is_open:
            self.port.close()

    def send(self, data):
        if self.port and self.port.is_open:
            self.port.write(data.encode())

    def read(self):
        if self.port and self.port.is_open and self.port.in_waiting:
            return self.port.readline().decode().strip()
        return None
    
    # def read_data(self):
    #     if self.port and self.port.is_open:# and self.port.in_waiting:
    #         return self.port.readline()
    #         #return self.rl.readline()
    #     return None

    # def reset_encoder(self):
    #     self.send_packet(0, 0, 1, 0)
    #     if self.port and self.port.is_open:
    #         print("Encoder reset.")

    # # Function to create a packet with the 3 validity bits, 5 boolean values, and velocity(int16_t)
    # def send_packet(self, mot_en, mot_stl, enc_rst, velocity):
        
    #     bool_byte = 0x00000010
    #     bool_byte |= mot_en << 4
    #     bool_byte |= mot_stl << 3
    #     bool_byte |= enc_rst << 2
    #     # Create the byte packet
    #     packet = struct.pack('<BBhB', self.start_byte, bool_byte, velocity, self.end_byte)
    #     if self.port and self.port.is_open:
    #         self.port.write(packet)
    
    # def send_ack(self):
    #     if self.port and self.port.is_open:
    #         self.port.write(self.ack_pack)
   
    def send_data_request(self):
        if self.port and self.port.is_open:
            self.rl.send_data_request
    
    
    # def unpack_data(self, data):
    #     # Unpack the data
    #     start, bool_byte, velocity, position, end = struct.unpack('<BBhqB', data)
    #     # Extract the boolean values
    #     mot_en = (bool_byte >> 4) & 0x01
    #     mot_stl = (bool_byte >> 3) & 0x01
    #     enc_rst = (bool_byte >> 2) & 0x01
    #     return mot_en, mot_stl, enc_rst, velocity, position
        
        
        

    

class EMG_Shimmer():
    def __init__(self):
        self.TYPE = util.SHIMMER_ExG_0
        self.shimmer_output_processed = 0
        self.device_name = "Shimmer3-4CBE" # Bluetooth device name
        self.PORT = None
        self.sensor_idx = 1
        self.buffer_size = 1000
        self.sensor1_data = np.zeros(self.buffer_size)
        self.sensor2_data = np.zeros(self.buffer_size)
        self.velocity_output = 0
        self.shimmer_device = None
        self.Filter =  filter.Signal()
        self.initialized = False
        self.up_counter = 0
        self.down_counter = 0
        self.control_freq = 10 # Hz

    def find_bluetooth_com_port(self, device_name=None, target_mac=None):
        """
        Find the active COM port of a Bluetooth device by its MAC address or device name.

        Args:
            device_name (str): The friendly name of the Bluetooth device.
            target_mac (str): The MAC address of the Bluetooth device (e.g., 00:06:66:FB:4C:BE).

        Returns:
            str: The active COM port name if found, otherwise None.
        """
        ports = serial.tools.list_ports.comports()

        for port in ports:
            #print(f"Checking port: {port.device}, Description: {port.description}, HWID: {port.hwid}")  # Debug output

            # Match by hardware ID for SPP (Serial Port Profile)
            if "BTHENUM\\{00001101-0000-1000-8000-00805F9B34FB}" in port.hwid.upper():
                # Optionally, match the MAC address in the HWID
                if target_mac and target_mac.replace(":", "").lower() in port.hwid.lower():
                    try:
                        # Try opening the port and check if it's responsive
                        with serial.Serial(port.device, 9600, timeout=1) as ser:
                            # Send a test command (replace with one your device responds to)
                            #print(f"Checking if {port.device} is active...")
                            ser.write(b'AT\r\n')  # Example command, replace with one supported by your device
                            time.sleep(0.5)  # Wait for response
                            if ser.in_waiting > 0:  # Check if there's any data received
                                print(f"Active device found on {port.device}")
                                return port.device
                    except serial.SerialException:
                        # If we can't open the port, it's not active
                        pass
                elif device_name and device_name.lower() in port.description.lower():
                    try:
                        # Check if the port is active by opening it
                        with serial.Serial(port.device, 9600, timeout=1) as ser:
                            # Send a test command
                            ser.write(b'AT\r\n')
                            time.sleep(0.5)
                            if ser.in_waiting > 0:
                                print(f"Active device found on {port.device}")
                                return port.device
                    except serial.SerialException:
                        pass

        print("No active Bluetooth COM port found.")
        open_windows_bluetooth_settings()
        return None

    def connect(self):
        try:
            self.PORT = self.find_bluetooth_com_port(self.device_name, "00:06:66:C5:5F:90")
            self.shimmer_device = shimmer.Shimmer3(self.TYPE, debug=True)
            self.res = self.shimmer_device.connect(com_port=self.PORT, write_rtc=True, update_all_properties=True, reset_sensors=True)
            self.shimmer_device.set_sampling_rate(650)
            self.shimmer_device.set_enabled_sensors(util.SENSOR_ExG1_16BIT, util.SENSOR_ExG2_16BIT)
            if self.res:
                self.initialized = True
        except Exception as e:
            print(f"Error: {e}")
            return

    def start_shimmer(self):
        try:
            # Ensure shimmer device starts
            self.shimmer_device.start_bt_streaming()
            self.running = True

            # Create new threads
            self.data_thread = threading.Thread(target=self.data_collection, daemon=True)
            self.process_thread = threading.Thread(target=self.process_data, daemon=True)
            self.data_lock = threading.Lock()

            # Start the threads
            self.data_thread.start()
            self.process_thread.start()
            return True
        except Exception as e:
            print(f"Error starting Shimmer: {e}")
            self.running = False
            return False

    def stop_shimmer(self):
        try:
            # Stop shimmer device
            self.shimmer_device.stop_bt_streaming()

            # Signal threads to stop
            self.running = False

            # Wait for threads to finish
            if self.data_thread and self.data_thread.is_alive():
                self.data_thread.join()
            if self.process_thread and self.process_thread.is_alive():
                self.process_thread.join()

            print("Shimmer stopped successfully.")
        except Exception as e:
            print(f"Error stopping Shimmer: {e}")


    # Function to get the data as a contiguous, ordered array for filtering
    def get_sequential_data(self, buffer, start_index):
        return np.concatenate((buffer[start_index:], buffer[:start_index]))

    def data_collection(self):
        while self.running:
            n_of_packets, packets = self.shimmer_device.read_data_packet_extended()
            if n_of_packets > 0:
                # Extract sensor1 and sensor2 data for all packets at once
                sensor1_values = np.array([packet[3] for packet in packets])
                sensor2_values = np.array([packet[4] for packet in packets])
                num_new = len(sensor1_values)

                # Insert new data in circular fashion
                for i in range(num_new):
                    self.sensor1_data[(self.sensor_idx + i) % self.buffer_size] = sensor1_values[i]
                    self.sensor2_data[(self.sensor_idx + i) % self.buffer_size] = sensor2_values[i]

                # Update index to the next write position in the circular buffer
                self.sensor_idx = (self.sensor_idx + num_new) % self.buffer_size

    def process_data(self):
        update_freq = self.control_freq
        total_updates = update_freq
        timer_update_start = time.time()
        sleep_time = 1/update_freq
        # Wait 1 second for data to be collected
        time.sleep(1)

        while self.running:
            sensor1_sequential = self.get_sequential_data(self.sensor1_data, self.sensor_idx)
            sensor2_sequential = self.get_sequential_data(self.sensor2_data, self.sensor_idx)
            self.Filter.set_signal(sensor1_sequential, sensor2_sequential)
            self.shimmer_output_processed = self.Filter.get_filtered_signals()
            self.control_output = self.Filter.get_control_value()
            # Dynamic sleep time adjuster for specified frequency
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

    def calibrate(self, target_max_value = 70, max_muscle_exertion = 0.5):
        calibrations_values = []
        colleting_calibration_values = True
        def collect_calibration_values():
            while colleting_calibration_values:
                # Add control_value to calibrations_values list
                calibrations_values.append(self.control_output)
                # Wait for new data
                time.sleep(1/self.control_freq)

        # Start new thread
        calibrate_thread = threading.Thread(target=collect_calibration_values, daemon=True)
        calibrate_thread.start()

        # Wait for calibration values to be collected
        input("Press Enter to stop collecting calibration values...")
        # Stop the thread
        colleting_calibration_values = False        

        # Save calibration 
        min_value = min(calibrations_values) * max_muscle_exertion
        max_value = max(calibrations_values) * max_muscle_exertion
        multiplier_biceps = (target_max_value / max_value) * self.Filter.multiplier_biceps
        multiplier_triceps = (target_max_value / abs(min_value)) * self.Filter.multiplier_triceps
        self.Filter.set_multipliers(multiplier_biceps, multiplier_triceps)

        # Print calibration values
        print(f"Min calibration value: {min_value}")
        print(f"Max calibration value: {max_value}")
        print(f"Multiplier biceps: {multiplier_biceps}")
        print(f"Multiplier triceps: {multiplier_triceps}")




            

            

        


        
