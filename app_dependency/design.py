from PyQt5.QtGui import QColor
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtWidgets import  QGraphicsColorizeEffect
import glob

# UI file path
UI_FILE_PATH = 'app_dependency/mainwindow.ui'

# Widget names
CULLOMS = ['menu_widget', 'console_widget', 'statusBar_widget']
TITLES = ['control_shimmer_title', 'muscle_movement_title', 'control_motor_title', 'animation_title']

# Images for exo-skeleton animation
EXO_IMAGES = sorted(glob.glob("app_dependency/frames/*.png"))

# Color for aaplication
RED = QColor("#F44336")
DARKER_RED = QColor("#D32F2F") 
GREEN = QColor("#4CAF50")
DARKER_GREEN = QColor("#388E3C")
YELLOW = QColor("#FFEB3B")
DARKER_YELLOW = QColor("#FBC02D")
BLUE = QColor("#007BFF")
DARKER_BLUE = QColor("#0056B3")

#Background color
BACKGROUND_COLOR = QColor("#f4f4f4")

# Button Styles
GREEN_BUTTON = """
                                    QPushButton {
                                        background-color: #4CAF50;  /* Original green background */
                                        border: none;
                                        color: white;
                                        padding: 10px 20px;
                                        text-align: center;
                                        text-decoration: none;
                                        font-size: 16px;
                                        font-weight: normal;
                                        border-radius: 8px;
                                    }
                                    QPushButton:hover {
                                        background-color: #45a049;  /* Original hover green */
                                    }
                                    QPushButton:pressed {
                                        background-color: #3e8e41;  /* Original pressed green */
                                    }"""
BLUE_BUTTON = """                                            QPushButton {
                                                background-color: #007BFF; /* Default Button Background */
                                                border: none;
                                                color: white;
                                                padding: 10px 20px;
                                                text-align: center;
                                                text-decoration: none;
                                                font-size: 16px;
                                                font-weight: normal;
                                                border-radius: 8px;
                                            }
                                            QPushButton:hover {
                                                background-color: #0069D9; /* Hover State */
                                            }
                                            QPushButton:pressed {
                                                background-color: #0056B3; /* Clicked State */
                                            }"""
RED_BUTTON = """
                                        QPushButton {
                                            background-color: #F44336;  /* Red background */
                                            border: none;
                                            color: white;
                                            padding: 10px 20px;
                                            text-align: center;
                                            text-decoration: none;
                                            font-size: 16px;
                                            font-weight: normal;
                                            border-radius: 8px;
                                        }
                                        QPushButton:hover {
                                            background-color: #E53935;  /* Darker red on hover */
                                        }
                                        QPushButton:pressed {
                                            background-color: #D32F2F;  /* Even darker red when pressed */
                                        }"""

# Animation
def color_animation(widget, color):
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
    if color == RED:
        animation.setEndValue(DARKER_RED)  # Darker red
    elif color == GREEN:
        animation.setEndValue(DARKER_GREEN)  # Darker green
    elif color == YELLOW:
        animation.setEndValue(DARKER_YELLOW)  # Darker yellow
    
    # Set the keyframes to alternate back and forth
    animation.setKeyValueAt(0.5, animation.endValue())  # Midway through, switch to the end color
    animation.setKeyValueAt(1.0, color)  # At the end, switch back to the start color
    
    # Loop indefinitely
    animation.setLoopCount(-1)  # Infinite loop
    
    # Apply easing curve for smooth animation
    animation.setEasingCurve(QEasingCurve.InOutQuad)
    
    return animation

def shake_animation(button, amplitude=10, duration=200):
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

