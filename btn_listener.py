from gpiozero import Button
import redis
import threading
import os
import time
from functools import partial
from signal import pause
from structs.buttonevent import ButtonEvent

# Function to handle button press
def on_press(label, r, start_times):
    start_times[label] = time.time()
    button_event = ButtonEvent(button_name=label, event_type='down')
    r.publish('button', str(button_event))

# Function to handle button release
def on_release(label, r, start_times):
    duration = time.time() - start_times.get(label, 0)
    button_event = ButtonEvent(button_name=label, event_type='up', duration=duration)
    r.publish('button', str(button_event))
    if label in start_times:
        del start_times[label]

# Function to continuously check for shutdown condition
def check_shutdown_condition(start_times, stop_event):
    while not stop_event.is_set():
        time.sleep(0.2)
        if 'top' in start_times and 'bottom' in start_times:
            if time.time() - max(start_times.values()) > 3:
                print("Shutting down")
                os.system('sudo shutdown -h now')
                break

# Setup Redis client
r = redis.Redis(host='localhost', port=6379, db=0)

# GPIO Pin for the button
top_pin = 13
mid_pin = 12
bottom_pin = 6

# Setup the button
top_button = Button(top_pin, bounce_time=0.1)
mid_button = Button(mid_pin, bounce_time=0.1)
bottom_button = Button(bottom_pin, bounce_time=0.1)

# Dictionary to store start times of button presses
start_times = {}

stop_event = threading.Event()
# Thread for checking the shutdown condition
condition_check_thread = threading.Thread(target=check_shutdown_condition, args=(start_times, stop_event))
condition_check_thread.start()

# Assign the handler for button press and release events
top_button.when_pressed = partial(on_press, 'top', r, start_times)
top_button.when_released = partial(on_release, 'top', r, start_times)

mid_button.when_pressed = partial(on_press, 'mid', r, start_times)
mid_button.when_released = partial(on_release, 'mid', r, start_times)

bottom_button.when_pressed = partial(on_press, 'bottom', r, start_times)
bottom_button.when_released = partial(on_release, 'bottom', r, start_times)


# Keep the script running
try:
    pause()
except KeyboardInterrupt:
    print("Exiting script")

    stop_event.set()
    condition_check_thread.join()
    # Cleanup GPIO
    top_button.close()
    mid_button.close()
    bottom_button.close()
