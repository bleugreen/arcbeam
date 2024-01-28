import jack
import soundfile as sf
import numpy as np
import threading
import time
import logging
import json
import os
from signal import pause

from backend import RedisClient
from config import LIB_PATH
from songqueue import SongQueue

logging.basicConfig(level=logging.INFO)

class AudioPlayer:
    def __init__(self, client_name="ArcbeamPlayer", max_channels=2, base_directory=LIB_PATH):
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
        self.queue = SongQueue(self.base_directory)


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
        start_time = time.time()
        while not self.playback_finished:
            time.sleep(0.1)
            current_time = time.time()
            elapsed_time = current_time - start_time

            if int(elapsed_time) % 2 == 0:
                self.update_player_state()

        print("Playback finished")
        self.client.deactivate()
        self.play_next_in_queue()

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

    def run(self, channel='player'):
        self.redis_channel = channel
        self.redis_client = RedisClient()
        self.pubsub = self.redis_client.redis.pubsub()
        self.pubsub.subscribe(self.redis_channel)
        self.subscriber_thread = threading.Thread(target=self.listen_to_redis)
        self.subscriber_thread.start()

    def play_next_in_queue(self):
        next_song = self.queue.get_next_song()
        if next_song:
            self.queue.set_current_song(next_song)
            path_parts = next_song.split(os.sep)
            self.current_artist = path_parts[-3]
            self.current_album = path_parts[-2]
            self.current_title = path_parts[-1].rsplit('.', 1)[0]
            self.redis_client.set_browse('artist', self.current_artist)
            self.redis_client.set_browse('album', self.current_album)
            self.redis_client.set_browse('track', self.current_title)
            self.playback_finished = False
            self.current_position = 0
            self.is_paused = False
            self.update_player_state()
            self.play_audio(next_song)


    def listen_to_redis(self):
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                self.handle_redis_command(data)

    def handle_redis_command(self, data):
        command = data.get('command')
        if command == 'play':
            file_path = self.construct_file_path(data)
            if file_path:
                # Stop current playback if any
                if self.playback_thread is not None:
                    self.stop()

                self.queue.set_current_song(file_path)
                self.playback_thread = threading.Thread(target=self.play_audio, args=(file_path,))
                self.playback_thread.start()
        elif command == 'pause':
            self.pause()
        elif command == 'resume':
            self.resume()
        elif command == 'stop':
            self.stop()
        elif command == 'next':
            self.playback_finished = True

    def construct_file_path(self, data):
        artist = data.get('artist')
        album = data.get('album')
        title = data.get('title')
        print(f"PLAYER GOT = Artist: {artist}, Album: {album}, Title: {title}")
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
        progress = 0 if not self.get_track_length() else self.get_time_elapsed() / self.get_track_length()
        state = {
            "title": str(self.current_title),
            "artist": str(self.current_artist),
            "album": str(self.current_album),
            "time_elapsed": str(self.get_time_elapsed()),
            "length": str(self.get_track_length()),
            "is_paused": str(self.is_paused),
            "progress": progress
        }
        self.redis_client.set_current_song(state, page='player')

    def get_time_elapsed(self):
        return self.current_position / self.client.samplerate

    def get_track_length(self):
        if self.data is not None:
            return len(self.data) / self.client.samplerate
        return 0

    def stop(self):
        self.playback_finished = True
        self.is_paused = False
        self.current_position = 0
        if self.playback_thread is not None:
            self.playback_thread.join(timeout=10)
            if self.playback_thread.is_alive():
                logging.warning("Playback thread did not terminate.")
            self.playback_thread = None

        self.update_player_state()

    def deactivate_client(self):
        try:
            self.client.deactivate()
            logging.info("JACK client deactivated.")
        except Exception as e:
            logging.error(f"Error deactivating JACK client: {e}")

    def cleanup(self):
        logging.info("Cleaning up player resources")
        self.stop()
        self.deactivate_client()
        try:
            self.client.close()
            logging.info("JACK client closed.")
        except Exception as e:
            logging.error(f"Error closing JACK client: {e}")

if __name__ == "__main__":
    player = AudioPlayer()
    try:
        player.run()
        pause()
    except Exception as e:
        logging.error(f"Error in player: {e}")
    finally:
        player.cleanup()