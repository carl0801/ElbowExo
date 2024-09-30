import socket
import threading
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore

# Define UDP parameters
udp_ip = "127.0.0.1"  # Localhost
udp_port = 5006  # Ensure this matches the publisher

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((udp_ip, udp_port))

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

def udp_listener():
    global sensor1_data, sensor2_data
    while True:
        data, addr = sock.recvfrom(1024)  # Buffer size is 1024 bytes
        message = data.decode()
        #print(f"Received message: {message}")

        # Parse the received message
        parts = message.split(", ")
        sensor1 = float(parts[0].split(": ")[1])
        sensor2 = float(parts[1].split(": ")[1])

        sensor1_data.append(sensor1)
        sensor2_data.append(sensor2)

        if len(sensor1_data) > 10000:
            sensor1_data.pop(0)
            sensor2_data.pop(0)

# Run the UDP listener in a separate thread
udp_thread = threading.Thread(target=udp_listener)
udp_thread.daemon = True
udp_thread.start()

# Set up a timer to update the plot
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(50)  # Update every 50 ms

if __name__ == '__main__':
    QtWidgets.QApplication.instance().exec_()