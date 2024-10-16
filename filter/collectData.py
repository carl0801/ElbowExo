import shimmer
import util
import subprocess
import threading
import serial
import pickle
import time
stop = False

def run_command(command):
    try:
        print(command)
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(result.stdout.decode())
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr.decode()}")


shimmer_device = shimmer.Shimmer3(util.SHIMMER_ExG_0, debug=False)
def connectShimmer():
    # Make rfcomm port
    mac_address = '00:06:66:FB:4C:BE'
    rfport_thread = threading.Thread(target=run_command, args=(f'sudo rfcomm connect /dev/rfcomm0 {mac_address}',))
    rfport_thread.start()
    time.sleep(5)
    run_command('sudo chmod 666 /dev/rfcomm0')

    PORT = "/dev/rfcomm0"
    # Initialize Shimmer
    shimmer_device.connect(com_port=PORT, write_rtc=True, update_all_properties=True, reset_sensors=True)
    shimmer_device.set_sampling_rate(650)
    shimmer_device.set_enabled_sensors(util.SENSOR_ExG1_16BIT, util.SENSOR_ExG2_16BIT)
    shimmer_device.set_exg_gain(util.ExG_GAIN_12)
    #shimmer_device.print_object_properties()
    #print(shimmer_device.get_available_sensors())

    shimmer_device.start_bt_streaming()


shimmer_data = []
def readShimmer():
    connectShimmer()
    while True:
        n_of_packets, packets = shimmer_device.read_data_packet_extended()
        if n_of_packets > 0:
            for packet in packets:
                # Calculate the time stamp between RTCcurrent and RTCstart
                timestamp = packet[2] - packet[1]
                sensor1 = packet[3]
                sensor2 = packet[4]

                # Store data
                shimmer_data.append([timestamp, sensor1, sensor2])
                #print(f"{timestamp}:\t {sensor1} : {sensor2}                     ", end="\r")
        if stop == True:
            save_data(shimmer_data, "shimmer")
            shimmer_device.stop_bt_streaming()
            shimmer_device.disconnect(reset_obj_to_init=True)
            print("Stopped Shimmer")
        

# Configure serial port settings
SERIAL_PORT = '/dev/ttyACM0'  # Change to your serial port
BAUD_RATE = 115200       # Change to your baud rate
loadcell_data = []
def readLoadcell():
    run_command('sudo chmod 666 /dev/ttyACM0')
    time.sleep(5)
    # Initialize serial connection
    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
        loadcell_data = []
        ser.reset_input_buffer()  # Clear the input buffer
        
        print("Starting to read from serial port...")
        while True:
            line = ser.readline().decode('utf-8').strip()  # Read a line from serial
            if line:  # Ensure the line is not empty
                try:
                    # Split the line into timestamp and reading
                    timestamp_str, reading_str = line.split(':')
                    # Convert to signed ints
                    timestamp = int(timestamp_str)
                    reading = int(reading_str)
                    loadcell_data.append((timestamp, reading))  # Save time and reading
                    #print(f"Timestamp: {timestamp}, Reading: {reading}                    ", end="\r")
                except ValueError:
                    print(f"Invalid format or integer: {line}")
                    if line == "Tareing....":
                        loadcell_data = []
            if stop == True:
                save_data(loadcell_data, "loadcell")
                ser.close()
                print("Stopped Serial readings.")

def save_data(array, name):
    file_name = f"data/{time.time()}-{name}.pkl"
    with open(file_name, 'wb') as f:
        pickle.dump(array, f)
    print("Data saved.")

if __name__ == "__main__":
    # Create threads
    thread1 = threading.Thread(target=readShimmer)
    thread2 = threading.Thread(target=readLoadcell)

    # Require sudo permissions
    run_command('sudo chmod 666 /dev/ttyACM0')

    # Start threads
    thread1.start()
    thread2.start()

    # Keep the main thread alive
    # Wait for input
    input("Press Enter to exit...")
    stop = True
    print("\nMain thread: Exiting...")
    thread1.join()  # Ensure threads finish
    thread2.join()  # Ensure threads finish