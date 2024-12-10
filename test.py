import time
import numpy as np
import libraries.com as com

velocity = 0

jashda = com.SerialCommunication()
jashda.connect()


start_time = time.time()

# make a control output simulated as a sinusoidal signal with a frequency of 0.1 Hz and amplitude of 15

#jashda.send("-20,1,0,0\n")

while True:
    velocity -=2 #int(15 * (1 + np.sin(0.1 * 2 * np.pi * (time.time() - start_time))))-10
    jashda.send(f"{velocity},1,0,0\n")
    print(f"Velocity: {velocity}")
    time.sleep(0.1)

