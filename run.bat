@echo off

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python and try again.
    exit /b
)

REM Install required libraries
echo Checking and installing required libraries...

REM Check if numpy is installed
pip show numpy >nul 2>&1
if %errorlevel% neq 0 (
    echo numpy is not installed. Installing numpy...
    pip install numpy >nul 2>&1
) else (
    echo numpy is already installed.
)

REM Check if pyqtgraph is installed
pip show pyqtgraph >nul 2>&1
if %errorlevel% neq 0 (
    echo pyqtgraph is not installed. Installing pyqtgraph...
    pip install pyqtgraph >nul 2>&1
) else (
    echo pyqtgraph is already installed.
)

REM Check if PyQt5 is installed
pip show PyQt5 >nul 2>&1
if %errorlevel% neq 0 (
    echo PyQt5 is not installed. Installing PyQt5...
    pip install PyQt5 >nul 2>&1
) else (
    echo PyQt5 is already installed.
)

REM Check if the necessary libraries are installed
pip show numpy pyqtgraph PyQt5 >nul 2>&1
if %errorlevel% neq 0 (
    echo Failed to install required libraries. Please try again.
    exit /b
)

REM Run the app
echo Starting Application...
python app.py
exit
