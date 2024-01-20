import jack
import soundfile as sf
import numpy as np
import threading
import time
import redis
import json
import os

class AudioPlayer:
    def __init__(self, client_name="PyJackAudioPlayer", max_channels=2, base_directory='/home/dev/crec'):
        self.client_name = client_name
        self.max_channels = max_channels
        self.base_directory = base_directory
        self.client = jack.Client(self.client_name)
        self.outports = [self.client.outports.register(f"{self.client_name}_out_{i}") for i in range(self.max_channels)]
        self.target_ports = self.client.get_ports(is_physical=True, is_input=True, is_audio=True)
        self.playback_finished = False
        self.is_paused = False
        self.current_position = 0
        self.data = None
        self.channels = None
        self.current_title = None
        self.current_artist = None
        self.current_album = None
        self.sample_rate = None
        self.playback_thread = None


        @self.client.set_process_callback
        def process(frames):
            self.process(frames)

    def play_audio(self, file_path):
        with sf.SoundFile(file_path) as sf_file:
            self.data = sf_file.read(dtype='float32')
            self.channels = sf_file.channels
            self.sample_rate = sf_file.samplerate

        self.playback_finished = False
        self.is_paused = False
        self.current_position = 0

        self.client.activate()

        for i, port in enumerate(self.outports):
            try:
                self.client.connect(port, self.target_ports[i])
            except Exception as e:
                print(f"Error connecting {port} to {self.target_ports[i]}: {e}")

        while not self.playback_finished:
            time.sleep(1)
            self.update_player_state()

        print("Playback finished")
        self.client.deactivate()

    def process(self, frames):
        if self.is_paused or self.playback_finished:
            for port in self.outports:
                port.get_buffer()[:] = np.zeros(frames, dtype='float32')
            return

        if self.current_position + frames < len(self.data):
            frame_data = self.data[self.current_position:self.current_position + frames]
            self.current_position += frames
        else:
            frame_data = np.zeros((frames, self.channels), dtype='float32')
            self.playback_finished = True
            return

        for i, port in enumerate(self.outports):
            port_buffer = np.ascontiguousarray(frame_data[:, i])
            port.get_buffer()[:] = port_buffer

    def pause(self):
        self.is_paused = True
        self.update_player_state()

    def resume(self):
        self.is_paused = False
        self.update_player_state()

    def stop(self):
        self.playback_finished = True
        if self.playback_thread is not None:
            self.playback_thread.join()
        self.update_player_state()

    def run(self, channel='player'):
        self.redis_channel = channel
        self.redis_client = redis.Redis()
        self.pubsub = self.redis_client.pubsub()
        self.pubsub.subscribe(self.redis_channel)
        self.subscriber_thread = threading.Thread(target=self.listen_to_redis)
        self.subscriber_thread.start()


    def listen_to_redis(self):
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'].decode('utf-8'))
                self.handle_redis_command(data)

    def handle_redis_command(self, data):
        command = data.get('command')
        if command == 'play':
            file_path = self.construct_file_path(data)
            if file_path:
                # Stop current playback if any
                self.stop()
                # Start playback in a new thread
                self.playback_thread = threading.Thread(target=self.play_audio, args=(file_path,))
                self.playback_thread.start()
        elif command == 'pause':
            self.pause()
        elif command == 'resume':
            self.resume()
        elif command == 'stop':
            self.stop()

    def construct_file_path(self, data):
        artist = data.get('artist')
        album = data.get('album')
        title = data.get('title')
        for ext in ['flac', 'wav', 'mp3', 'ogg']:
            file_path = os.path.join(self.base_directory, artist, album, f"{title}.{ext}")
            if os.path.exists(file_path):
                self.current_title = title
                self.current_artist = artist
                self.current_album = album
                self.update_player_state()
                return file_path
        return None

    def update_player_state(self):
        state = {
            "title": str(self.current_title),
            "artist": str(self.current_artist),
            "album": str(self.current_album),
            "time_elapsed": str(self.get_time_elapsed()),
            "length": str(self.get_track_length()),
            "is_paused": str(self.is_paused)
        }
        self.redis_client.hset("player_state", mapping=state)

    def get_time_elapsed(self):
        # Calculate and return the time elapsed in seconds
        # Note: This depends on how you're tracking playback time
        return self.current_position / self.client.samplerate

    def get_track_length(self):
        # Calculate and return the total track length in seconds
        # Note: This depends on the total number of frames and sample rate
        if self.data is not None:
            return len(self.data) / self.client.samplerate
        return 0

# Example Usage
if __name__ == "__main__":
    player = AudioPlayer()
    player.run()