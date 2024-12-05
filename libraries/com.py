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

def open_windows_bluetooth_settings():
        if platform.system() == "Windows":
            subprocess.run(["start", "ms-settings:bluetooth"], shell=True)
        else:
            print("This feature is only supported on Windows.")

class SerialCommunication:
    def __init__(self):
        self.port = None
        self.port_name = None
        self.reader = None

        # Device's specific IDs or keyword
        self.vendor_id = "1A86"  
        self.product_id = "7523"  


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
            self.port = serial.Serial(self.port_name, baudrate=115200, timeout=1)
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

    def reset_encoder(self):
        self.send("0,0,0,1\n")
        print("Encoder reset.")

    

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
        self.colleting_calibration_values = True

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
            #print(f"Sensor1: {sensor1_sequential[-1]}, Sensor2: {sensor2_sequential[-1]}")
            self.Filter.set_signal(sensor1_sequential, sensor2_sequential)
            self.shimmer_output_processed = self.Filter.get_filtered_signals()
            self.control_output = self.Filter.get_control_value()
            #print(f"Control output: {self.control_output}")
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

    def calibrate(self, target_max_value = 70, max_muscle_exertion = 0.5, min_muscle_exertion = 0.05):
        calibrations_values = []
        run = time.time()
        while run + 10 > time.time():
            # Add control_value to calibrations_values list
            calibrations_values.append(self.control_output)
            # Wait for new data
            time.sleep(1/self.control_freq)
     
        # Save calibration 
        min_value = min(calibrations_values)
        max_value = max(calibrations_values) 
        multiplier_biceps = (target_max_value / max_value) * self.Filter.multiplier_biceps
        multiplier_triceps = (target_max_value / abs(min_value)) * self.Filter.multiplier_triceps
        activation_threshold = min_muscle_exertion * (multiplier_biceps + multiplier_triceps) / 2
        multiplier_biceps *= max_muscle_exertion
        multiplier_triceps *= max_muscle_exertion
        self.Filter.set_multipliers(multiplier_biceps, multiplier_triceps, activation_threshold)

        # Print calibration values
        print(f"Min calibration value: {min_value}")
        print(f"Max calibration value: {max_value}")
        print(f"Multiplier biceps: {multiplier_biceps}")
        print(f"Multiplier triceps: {multiplier_triceps}")
        print(f"Activation threshold: {activation_threshold}")




            

            

        


        
