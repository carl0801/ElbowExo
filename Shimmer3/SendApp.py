import socket
import shimmer
import util
import numpy as np

TYPE = util.SHIMMER_ExG_0
PORT = "COM5"

# Initialize Shimmer
shimmer = shimmer.Shimmer3(TYPE, debug=True)
shimmer.connect(com_port=PORT, write_rtc=True, update_all_properties=True, reset_sensors=True)
shimmer.set_sampling_rate(512)
shimmer.set_enabled_sensors(util.SENSOR_ExG1_16BIT, util.SENSOR_ExG2_16BIT)
shimmer.print_object_properties()
print(shimmer.get_available_sensors())

shimmer.start_bt_streaming()

# Define UDP parameters
udp_ip = "127.0.0.1"  # Localhost
udp_port = 5006

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    while True:
        n_of_packets, packets = shimmer.read_data_packet_extended()
        if n_of_packets > 0:
            for packet in packets:
                sensor1 = packet[3]
                sensor2 = packet[4]
                message = f"Sensor1: {sensor1}, Sensor2: {sensor2}"
                print(f"Sending: {message}")
                sock.sendto(message.encode(), (udp_ip, udp_port))
except KeyboardInterrupt:
    print("KeyboardInterrupt")
    shimmer.stop_bt_streaming()
    shimmer.disconnect(reset_obj_to_init=True)
    sock.close()