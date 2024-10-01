#!/bin/bash
set -e

# setup ros2 environment
source "/opt/ros/$ROS_DISTRO/setup.bash" --

# Initialize micromamba
eval "$(micromamba shell hook --shell=bash)"

# Build things here
cd /workspace/rustTest
cargo build --release

# Go into the workspace
cd /workspace

# Execute the command passed to the container
exec "$@"