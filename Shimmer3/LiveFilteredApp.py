import socket
import shimmer
import util
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
import threading
import filter

TYPE = util.SHIMMER_ExG_0
PORT = "COM5"

# Initialize Shimmer
shimmer = shimmer.Shimmer3(TYPE, debug=True)
shimmer.connect(com_port=PORT, write_rtc=True, update_all_properties=True, reset_sensors=True)
shimmer.set_sampling_rate(200)
shimmer.set_enabled_sensors(util.SENSOR_ExG1_16BIT, util.SENSOR_ExG2_16BIT)

shimmer.start_bt_streaming()

Filter = filter.generate_filter(fs=650)

# Initialize lists to store received data as NumPy arrays
sensor1_data = np.array([])
sensor2_data = np.array([])

# Set up the PyQtGraph plot
app = QtWidgets.QApplication([])
win = pg.GraphicsLayoutWidget(show=True, title="Live Sensor Data")
win.resize(1000, 600)
win.setWindowTitle('Live Sensor Data')

pg.setConfigOptions(antialias=True)

# Create two plots
p1 = win.addPlot(title="Sensor 1")
curve1 = p1.plot(pen='y')
p2 = win.addPlot(title="Sensor 2")
curve2 = p2.plot(pen='r')

def update():
    global sensor1_data, sensor2_data, Filter 
    if len(sensor1_data) > 0:
        sensor1_data_filtered = filter.array_run(sensor1_data, Filter)
        curve1.setData(sensor1_data_filtered)
    if len(sensor2_data) > 0:
        sensor2_data_filtered = filter.array_run(sensor2_data, Filter)
        curve2.setData(sensor2_data_filtered)

def data_collection():
    global sensor1_data, sensor2_data
    try:
        while True:
            n_of_packets, packets = shimmer.read_data_packet_extended()
            if n_of_packets > 0:
                for packet in packets:
                    sensor1 = packet[3]
                    sensor2 = packet[4]

                    # Append data to NumPy arrays
                    sensor1_data = np.append(sensor1_data, sensor1)
                    sensor2_data = np.append(sensor2_data, sensor2)

                    if len(sensor1_data) > 1000:
                        sensor1_data = sensor1_data[-1000:]
                        sensor2_data = sensor2_data[-1000:]
    except KeyboardInterrupt:
        shimmer.stop_bt_streaming()
        shimmer.disconnect(reset_obj_to_init=True)

# Run the data collection in a separate thread
data_thread = threading.Thread(target=data_collection)
data_thread.daemon = True
data_thread.start()

# Set up a timer to update the plot
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(50)  # Update every 50 ms

if __name__ == '__main__':
    QtWidgets.QApplication.instance().exec_()