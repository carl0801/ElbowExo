# emg_launch.py
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='emg_listener',
            executable='listener',  # Make sure this matches the executable defined in CMakeLists.txt
            name='listener',
            output='screen',
        ),
        Node(
            package='emg_sensor',
            executable='sensor',  # Make sure this matches the executable defined in CMakeLists.txt
            name='sensor',
            output='screen',
        ),
    ])