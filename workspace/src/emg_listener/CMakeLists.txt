cmake_minimum_required(VERSION 3.5)
project(emg_listener)

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

# Create executable
add_executable(listener src/listener.cpp)

# Link libraries
ament_target_dependencies(listener rclcpp std_msgs)

# Install the executable
install(TARGETS
  listener
  DESTINATION lib/${PROJECT_NAME})

# Testing (optional)
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()