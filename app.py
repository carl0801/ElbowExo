
import sys
import re
import numpy as np
import datetime
import pyqtgraph as pg
import glob
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QMessageBox, QLineEdit, QDesktopWidget, QGraphicsColorizeEffect
from PyQt5.QtGui import QTextCursor, QPixmap
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5 import uic

# Import the SerialCommunication and EMG_Shimmer classes from the libraries module
from libraries.com import SerialCommunication, EMG_Shimmer
import app_dependency.design as design


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('app_dependency/mainwindow.ui', self)
        self.collums = ['menu_widget', 'console_widget', 'statusBar_widget']
        self.image_index = 0
        self.image_target = 1
        self.images = sorted(glob.glob("app_dependency/frames/*.png"))
        self.serial_comm = SerialCommunication()
        self.EmgUnit = EMG_Shimmer()
        self.consolebuffer = np.empty(100, dtype=object)
        self.startTime = datetime.datetime.now()
        self.bind_output = False
        self.connection_status = False
        self.sent_velocity = 0
        self.encoder_value = 0
        self.add_graph()
        screen = QDesktopWidget().screenGeometry()
        width = int(screen.width() * 0.7)
        height = int(screen.height() * 0.7)
        self.setGeometry(0, 0, width, height)
        self.init_timer()

        # Start video frame update
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(50)  # Update every 50 ms

        # Animations
        self.shimmer_status_animation = self.create_color_animation(self.shimmer_status, design.RED)
        
        # Initialize the buttons and connect them to the corresponding functions
        for button in self.findChildren(QPushButton):
            button.clicked.connect(lambda _, name=button.objectName(): self.on_button_click(name.replace('_button', '')))
         
    def resizeEvent(self, event):
        
        for column in self.collums:
            self.findChild(QWidget, f'{column}').setFixedWidth(int(self.width()/3.1))

        # Adjust the size of the groupboxes
        self.control_shimmer_groupbox.setFixedHeight(int(self.height()/2.2))
        self.motor_groupbox.setFixedHeight(int(self.height()/2.2))
        self.information_groupbox.setFixedHeight(int(self.height()/2.2))
        self.muscle_graph_groupbox.setFixedHeight(int(self.height()/2.2))
        self.console_groupbox.setFixedHeight(int(self.height()/2.2))
        self.animation_groupbox.setFixedHeight(int(self.height()/2.2))

        super().resizeEvent(event)

    def update_frame(self):

        # Check if the image index is within the bounds of the list
        if self.image_target >= len(self.images):
            self.image_target = len(self.images) - 1
        elif self.image_target < 0:
            self.image_target = 0


        if self.image_index < self.image_target:
            pixmap = QPixmap(self.images[self.image_index])
            pixmap = pixmap.copy(0, 0, pixmap.width() - 100, pixmap.height())
            pixmap = pixmap.scaled(self.animation_widget.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

            # Make the white background color transparent
            pixmap.setMask(pixmap.createMaskFromColor(Qt.white, Qt.MaskInColor))

            self.animation_widget.setPixmap(pixmap)
            self.image_index += 1

        elif self.image_index > self.image_target:
            pixmap = QPixmap(self.images[self.image_index])
            pixmap = pixmap.copy(0, 0, pixmap.width() - 100, pixmap.height())
            pixmap = pixmap.scaled(self.animation_widget.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

            # Make the white background color transparent
            pixmap.setMask(pixmap.createMaskFromColor(Qt.white, Qt.MaskInColor))

            self.animation_widget.setPixmap(pixmap)
            self.image_index -= 1

    def create_color_animation(self, widget, color):
        # Create a colorize effect for the widget
        effect = QGraphicsColorizeEffect(widget)
        effect.setColor(color)
        
        # Apply the effect to the widget
        widget.setGraphicsEffect(effect)
        
        # Create a property animation on the 'color' property of the effect
        animation = QPropertyAnimation(effect, b"color")
        animation.setDuration(3000)  # Duration of one full cycle (in milliseconds)
        
        # Set the start and end color based on the input color
        animation.setStartValue(color)  # Start color
        
        # Choose the end color based on the current color
        if color == design.RED:
            animation.setEndValue(design.DARKER_RED)  # Darker red
        elif color == design.GREEN:
            animation.setEndValue(design.DARKER_GREEN)  # Darker green
        elif color == design.YELLOW:
            animation.setEndValue(design.DARKER_YELLOW)  # Darker yellow
        
        # Set the keyframes to alternate back and forth
        animation.setKeyValueAt(0.5, animation.endValue())  # Midway through, switch to the end color
        animation.setKeyValueAt(1.0, color)  # At the end, switch back to the start color
        
        # Loop indefinitely
        animation.setLoopCount(-1)  # Infinite loop
        
        # Apply easing curve for smooth animation
        animation.setEasingCurve(QEasingCurve.InOutQuad)

        animation.start()
        
        return animation

    def create_shake_animation(self, button, amplitude=10, duration=200):
        """
        Creates a horizontal shake animation for a button, making it move left and right.

        :param button: The QPushButton to animate.
        :param amplitude: The distance (in pixels) the button moves left and right.
        :param duration: The duration (in milliseconds) for one full shake cycle.
        :return: The QPropertyAnimation instance.
        """

        # Create a property animation on the 'pos' property of the button
        animation = QPropertyAnimation(button, b"pos")
        animation.setDuration(duration)
        
        # Get the button's original position
        original_pos = QPoint(button.x(), button.y())
        #print(original_pos.x(), original_pos.y())
        # Set keyframes for the shake animation
        animation.setKeyValueAt(0.0, original_pos)  # Start at the original position
        animation.setKeyValueAt(0.25, original_pos + QPoint(-amplitude, 0))  # Move left
        animation.setKeyValueAt(0.5, original_pos)  # Return to the center
        animation.setKeyValueAt(0.75, original_pos + QPoint(amplitude, 0))  # Move right
        animation.setKeyValueAt(1.0, original_pos)  # Return to the center

        # Apply easing curve for smooth movement
        animation.setEasingCurve(QEasingCurve.InOutQuad)

        # Loop indefinitely
        animation.setLoopCount(2)

        return animation

    def send_velocity_from_shimmer(self):
        if self.connection_status:
            self.serial_comm.send(f"{self.EmgUnit.shimmer_output_processed},1,0\n")

    def start_send_velocity_from_shimmer(self):
        self.update_timer_vel = QTimer()
        self.update_timer_vel.timeout.connect(self.send_velocity_from_shimmer)
        self.update_timer_vel.start(200)  # Update every 200 ms
    
    def stop_send_velocity_from_shimmer(self):
        self.update_timer_vel.stop()

    def update_stylesheet(self, widget: QWidget, property_name: str, value: str):
        """
        Updates a specific property in a widget's stylesheet.

        Args:
            widget (QWidget): The widget whose stylesheet needs updating.
            property_name (str): The name of the CSS property to update (e.g., "background-color").
            value (str): The new value for the property (e.g., "red", "#FFFFFF").
        """
        # Get the current stylesheet
        current_style = widget.styleSheet()

        # Create the CSS rule for the property
        new_property = f"{property_name}: {value};"

        # Use regex to remove any existing rule for the property
        updated_style = re.sub(fr"{property_name}:\s*[^;]+;", '', current_style)

        # Add the new property to the updated stylesheet
        updated_style += new_property

        # Apply the updated stylesheet to the widget
        widget.setStyleSheet(updated_style)

    def add_graph(self):
        # Block Graph for Muscle Block Visualization
        self.block_graph = pg.PlotWidget(background=design.BACKGROUND_COLOR.name())
        self.block_graph.setYRange(-100, 100)  # Set the range of the y-axis
        self.block_graph.setXRange(-0.2, 0.18)  # Center the bar graph
        self.block_graph.hideAxis('bottom')
        self.block_graph.hideAxis('left')
        self.block_graph.hideAxis('right')
        self.block_graph.hideAxis('top')

        self.bar_item = pg.BarGraphItem(x=[0], height=[100], width=0.5, brush='#007BFF')
        self.block_graph.addItem(self.bar_item)

        
        self.block_graph.setFixedHeight(200)
        self.block_graph.setFixedWidth(int(self.width() / 3.5))
        self.block_graph.setStyleSheet("border: none;")
        self.block_graph.addLegend()

        # Add the block graph to the layout
        self.muscle_graph_layout.addWidget(self.block_graph, alignment=Qt.AlignCenter)

    def init_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_serial_data)
        self.timer.start(50)  # Poll every 100 ms

    def toggle_connection(self):
        self.connect_serial_button_animation = self.create_shake_animation(self.connect_serial_button)
        if self.connection_status:
            self.serial_comm.disconnect()
            self.connection_status = False
            self.connect_serial_button.setStyleSheet(design.GREEN_BUTTON)
            self.enable_motor_button.setStyleSheet(design.GREEN_BUTTON)
            self.stall_motor_button.setStyleSheet(design.GREEN_BUTTON)
            self.connect_serial_button.setText("Connected to Serial")
            self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Disconnected from the serial port.")
        else:
            if self.serial_comm.connect():
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
                self.serial_comm.send(f"{self.sent_velocity},0,1\n")
                self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Disabled Motor")
            else:
                self.serial_comm.send(f"{self.sent_velocity},1,1\n")
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
                    if self.MotorEnabled:
                        self.enable_motor_button.setText("Disable Motor")
                        self.enable_motor_button.setStyleSheet(design.RED_BUTTON)
                    else:
                        self.enable_motor_button.setText("Enable Motor")
                        self.enable_motor_button.setStyleSheet(design.GREEN_BUTTON)
                    self.MotorStalled = bool(parts[4])
                    if self.MotorStalled:
                        self.stall_motor_button.setText("Motor is stopped")
                        self.stall_motor_button.setStyleSheet(design.RED_BUTTON)
                    else:
                        self.stall_motor_button.setText("Motor is running")
                        self.stall_motor_button.setStyleSheet(design.GREEN_BUTTON)
            except Exception as e:
                print(f"Error reading from serial port: {e}")            

    def update_block_graph(self):
        self.muscleBlock = self.EmgUnit.shimmer_output_processed
        self.bar_item.setOpts(height=self.muscleBlock)
        if self.muscleBlock > 0:
            self.bar_item.setOpts(brush='#007BFF')
        else:
            self.bar_item.setOpts(brush='#E57373')

    def start_block_graph_update(self):
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_block_graph)
        self.update_timer.start(200)  # Update every 200 ms

    def stop_block_graph_update(self):
        self.update_timer.stop()

    def bind_output_start(self):
        self.bind_output_animation = self.create_shake_animation(self.bind_output_button)
        if self.EmgUnit.initialized:
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
        else:
            self.bind_output_animation.start()
            self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Shimmer not initialized.") 

    def on_button_click(self, button):
        if button == 'initialize_shimmer':
            if not self.EmgUnit.initialized:
                self.shimmer_status_animation.stop()
                self.shimmer_status_animation = self.create_color_animation(self.shimmer_status, design.YELLOW)
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
                    self.shimmer_status_animation = self.create_color_animation(self.shimmer_status, design.RED)
            
            # Disconnect the shimmer
            elif self.EmgUnit.initialized:
                self.EmgUnit.initialized = False
                self.handle_console_output(f'{datetime.datetime.now().strftime("%H:%M")} - Shimmer disconnected')
                self.EmgUnit.shimmer_device.disconnect()
                self.shimmer_status_animation.stop()
                self.shimmer_status_animation = self.create_color_animation(self.shimmer_status, design.RED)
                self.initialize_shimmer_button.setText("Initialize Shimmer")
                self.initialize_shimmer_button.setStyleSheet(design.GREEN_BUTTON)

        elif button == 'start_streaming':
            time_3 = datetime.datetime.now().strftime('%H:%M')
            #self.handle_console_output(f'{time_3} - Button 3 was clicked')
            res = self.EmgUnit.start_shimmer()
            if res:
                self.handle_console_output(f'{datetime.datetime.now().strftime("%H:%M")} - Shimmer streaming started')
                self.shimmer_status_animation.stop()
                self.shimmer_status_animation = self.create_color_animation(self.shimmer_status, design.GREEN)
                self.start_block_graph_update()

            else:
                self.handle_console_output(f'{datetime.datetime.now().strftime("%H:%M")} - Shimmer streaming failed')
                self.shimmer_status_animation.stop()
                self.shimmer_status_animation = self.create_color_animation(self.shimmer_status, design.RED)
                
        elif button == 'stop_streaming':
            time_4 = datetime.datetime.now().strftime('%H:%M')
            #self.handle_console_output(f'{time_4} - Button 4 was clicked')
            self.EmgUnit.stop_shimmer()
            self.handle_console_output(f'{datetime.datetime.now().strftime("%H:%M")} - Shimmer streaming stopped')
            self.shimmer_status_animation.stop()
            self.shimmer_status_animation = self.create_color_animation(self.shimmer_status, design.YELLOW)
            if self.update_timer.isActive():
                self.stop_block_graph_update()
        
        elif button == 'send_velocity':
            time_5 = datetime.datetime.now().strftime('%H:%M')
            #self.handle_console_output(f'{time_5} - Button 5 was clicked')
            if self.connection_status:
                try:
                    velocity = int(self.findChild(QLineEdit, 'velocity_input').text())
                    self.sent_velocity = velocity
                    self.serial_comm.send(f"{velocity},1,0\n")
                    self.handle_console_output(f"{datetime.datetime.now().strftime('%H:%M')} - Sent velocity: {velocity}")
                except ValueError:
                    QMessageBox.warning(self, "Input Error", "Please enter a valid velocity.")

            # Clear the input field
            self.findChild(QLineEdit, 'velocity_input').clear()
        
        elif button == 'enable_motor':
            time_6 = datetime.datetime.now().strftime('%H:%M')
            #self.handle_console_output(f'{time_6} - Button 6 was clicked')
            self.toggle_motor_enable()
        
        elif button == 'stall_motor':
            time_7 = datetime.datetime.now().strftime('%H:%M')
            #self.handle_console_output(f'{time_7} - Button 7 was clicked')

        elif button == 'connect_serial':
            time_8 = datetime.datetime.now().strftime('%H:%M')
            #self.handle_console_output(f'{time_8} - Button 8 was clicked')
            self.toggle_connection()
        
        elif button == 'bind_output':
            time_9 = datetime.datetime.now().strftime('%H:%M')
            #self.handle_console_output(f'{time_9} - Button 9 was clicked')
            self.bind_output_start()

    def handle_console_output(self, output):
        # Shift the buffer to the left and add the new output at the end
        self.consolebuffer = np.roll(self.consolebuffer, -1)
        self.consolebuffer[-1] = output
        # Update the console output
        self.console_text.setText('\n'.join(filter(None, self.consolebuffer)))
        # Move the cursor to the end of the text
        self.console_text.moveCursor(QTextCursor.End)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
