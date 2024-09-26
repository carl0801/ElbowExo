import shimmer
import util

TYPE = util.SHIMMER_GSRplus
PORT = "COM5"

shimmer = shimmer.Shimmer3(TYPE, debug=True)
shimmer.connect(com_port=PORT, write_rtc=True, update_all_properties=True, reset_sensors=True)
shimmer.set_sampling_rate(512.0)
shimmer.set_enabled_sensors(util.SENSOR_LOW_NOISE_ACCELEROMETER)
shimmer.print_object_properties()

shimmer.start_bt_streaming()

reads = []

try:
    while True:
        n_of_packets, packets = shimmer.read_data_packet_extended(calibrated=True)
        if n_of_packets > 0:
            for packet in packets:
                print(packet)
except KeyboardInterrupt:
    shimmer.stop_bt_streaming()
    shimmer.disconnect(reset_obj_to_init=True)