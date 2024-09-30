#!/bin/bash
set -e

# setup ros2 environment
source "/opt/ros/$ROS_DISTRO/setup.bash" --


# Activate micromamba environment
source /usr/local/bin/micromamba shell activate myenv

# Execute the command passed to the container
exec "$@"