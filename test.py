import time
import numpy as np
import libraries.com as com

velocity = 0

jashda = com.SerialCommunication()
jashda.connect()


start_time = time.time()
reached_20 = False
# start by ramping up the velocity to 20 then ramp down to -20 then ramp up to 20 and always multiply with random noise between -2 and 2
while time.time() - start_time < 200:
    if velocity < 30 and not reached_20:
        velocity += 1
        # set flag
        if velocity == 30:
            reached_20 = True
    elif reached_20:
        velocity -= 1
        if velocity == -30:
            reached_20 = False

    print(f"Velocity: {velocity}")
    jashda.send(f"{velocity},1,0,0\n")
    time.sleep(0.1)

