from gpiozero import Button
from signal import pause
import subprocess
import time
from status_led import StatusLed
import threading
from export_music import sync_music

# Define your main program function
led = StatusLed()
led.turn_off(update=False)
led.set_sesh_status('Stop')
led.update()
process = None
drive_to_mount = None

# Button press handler


def check_unmounted_partitions():
    global led, drive_to_mount, process
    try:

        if process is None:
            # Run lsblk and capture its output
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
    threading.Timer(3.0, check_unmounted_partitions).start()


def toggle_sesh():
    global running, process, led, drive_to_mount
    if not running:
        running = True
        led.set_sesh_status('Start')
        led.set_drive_status('Off')
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
    global running, process, led, drive_to_mount
    if running == False and process is None:
        if drive_to_mount is None:
            led.set_drive_status('Error', update=True)
            time.sleep(1)
            led.set_drive_status('Off', update=True)
            return
        else:
            sync_music(drive_to_mount, led)


check_unmounted_partitions()
# GPIO Pin for the button
sesh_button_pin = 5
sync_button_pin = 19

# Setup the button
sesh_button = Button(sesh_button_pin,  bounce_time=0.1)
sync_button = Button(sync_button_pin,  bounce_time=0.1)
# Assign the handler for button press event
sesh_button.when_pressed = toggle_sesh
sync_button.when_pressed = run_sync
# Flag to control the program execution
running = False


# Keep the script running
try:
    pause()
except KeyboardInterrupt:
    print("Exiting script")
