from gpiozero import Button


from signal import pause
import subprocess
import time
from status_led import StatusLed
import threading
from export_music import sync_music


green_pin = 20
yellow_pin = 19
red_pin = 26
blue_pin = 16


def on_green_press():
    print('green press')


def on_blue_press():
    print('blue press')


def on_yellow_press():
    print('yellow press')


def on_red_press():
    print('red press')


    # Setup the button
# sesh_button = Button(blue_pin,  bounce_time=0.1)
green_button = Button(green_pin,  bounce_time=0.1)
blue_button = Button(blue_pin,  bounce_time=0.1)
yellow_button = Button(yellow_pin,  bounce_time=0.1)
red_button = Button(red_pin,  bounce_time=0.1)
# Assign the handler for button press event
green_button.when_pressed = on_green_press
blue_button.when_pressed = on_blue_press
yellow_button.when_pressed = on_yellow_press
red_button.when_pressed = on_red_press
# Flag to control the program execution
running = False


# Keep the script running
try:
    pause()
except KeyboardInterrupt:
    print("Exiting script")
