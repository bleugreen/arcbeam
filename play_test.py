import jack
import soundfile as sf
import numpy as np
import threading
import redis
import json
import os
import tempfile
import subprocess
import time
# Constants
client_name = "PyJackAudioPlayer"
redis_channel = 'player'
base_directory = '/home/dev/crec'  # Base directory for music files

# Initialize JACK client
max_channels = 2  # Set to the maximum number of channels you expect to handle

# Initialize JACK client
client = jack.Client(client_name)
outports = [client.outports.register(f"{client_name}_out_{i}") for i in range(max_channels)]
# Attempt to register new ports
target_ports = client.get_ports(is_physical=True, is_input=True, is_audio=True)
# Check if the number of target ports is sufficient
is_paused = False
current_position = 0

playback_finished = False
# Function to play audio file
def play_audio(file_path):
    global outports, playback_finished
    playback_finished = False

    with sf.SoundFile(file_path) as sf_file:
        data = sf_file.read(dtype='float32')
        channels = sf_file.channels

    @client.set_process_callback
    def process(frames):
        nonlocal data, channels
        global playback_finished, is_paused, current_position
        if playback_finished:
            return
        if is_paused:
            # Fill buffer with zeros (silence) when paused
            for port in outports:
                port.get_buffer()[:] = np.zeros(frames, dtype='float32')
            return
        if current_position + frames < len(data):
            frame_data = data[current_position:current_position + frames]
            current_position += frames
        else:
            frame_data = np.zeros((frames, channels), dtype='float32')
            playback_finished = True
            return

        for i, port in enumerate(outports):
            port_buffer = np.ascontiguousarray(frame_data[:, i])
            port.get_buffer()[:] = port_buffer

    client.activate()

    for i, port in enumerate(outports):
        try:
            client.connect(port, target_ports[i])
        except Exception as e:
            print(f"Error connecting {port} to {target_ports[i]}: {e}")
    print("Connected")
    while not playback_finished:
        time.sleep(0.1)
    print("Playback finished")
    client.deactivate()


# Redis subscriber
def redis_subscriber():
    global playback_finished, is_paused
    r = redis.Redis()
    pubsub = r.pubsub()
    pubsub.subscribe(redis_channel)
    player_thread = None
    print(f"Subscribed to {redis_channel}")
    for message in pubsub.listen():
        # print(message)
        if message['type'] == 'message':
            data = json.loads(message['data'].decode('utf-8'))
            print(data)
            if data.get('command') == 'play':
                artist = data.get('artist')
                album = data.get('album')
                title = data.get('title')

                # Construct file path and check for different file extensions
                for ext in ['flac', 'wav', 'mp3', 'ogg']:
                    file_path = os.path.join(base_directory, artist, album, f"{title}.{ext}")
                    print(f"Checking {file_path}")
                    if os.path.exists(file_path):
                        print(f"Found {file_path}")
                        if player_thread is not None:
                            playback_finished = True
                            player_thread.join()
                        playback_finished = False
                        player_thread = threading.Thread(target=play_audio, args=(file_path,))
                        player_thread.start()
                        break
            elif data.get('command') == 'pause':
                is_paused = True
            elif data.get('command') == 'resume':
                is_paused = False
            elif data.get('command') == 'stop':
                playback_finished = True
                player_thread.join()


# Keep the main thread alive
try:
    redis_subscriber()
except KeyboardInterrupt:
    client.deactivate()
    client.close()
