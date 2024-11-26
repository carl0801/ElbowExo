@echo off

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python and try again.
    exit /b
)

REM Install required libraries
echo Checking and installing required libraries...
pip install numpy pyqtgraph PyQt5 >nul 2>&1
if %errorlevel% neq 0 (
    echo Failed to install required libraries. Please ensure pip is installed and try again.
    exit /b
)

REM Run the app
echo Starting Application...
python app.py
exit
