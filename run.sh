#!/bin/bash

# Check if Python is installed
if ! command -v python &> /dev/null
then
    echo "Python is not installed. Please install Python and try again."
    exit 1
fi

# Install required libraries
echo "Checking and installing required libraries..."
pip install numpy pyqtgraph PyQt5 > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Failed to install required libraries. Please ensure pip is installed and try again."
    exit 1
fi

# Run the application
echo "Starting Application..."
python app.py
