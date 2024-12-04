
import sys
import numpy as np
import datetime
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QMessageBox, QLineEdit, QDesktopWidget, QCheckBox
from PyQt5.QtGui import QTextCursor, QPixmap, QIcon
from PyQt5.QtCore import Qt, QTimer
from PyQt5 import uic

# Import the SerialCommunication and EMG_Shimmer classes from the libraries module
from libraries.com import SerialCommunication, EMG_Shimmer
import app_dependency.design as design
import libraries.loadData as loadData


class MainWindow(QMainWindow):
    def __init__(self, test_mode=False):
        super(MainWindow, self).__init__()
        uic.loadUi(design.UI_FILE_PATH, self)
        self.collums = design.CULLOMS
        self.titles = design.TITLES
        self.test_mode = False
        self.emg_signal = []

        # Set the application icon
        self.setWindowIcon(QIcon(design.APP_ICON))

        self.encoder_range = 1100-40
        self.sent_velocity = 0
        self.encoder_value = 0
        self.image_index = 0
        self.image_target = 0
        self.images = design.EXO_IMAGES

        self.serial_comm = SerialCommunication()
        self.EmgUnit = EMG_Shimmer()
        self.startTime = datetime.datetime.now()
        self.consolebuffer = np.empty(100, dtype=object)

        self.checkbox = self.findChild(QCheckBox, 'test_mode_checkbox')
        self.checkbox.stateChanged.connect(self.update_test_mode)

        self.bind_output = False
        self.connection_status = False

        screen = QDesktopWidget().screenGeometry()
        width = int(screen.width() * 0.7)
        height = int(screen.height() * 0.7)
        self.setGeometry(0, 0, width, height)
        self.add_graph()
        self.control_output_prev = 0
        # Init timers
        self.animation_timer = self.create_timer(10, self.update_frame)
        self.resize_timer = self.create_timer(0, self.resize_window, single_shot=True)
        
        # Animations
        self.shimmer_status_animation = design.color_animation(self.shimmer_status, design.RED)

        # Add returnPressed signal to the velocity input field
        self.findChild(QLineEdit, 'velocity_input').returnPressed.connect(lambda: self.on_button_click('send_velocity'))
        
        # Initialize the buttons and connect them to the corresponding functions
        for button in self.findChildren(QPushButton):
            button.clicked.connect(lambda _, name=button.objectName(): self.on_button_click(name.replace('_button', '')))
    
    def update_test_mode(self, state):
        # Update the self.test_mode variable based on checkbox state
        self.test_mode = state == 2  # True if checked, False otherwise
                # Load the shimmer data if the test mode is enabled

        if self.test_mode:
            self.shimmer_data = loadData.loadShimmer(n=1)
            self.EmgUnit.Filter.set_signal(self.shimmer_data[:, 1], self.shimmer_data[:, 2])
            self.test_control_output = self.EmgUnit.Filter.get_control_signal()
            self.test_samples = 0
        
        if self.bind_output and not self.test_mode:
            if self.update_timer_vel.isActive():
                self.stop_send_velocity_from_shimmer()
                self.bind_output = False
                self.test_samples = len(self.shimmer_data)
                self.bind_output_button.setText("Bind Output")
                self.bind_output_button.setStyleSheet(design.BLUE_BUTTON)

        self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} Test Mode is {'enabled' if self.test_mode else 'disabled'}")

    def resizeEvent(self, event):
        # Stop the timer if it's already running
        if self.resize_timer.isActive():
            self.resize_timer.stop()

        # Start the timer again with a delay
        self.resize_timer.start(10)  # Wait for 10 ms after the resize event to trigger

        # Optionally, call the base class implementation
        super().resizeEvent(event)

    def resize_window(self):
        
        # Adjust the size of the widgets
        for column in self.collums:
            self.findChild(QWidget, f'{column}').setFixedWidth(int(self.width()/3.1))

        # Adjust the size of the titles
        for title in self.titles:
            self.findChild(QWidget, f'{title}').setFixedHeight(int(self.height()/15))
        
        # Adjust the size of the buttons
        for button in self.findChildren(QPushButton):
            button.setFixedHeight(int(self.height()/20))
        
        self.findChild(QPushButton, 'bind_output_button').setFixedWidth(int(self.width()/5))
        self.findChild(QCheckBox, 'test_mode_checkbox').setFixedWidth(int(self.width()/20))

        # Adjust the size of the groupboxes
        self.control_shimmer_groupbox.setFixedHeight(int(self.height()/2.2))
        self.motor_groupbox.setFixedHeight(int(self.height()/2.2))
        self.information_groupbox.setFixedHeight(int(self.height()/2.2))
        self.muscle_graph_groupbox.setFixedHeight(int(self.height()/2.2))
        self.console_groupbox.setFixedHeight(int(self.height()/2.2))
        self.animation_groupbox.setFixedHeight(int(self.height()/2.2))

        # Adjust the size of the graph
        self.block_graph.setFixedHeight(int(self.height() / 5))
        self.block_graph.setFixedWidth(int(self.width() / 4.5))

    def image_loader(self):
        pixmap = QPixmap(self.images[self.image_index])
        pixmap = pixmap.scaled(self.animation_widget.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        # Make the white background color transparent
        pixmap.setMask(pixmap.createMaskFromColor(Qt.white, Qt.MaskInColor))

        self.animation_widget.setPixmap(pixmap)

        return

    def update_frame(self):

        self.image_loader()
        # Check if the image index is within the bounds of the list
        if self.image_target >= len(self.images):
            self.image_target = len(self.images) - 1
        elif self.image_target < 0:
            self.image_target = 0

        if self.image_index < self.image_target:
            self.image_loader()
            self.image_index += 1

        elif self.image_index > self.image_target:
            self.image_loader()
            self.image_index -= 1

    def send_velocity_from_shimmer(self):
        if self.test_mode:
            if self.test_samples < len(self.shimmer_data):
                if self.print_velocity % 10 == 0:
                    self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Sent velocity: {int(self.test_control_output[self.test_samples]*100)}")
                self.print_velocity += 1
                self.test_samples +=10
                self.serial_comm.send(f"{int(self.test_control_output[self.test_samples]*100)},1,0,0\n")
            else:
                self.stop_send_velocity_from_shimmer()
                self.bind_output = False
                self.test_samples = len(self.shimmer_data)
        else:    
            if abs(self.EmgUnit.control_output - self.control_output_prev) > 5:
                self.control_output_prev = self.EmgUnit.control_output
                
                if self.print_velocity % 1 == 0:
                    self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Sent velocity: {int(self.EmgUnit.control_output)}")
                self.print_velocity += 1
                self.serial_comm.send(f"{int(self.EmgUnit.control_output)},1,0,0\n")

    

    def start_send_velocity_from_shimmer(self):
        self.update_timer_vel = self.create_timer(200, self.send_velocity_from_shimmer)
    
    def stop_send_velocity_from_shimmer(self):
        self.update_timer_vel.stop()

    def add_graph(self):
         # Block Graph for Muscle Block Visualization
        self.block_graph = pg.PlotWidget(background=design.BACKGROUND_COLOR.name())
        self.block_graph.setYRange(-1, 1)  # Set the range of the y-axis
        self.block_graph.setXRange(-0.8, 0.9)  # Center the bar graph
        self.block_graph.hideAxis('bottom')
        self.block_graph.hideAxis('left')
        self.block_graph.hideAxis('right')
        self.block_graph.hideAxis('top')

        self.bar_item1 = pg.BarGraphItem(x=[-0.6], height=[100], width=0.7, brush='#007BFF')
        self.bar_item2 = pg.BarGraphItem(x=[0.6], height=[100], width=0.7, brush='#007BFF')
        self.block_graph.addItem(self.bar_item1)
        self.block_graph.addItem(self.bar_item2)

        self.block_graph.setFixedHeight(int(self.height() / 5))
        self.block_graph.setFixedWidth(int(self.width() / 4.5))
        self.block_graph.setStyleSheet("border: none;")
        self.block_graph.addLegend()

        # Add the block graph to the layout
        self.muscle_graph_layout.addWidget(self.block_graph, alignment=Qt.AlignCenter)

    def create_timer(self, frequency, callback, single_shot=False):
        '''Create a QTimer object that triggers the callback function at the specified frequency.'''
        timer = QTimer()
        timer.timeout.connect(callback)

        if single_shot:
            timer.setSingleShot(True)
        else:
            timer.start(frequency) 
        
        return timer

    def toggle_connection(self):
        self.connect_serial_button_animation = design.shake_animation(self.connect_serial_button)
        if self.connection_status:
            self.serial_comm.disconnect()
            self.update_serial_timer.stop()
            self.connection_status = False
            self.connect_serial_button.setStyleSheet(design.GREEN_BUTTON)
            self.enable_motor_button.setStyleSheet(design.GREEN_BUTTON)
            self.stall_motor_button.setText("")
            self.stall_motor_button.setStyleSheet(design.GREEN_BUTTON)
            self.connect_serial_button.setText("Connected to Serial")
            self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Disconnected from the serial port.")
        else:
            if self.serial_comm.connect():
                self.update_serial_timer = self.create_timer(50, self.update_serial_data)
                self.connection_status = True
                self.connect_serial_button.setText("Disconnect from Serial")
                self.connect_serial_button.setStyleSheet(design.RED_BUTTON)
                #print("Connected to the serial port.")
                self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Connected to the serial port.")
            else:
                self.connect_serial_button_animation.start()
                self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - ESP32 not found.")

    def toggle_motor_enable(self):
        if self.connection_status:
            if self.MotorEnabled:
                self.serial_comm.send(f"{self.sent_velocity},0,1,0\n")
                self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Disabled Motor")
            else:
                self.serial_comm.send(f"{self.sent_velocity},1,1,0\n")
                self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Enabled Motor")
        
    def update_serial_data(self):
        if self.connection_status:
            try:
                data = self.serial_comm.read()
                if data:
                    parts = list(map(int, data.split(',')))
                    self.stall_guard_label.setText(f"StallGuard: {parts[0]}")
                    self.velocity_label.setText(f"Velocity: {parts[1]}")
                    self.MotorEnabled = bool(parts[3])
                    if len(parts) > 5:
                        self.encoder_label.setText(f"Encoder: {parts[5]}")
                        self.encoder_value = parts[5]
                        self.image_target = int(self.encoder_value / (self.encoder_range/len(self.images)))
                    if self.MotorEnabled:
                        self.enable_motor_button.setText("Disable Motor")
                        self.enable_motor_button.setStyleSheet(design.RED_BUTTON)
                    else:
                        self.enable_motor_button.setText("Enable Motor")
                        self.enable_motor_button.setStyleSheet(design.GREEN_BUTTON)
                    self.MotorStalled = bool(parts[4])
                    if self.MotorStalled or not bool(parts[1]) and self.MotorEnabled:
                        self.stall_motor_button.setText("Motor is stopped")
                        #self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Motor is stopped")
                        self.stall_motor_button.setStyleSheet(design.RED_BUTTON)
                    elif self.MotorEnabled:
                        self.stall_motor_button.setText("Motor is running")
                        self.stall_motor_button.setStyleSheet(design.GREEN_BUTTON)
            except Exception as e:
                print(f"Error reading from serial port: {e}")            

    def update_block_graph(self):
        self.muscleBlock1 = (self.EmgUnit.shimmer_output_processed) 
        #self.muscleBlock2 = np.mean(self.EmgUnit.shimmer_output_processed[1])
        self.bar_item1.setOpts(height=self.muscleBlock1)
        self.bar_item2.setOpts(height=1)
        if self.muscleBlock1 > 0:
            self.bar_item1.setOpts(brush='#007BFF')
        else:
            self.bar_item1.setOpts(brush='#E57373')
       

    def start_block_graph_update(self):
        self.update_timer = self.create_timer(200, self.update_block_graph)

    def stop_block_graph_update(self):
        self.update_timer.stop()

    def bind_output_start(self):
        if self.bind_output:
            self.bind_output = False
            self.stop_send_velocity_from_shimmer()
            self.bind_output_button.setText("Bind Output")
            self.bind_output_button.setStyleSheet(design.BLUE_BUTTON)
            self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Unbound the output from the shimmer.")
        else:
            self.bind_output = True
            self.start_send_velocity_from_shimmer()
            self.bind_output_button.setText("Unbind Output")
            self.bind_output_button.setStyleSheet(design.RED_BUTTON)
            self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Bound the output to the shimmer.")

    def on_button_click(self, button):
        if button == 'initialize_shimmer':
            if not self.EmgUnit.initialized:
                self.shimmer_status_animation.stop()
                self.shimmer_status_animation = design.color_animation(self.shimmer_status, design.YELLOW)
                self.EmgUnit.connect()
                time_2 = datetime.datetime.now().strftime('%H:%M')
                #self.handle_console_output(f'{time_2} - Button 2 was clicked')
                if self.EmgUnit.initialized:
                    
                    self.handle_console_output(f'{datetime.datetime.now().strftime("%H:%M")} - Shimmer Initialized')
                    self.initialize_shimmer_button.setText("Disconnect Shimmer")
                    self.initialize_shimmer_button.setStyleSheet(design.RED_BUTTON)

                elif not self.EmgUnit.initialized:
                    self.handle_console_output(f'{datetime.datetime.now().strftime("%H:%M")} - Shimmer Initialization failed')
                    self.shimmer_status_animation.stop()
                    self.shimmer_status_animation = design.color_animation(self.shimmer_status, design.RED)
                    
            
            # Disconnect the shimmer
            elif self.EmgUnit.initialized:
                self.EmgUnit.initialized = False
                self.handle_console_output(f'{datetime.datetime.now().strftime("%H:%M")} - Shimmer disconnected')
                self.EmgUnit.shimmer_device.disconnect()
                self.shimmer_status_animation.stop()
                self.shimmer_status_animation = design.color_animation(self.shimmer_status, design.RED)
                self.initialize_shimmer_button.setText("Initialize Shimmer")
                self.initialize_shimmer_button.setStyleSheet(design.GREEN_BUTTON)

        elif button == 'start_streaming':
            self.start_streaming_animation = design.shake_animation(self.start_streaming_button)
            if self.EmgUnit.initialized:
                time_3 = datetime.datetime.now().strftime('%H:%M')
                #self.handle_console_output(f'{time_3} - Button 3 was clicked')
                res = self.EmgUnit.start_shimmer()
                if res:
                    self.handle_console_output(f'{datetime.datetime.now().strftime("%H:%M")} - Shimmer streaming started')
                    self.shimmer_status_animation.stop()
                    self.shimmer_status_animation = design.color_animation(self.shimmer_status, design.GREEN)
                    self.start_block_graph_update()

                else:
                    self.handle_console_output(f'{datetime.datetime.now().strftime("%H:%M")} - Shimmer streaming failed')
                    self.shimmer_status_animation.stop()
                    self.shimmer_status_animation = design.color_animation(self.shimmer_status, design.RED)
            else:
                self.start_streaming_animation.start()
                self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Shimmer not initialized.")

                
        elif button == 'stop_streaming':
            self.stop_streaming_animation = design.shake_animation(self.stop_streaming_button)
            if self.EmgUnit.initialized:
                time_4 = datetime.datetime.now().strftime('%H:%M')
                #self.handle_console_output(f'{time_4} - Button 4 was clicked')
                self.EmgUnit.stop_shimmer()
                self.handle_console_output(f'{datetime.datetime.now().strftime("%H:%M")} - Shimmer streaming stopped')
                self.shimmer_status_animation.stop()
                self.shimmer_status_animation = design.color_animation(self.shimmer_status, design.YELLOW)
                if self.update_timer.isActive():
                    self.stop_block_graph_update()
            else:
                self.stop_streaming_animation.start()
                self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Shimmer not initialized.")
        
        elif button == 'send_velocity':
            self.send_velocity_animation = design.shake_animation(self.send_velocity_button)
            self.sent_velocity = 0
            if self.connection_status:
                time_5 = datetime.datetime.now().strftime('%H:%M')
                #self.handle_console_output(f'{time_5} - Button 5 was clicked')
                if self.connection_status:
                    try:
                        velocity = int(self.findChild(QLineEdit, 'velocity_input').text())
                        self.sent_velocity = velocity
                        self.serial_comm.send(f"{velocity},1,0,0\n")
                        self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Sent velocity: {velocity}")
                    except ValueError:
                        QMessageBox.warning(self, "Input Error", "Please enter a valid velocity.")

                # Clear the input field
                self.findChild(QLineEdit, 'velocity_input').clear()
            else:
                self.send_velocity_animation.start()
                self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Not connected to the serial port.")
        
        elif button == 'enable_motor':
            self.enable_motor_animation = design.shake_animation(self.enable_motor_button)
            if self.connection_status:
                time_6 = datetime.datetime.now().strftime('%H:%M')
                #self.handle_console_output(f'{time_6} - Button 6 was clicked')
                self.toggle_motor_enable()
            else:
                self.enable_motor_animation.start()
                self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Not connected to the serial port.")
        
        elif button == 'stall_motor':
            self.stall_motor_animation = design.shake_animation(self.stall_motor_button)
            if self.connection_status:
                time_7 = datetime.datetime.now().strftime('%H:%M')
                #self.handle_console_output(f'{time_7} - Button 7 was clicked')
            else:
                self.stall_motor_animation.start()
                self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Not connected to the serial port.")

        elif button == 'connect_serial':
            time_8 = datetime.datetime.now().strftime('%H:%M')
            #self.handle_console_output(f'{time_8} - Button 8 was clicked')
            self.toggle_connection()
        
        elif button == 'bind_output':
            if self.test_mode:
                self.bind_output_animation = design.shake_animation(self.bind_output_button)
                self.print_velocity = 0
                if True:
                    self.bind_output_start()
                else:
                    self.bind_output_animation.start()
                    self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Not connected to the serial port.") 
                
            else:
                self.bind_output_animation = design.shake_animation(self.bind_output_button)
                self.print_velocity = 0
                if self.connection_status:
                    if self.EmgUnit.initialized:
                        #time_9 = datetime.datetime.now().strftime('%H:%M')
                        #self.handle_console_output(f'{time_9} - Button 9 was clicked')
                        self.bind_output_start()
                    else:
                        self.bind_output_animation.start()
                        self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Shimmer not initialized.")
                else:
                    self.bind_output_animation.start()
                    self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Not connected to the serial port.") 

        elif button == 'reset_encoder':
            if self.connection_status:
                #time_10 = datetime.datetime.now().strftime('%H:%M')
                #self.handle_console_output(f'{time_10} - Button 10 was clicked')
                self.serial_comm.reset_encoder()
                self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Encoder reset")
            else:
                self.reset_encoder_animation = design.shake_animation(self.reset_encoder_button)
                self.reset_encoder_animation.start()
                self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Not connected to the serial port.")
            

    def handle_console_output(self, output):
        # Shift the buffer to the left and add the new output at the end
        self.consolebuffer = np.roll(self.consolebuffer, -1)
        self.consolebuffer[-1] = output
        # Update the console output
        self.console_text.setText('\n'.join(filter(None, self.consolebuffer)))
        # Move the cursor to the end of the text
        self.console_text.moveCursor(QTextCursor.End)

    def close_application(self):
            app.exec_()
            self.serial_comm.disconnect()
            self.EmgUnit.stop_shimmer()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(window.close_application())
