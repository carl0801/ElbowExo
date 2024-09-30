cmake_minimum_required(VERSION 3.5)
project(emg_sensor)

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)

# Add executable
add_executable(sensor src/sensor.cpp)

# Link dependencies
ament_target_dependencies(sensor rclcpp)

# Install executable
install(TARGETS
  sensor
  DESTINATION lib/${PROJECT_NAME})

# Ament package
ament_package()