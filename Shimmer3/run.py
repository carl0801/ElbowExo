import matplotlib.pyplot as plt
import numpy as np
import filter
import myMain
import time
import pandas as pd

# Load the data from the .npz file
data = np.load('RawMeasurements\BevægelseVertikaltExFlex.npz')['data']

# Extract the timestamps and the sensor data
timestamps = data[:, 0]
sensor1_data = data[:, 1]
sensor2_data = data[:, 2]
up = data[:, 3]
down = data[:, 4]

keyhandle = myMain.init()
if keyhandle is not None:
    print('Connected to EPOS4')
Filter = filter.generate_filter(fs=650)

time.sleep(4)

last_movement = 'rest'
def classify(sensor1, sensor2):
    global keyhandle, last_movement
    threshold = 4
    # Rolling variance
    
    window_size = 100
    variance1 = np.var(sensor1[-window_size:])
    variance2 = np.var(sensor2[-window_size:])
    diff = variance1 - variance2
    if diff > threshold:
        if last_movement != 'up':
            myMain.velocity_control(keyhandle, 1000)
            time.sleep(1)
            print('Moving up')
        last_movement = 'up'
        return 'up'
    elif diff < -threshold:
        if last_movement != 'down':
            myMain.velocity_control(keyhandle, -1000)
            time.sleep(1)
            print('Moving down')
        last_movement = 'down'
        return 'down'
    else:
        if last_movement != 'rest':
            myMain.velocity_control(keyhandle, 0)
            time.sleep(1)
            print('Resting')
        last_movement = 'rest'
        return 'rest'

# Loop through the data with a time delay defined by the timestamps
previous_timestamp = timestamps[0]
try:
    for i in range(1, len(timestamps)):
        current_timestamp = timestamps[i]
        time_delay = (current_timestamp - previous_timestamp) / 650  # Adjust time delay based on sampling frequency
        previous_timestamp = current_timestamp
        
        # Simulate real-time delay
        time.sleep(time_delay)
        
        # Process the data in batches of 100 samples
        if i >= 100:
            current_array = sensor1_data[i-100:i]
            filtered_array = filter.array_run(current_array, Filter)
            # Get rolling variance using pandas with a window size of 100
            variance = pd.Series(filtered_array).rolling(window=100).var()

            # Run classification based on rolling variance
            status = classify(sensor1_data[i-100:i], sensor2_data[i-100:i])
            
            #print(f"At timestamp {current_timestamp}: Status = {status}")
        else:
            current_array = sensor1_data[:i]
except KeyboardInterrupt:
    myMain.stop_motor(keyhandle)
    print('Motor stopped')
    