#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to kill a process by name and wait until it's done
kill_process() {
    local name=$1

    # First, try finding the process using pgrep
    local pid=$(pgrep -fx "$name")

    # If pgrep didn't find the process, use ps and grep
    if [ -z "$pid" ]; then
        pid=$(ps -ef | grep "$name" | grep -v grep | awk '{print $2}')
    fi

    if [ ! -z "$pid" ]; then
        echo "Killing $name with PID $pid"
        kill "$pid"
        while kill -0 "$pid" > /dev/null 2>&1; do
            sleep 1
        done
        # Wait an additional second after the process has been killed
        sleep 1
    else
        echo "$name is not running."
    fi
}


read_config_value() {
    local key=$1
    yq ".audio.$key" $DIR/config.yaml | sed 's/"//g'
}


# Kill existing jackd and shairport-sync processes
kill_process "main.py"
kill_process "recorder.py"
kill_process "monitor.py"
kill_process "shairport-sync"
kill_process "alsa_out"
kill_process "alsa_out"
kill_process "arecord"
kill_process "jackd"


# Read configuration values
DEVICE=$(read_config_value "device")
SAMPLERATE=$(read_config_value "samplerate")
CHANNELS=$(read_config_value "channels")
PERIOD=$(read_config_value "period")

echo "Device: $DEVICE"
echo "Samplerate: $SAMPLERATE"
echo "Channels: $CHANNELS"
echo "Period: $PERIOD"

# Start JACK
jackd -d alsa -r "$SAMPLERATE" -p "$PERIOD" -n "$CHANNELS" -d "$DEVICE" &
sleep 1

# Start applications

alsa_out -d hw:Loopback,1,1 -j "Loopback1" &
alsa_out -d hw:Loopback,1,3 -j "Loopback3" &
alsa_out -d hw:Loopback,1,5 -j "Loopback5" &
shairport-sync &
sleep 1

# Set up connections
jack_connect shairport-sync:out_L system:playback_1
jack_connect shairport-sync:out_R system:playback_2

jack_connect shairport-sync:out_L Loopback1:playback_1
jack_connect shairport-sync:out_R Loopback1:playback_2

jack_connect shairport-sync:out_L Loopback3:playback_1
jack_connect shairport-sync:out_R Loopback3:playback_2

jack_connect shairport-sync:out_L Loopback5:playback_1
jack_connect shairport-sync:out_R Loopback5:playback_2

echo "JACK session set up complete. Starting Listener"

/home/dev/env/bin/python /home/dev/cymatic-rec/monitor.py &
/home/dev/env/bin/python /home/dev/cymatic-rec/main.py
