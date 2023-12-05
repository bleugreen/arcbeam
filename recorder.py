import sys
import signal
import shutil
import os
import subprocess
import time
from recording import RecordingProcess
from config import LIB_PATH, LIB_FILETYPE, REC_FOLDER_RAW, REC_FOLDER_TRIM
from time_mgmt import amt_ns_to_ms
from status_led import StatusLed
from db import MusicDatabase
import select
from devicedata import AirplayDevice
import redis


class AirplayRecorder:
    def __init__(self):
        self.device = AirplayDevice()
        self.db = MusicDatabase()
        self.led = StatusLed()
        self.recordings = []
        self.running = True
        self.alt_loop = False
        self.stream_type = 'Realtime'
        self.proc = None
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.redis_pubsub = redis.Redis(
            host='localhost', port=6379, db=0).pubsub()
        self.redis_pubsub.subscribe('crec')
        print(f'recording {LIB_FILETYPE} files to {LIB_PATH}')
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def clear_temp_files(self):
        for folder in [REC_FOLDER_RAW, REC_FOLDER_TRIM]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')

    def start_next_recording(self):
        self.recordings.append(RecordingProcess(
            LIB_PATH, LIB_FILETYPE, self.stream_type, led=self.led, db=self.db))
        self.recordings[-1].start_recording(self.alt_loop)
        self.alt_loop = not self.alt_loop

    def process_metadata_line(self, line):
        # Place the logic for processing each line of metadata here
        pass

    def main(self):
        self.clear_temp_files()
        self.led.set_sesh_status('Active')
        self.led.update()

        print('starting first recording')
        self.start_next_recording()

        while self.running:
            message = self.redis_pubsub.get_message()
            if message and message['type'] == 'message':
                line = message['data'].decode()
                self.process_metadata_line(line)
                self.manage_recordings()

            if not self.recordings:
                print('no recordings! starting one')
                self.start_next_recording()

            # To avoid busy waiting; adjust the sleep time as needed
            time.sleep(1)
            self.led.update()
            self.check_and_end_session()

        self.cleanup()

    def stop_all_recordings(self):
        # Logic to stop all recordings
        pass

    def manage_recordings(self):
        # Logic to manage the state of recordings
        pass

    def check_and_end_session(self):
        # Check if the session should end and clean up if needed
        pass

    def signal_handler(self, sig, frame):
        print('Shutting Down!')
        self.running = False
        self.cleanup()

    def cleanup(self):
        self.led.set_sesh_status('Stop')
        self.led.update()
        for rec in self.recordings:
            rec.stop_recording()
            rec.save_song()
            self.led.turn_off_rec(rec.device)
        self.led.update()
        self.recordings = []
        print('hitting exit')
        if self.proc is not None:
            self.proc.terminate()
            self.proc.wait()
        sys.exit(0)


if __name__ == '__main__':
    recorder = AirplayRecorder()
    recorder.main()
