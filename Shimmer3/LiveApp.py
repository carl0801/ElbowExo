import socket
import shimmer
import util
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
import threading

TYPE = util.SHIMMER_ExG_0
PORT = "COM5"

# Initialize Shimmer
shimmer = shimmer.Shimmer3(TYPE, debug=True)
shimmer.connect(com_port=PORT, write_rtc=True, update_all_properties=True, reset_sensors=True)
shimmer.set_sampling_rate(200)
shimmer.set_enabled_sensors(util.SENSOR_ExG1_16BIT, util.SENSOR_ExG2_16BIT)
#shimmer.#print_object_properties()
#print(shimmer.get_available_sensors())

shimmer.start_bt_streaming()

# Initialize lists to store received data
sensor1_data = []
sensor2_data = []

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
    curve1.setData(sensor1_data)
    curve2.setData(sensor2_data)
    if len(sensor1_data) > 100:
        compare()

# create a function that prints "up" if the last 100 entries from sensor1 is 10 greater than sensor2 and "down" if sensor2 is 10 greater than sensor1
def compare():
    if len(sensor1_data) >= 100 and len(sensor2_data) >= 100:
        array1 = np.array(sensor1_data[-100:])
        array2 = np.array(sensor2_data[-100:])
        absvar1 = np.var(np.abs(array1))
        absvar2 = np.var(np.abs(array2))
        var1 = np.var(array1)
        var2 = np.var(array2)
        if abs(var1 - var2) > 10:
            print("up")
        elif abs(var2 - var1) > 10:
            print("down")
    


def data_collection():
    try:
        while True:
            n_of_packets, packets = shimmer.read_data_packet_extended()
            if n_of_packets > 0:
                for packet in packets:
                    sensor1 = packet[3]
                    sensor2 = packet[4]
                    #message = f"Sensor1: {sensor1}, Sensor2: {sensor2}"
                    #print(f"Sending: {message}")

                    # Append data to lists
                    sensor1_data.append(sensor1)
                    sensor2_data.append(sensor2)

                    if len(sensor1_data) > 1000:
                        sensor1_data.pop(0)
                        sensor2_data.pop(0)
    except KeyboardInterrupt:
        #print("KeyboardInterrupt")
        shimmer.stop_bt_streaming()
        shimmer.disconnect(reset_obj_to_init=True)

# Run the data collection in a separate thread
data_thread = threading.Thread(target=data_collection)
data_thread.daemon = True
data_thread.start()

# Set up a timer to update the plot
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(5)  # Update every 50 ms

if __name__ == '__main__':
    QtWidgets.QApplication.instance().exec_()