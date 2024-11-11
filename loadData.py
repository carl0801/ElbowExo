import pickle
import glob
import os
import numpy as np

def load(n=0):
    # Find files with the highest number
    files = glob.glob('data/[0-9.]*-shimmer.pkl') + glob.glob('data/[0-9.]*-loadcell.pkl')
    files.sort(key=lambda x: list(map(float, os.path.splitext(os.path.basename(x))[0].split('-')[0].split('.'))), reverse=True)
    # The nth latest reading
    data1 = pickle.load(open(files[n*2], 'rb'))
    data2 = pickle.load(open(files[n*2+1], 'rb'))
    if len(data1[0]) > len(data2[0]):
        shimmerData = data1
        loadcellData = data2
    else:
        shimmerData = data2
        loadcellData = data1
    shimmerData = np.array(shimmerData)
    loadcellData = np.array(loadcellData, dtype=float)

    # Shimmer data is stored in an array where each entry contain (time, sensor1, sensor2)
    # Loadcell data is stored in an array where each entry contain (time, sensor)
    # Shimmer time is in seconds, and loadcell is in miliseconds, but the clock they oprate after is not the same
    # They start at different times, but the readings end at the same time, so that is how they should be calibrate

    loadcellData[:, 0] = loadcellData[:, 0] / 1000

    # Get the time of the last data point
    last_time_shimmer = shimmerData[-1][0]
    last_time_loadcell = loadcellData[-1][0]

    # The time difference is the difference between the last time of the two systems
    time_diff = last_time_loadcell - last_time_shimmer

    # Calibrate the time of the loadcell
    loadcellData[:, 0] = loadcellData[:, 0] - time_diff

    # Make sure shimmer data is a signed int and there is no overflow
    shimmerData[:, 1] = np.int16(shimmerData[:, 1])
    shimmerData[:, 2] = np.int16(shimmerData[:, 2])

    return shimmerData, loadcellData

def loadShimmer(n=0):
    # Find files with the highest number
    files = glob.glob('data/[0-9.]*-shimmer.pkl')
    files.sort(key=lambda x: list(map(float, os.path.splitext(os.path.basename(x))[0].split('-')[0].split('.'))), reverse=True)
    # The nth latest reading
    shimmerData = pickle.load(open(files[n], 'rb'))
    shimmerData = np.array(shimmerData)

    # Make sure shimmer data is a signed int and there is no overflow
    shimmerData[:, 1] = np.int16(shimmerData[:, 1])
    shimmerData[:, 2] = np.int16(shimmerData[:, 2])

    return shimmerData
