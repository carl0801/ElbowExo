import time

import libraries.com as com

velocity = 20

jashda = com.SerialCommunication()
jashda.connect()

direction = 1
start_time = time.time()

while True:
    current_time = time.time()
    direction = -1
    """ if current_time - start_time >=7.0:
        direction *= -1
        start_time = current_time """
    velocity = direction * abs(velocity)
    # Add your code to use the velocity variable here
    jashda.send(f"{velocity},1,0,0\n")
    #jashda.port.reset_output_buffer()
    #jashda.port.reset_input_buffer()
    #jashda.port.flush()
    print(f"Sent: {velocity}")
    #time.sleep(0.5)  # Small sleep to prevent high CPU usage
    velocity -= 10
    time.sleep(2)  # Small sleep to prevent high CPU usage

