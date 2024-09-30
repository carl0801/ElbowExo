#!/bin/bash
set -e

# Setup ROS2 environment
source "/opt/ros/$ROS_DISTRO/setup.bash"

# Initialize micromamba
eval "$(micromamba shell hook --shell=bash)"

# Activate micromamba environment
micromamba activate myenv

# Execute the command passed to the container
exec "$@"