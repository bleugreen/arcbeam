from gpiozero import Button
from signal import pause
import subprocess
import time
from status_led import StatusLed
import threading
from transfer.export_music import sync_music
from backend.redis_client import RedisClient
from datetime import datetime
from config import LIB_PATH, REC_NICE, REC_BUFFER, CHANNELS, SAMPLE_RATE, REC_FORMAT
import os
# re-initialize saved status
r = RedisClient()
r.reset()
del r

led = StatusLed()
led.turn_off(update=False)
led.set_sesh_status('Stop')
led.update()
process = None
drive_to_mount = None

clip_process = None
clip_toggle = False
red_held = False
green_held = False


def check_unmounted_partitions():
    global led, drive_to_mount, process
    try:
        # List connected drives
        result = subprocess.run(
            ['lsblk', '-o', 'MOUNTPOINT,NAME,SIZE'], capture_output=True, text=True)
        lines = result.stdout.splitlines()
        # Check each line for unmounted partitions
        unmounteds = []
        for line in lines[1:]:  # Skip the header line
            parts = line.split()
            # Only NAME is present, MOUNTPOINT is missing
            if len(parts) == 2 and 'mmcblk0' not in parts[0] and '─' in parts[0]:
                size = None
                if 'M' in parts[1]:
                    size = float(parts[1][:-1])
                elif 'G' in parts[1]:
                    size = float(parts[1][:-1])*1000
                elif 'T' in parts[1]:
                    size = float(parts[1][:-1])*1000000
                if size > 1000:
                    unmounteds.append({'name': parts[0][2:], 'size': size})

        if not unmounteds:
            led.set_drive_status('Off', update=True)
            drive_to_mount = None
        else:
            largest_unmounted = max(unmounteds, key=lambda x: x['size'])
            led.set_drive_status('Start', update=True)
            drive_to_mount = f"/dev/{largest_unmounted['name']}"

    except Exception as e:
        print(f"An error occurred: {e}")

    # run on a 5 second timer
    threading.Timer(5.0, check_unmounted_partitions).start()


def toggle_sesh():
    global running, process, led, drive_to_mount, red_held, clip_toggle
    if red_held:
        clip_toggle = True
        return
    if not running:
        running = True
        led.set_sesh_status('Start')
        led.update()
        time.sleep(0.1)
        print("Starting program")
        command = ['/home/dev/env/bin/python',
                   '/home/dev/cymatic-rec/main.py']
        process = subprocess.Popen(command)

    else:
        # set_sesh_status('Stopping')
        running = False
        process.terminate()
        process.wait()
        process = None
        print("Stopping program")
        led.turn_off(update=False)
        led.set_sesh_status('Stop', update=True)


def run_sync():
    global running, process, led, drive_to_mount, red_held, green_held
    green_held = False
    if running == False and process is None:
        if drive_to_mount is None:
            led.set_drive_status('Error', update=True)
            time.sleep(1)
            led.set_drive_status('Off', update=True)
            return
        else:
            sync_music(drive_to_mount, delete=red_held)


def stop_clip():
    global led, clip_process, clip_toggle
    clip_toggle = False
    led.set_clip_status('Stop', True)
    clip_process.terminate()
    clip_process.wait()
    clip_process = None
    led.set_clip_status('Off', True)


def toggle_disabled():
    global led
    led.toggle_disabled()


def on_clip_start():
    global led, clip_process, clip_toggle, red_held, green_held
    red_held = True
    if green_held:
        return
    if clip_toggle and clip_process is not None:
        stop_clip()
    else:
        led.set_clip_status('Error', True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filepath = os.path.join(LIB_PATH, '_clip', f'{timestamp}.wav')
        command = ['sudo',
                   'nice',
                   '-n', str(REC_NICE),
                   'arecord',
                   '-B', str(int(REC_BUFFER*1_000_000)),
                   '-D', f'hw:Loopback,0,5',
                   '-c', str(CHANNELS),
                   '-r', str(SAMPLE_RATE),
                   '-f', str(REC_FORMAT),
                   filepath
                   ]
        clip_process = subprocess.Popen(command, stdout=subprocess.PIPE)


def on_clip_release():
    global clip_process, clip_toggle, red_held
    red_held = False
    if not clip_toggle and clip_process is not None:
        stop_clip()


def on_green_press():
    global green_held
    green_held = True


check_unmounted_partitions()
# GPIO Pin for the button
green_pin = 20
yellow_pin = 19
red_pin = 26
blue_pin = 16
# Setup the button
blue_button = Button(blue_pin,  bounce_time=0.1)
green_button = Button(green_pin,  bounce_time=0.1)
red_button = Button(red_pin,  bounce_time=0.1)
yellow_button = Button(yellow_pin,  bounce_time=0.1)
# Assign the handler for button press event
blue_button.when_pressed = toggle_sesh
green_button.when_pressed = on_green_press
green_button.when_released = run_sync
yellow_button.when_pressed = toggle_disabled
red_button.when_pressed = on_clip_start
red_button.when_released = on_clip_release
# Flag to control the program execution
running = False


# Keep the script running
try:
    pause()
except KeyboardInterrupt:
    print("Exiting script")

    # Cleanup GPIO
    blue_button.close()
    green_button.close()
    yellow_button.close()
    red_button.close()

    # Cleanup the process
    if process is not None:
        process.terminate()
        process.wait()

    if clip_process is not None:
        clip_process.terminate()
        clip_process.wait()

    # Turn off the LED
    led.turn_off()

    # Exit the script
    exit(0)
