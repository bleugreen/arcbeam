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
from redis_client import RedisClient
from util import clear_temp_files
import json


class AirplayRecorder:
    def __init__(self):
        self.device = AirplayDevice()
        self.db = MusicDatabase()
        self.led = StatusLed()
        self.recordings: list[RecordingProcess] = []
        self.running = True
        self.alt_loop = False
        self.stream_type = 'Realtime'
        self.redis_client = RedisClient()

        self.redis_pubsub = redis.Redis(
            host='localhost', port=6379, db=0).pubsub()
        self.redis_pubsub.subscribe('crec')
        print(f'recording {LIB_FILETYPE} files to {LIB_PATH}')
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def update_redis_status(self, update=False):
        self.conn = self.redis_client.get_device_addr() != 'none'
        self.active = self.redis_client.is_active()
        self.playing = self.redis_client.is_playing()
        if self.active or self.playing:
            self.led.set_sesh_status('Good', update)
        elif self.conn:
            self.led.set_sesh_status('Done', update)
        elif self.running:
            self.led.set_sesh_status('Start', update)
        else:
            self.led.set_sesh_status('Stop', update)
        return self.running and self.conn

    def start_next_recording(self):
        rec = RecordingProcess(LIB_PATH, LIB_FILETYPE,
                               self.stream_type, led=self.led, db=self.db)
        rec.start_recording(self.alt_loop)
        self.recordings.append(rec)
        self.alt_loop = not self.alt_loop

    def stop_all_recordings(self, reason=None):
        for idx, rec in enumerate(self.recordings):
            print(rec.song_data.title,
                  f'stopping: {reason}')
            self.stop_recording(idx)

    def process_metadata(self, data: dict):
        datatype = data.get('type', None)
        if datatype == 'frame':
            for recording in self.recordings:
                recording.parse_rtp(data['rtp'], data['ms'])
        elif datatype == 'progress':
            for recording in self.recordings:
                recording.parse_progress(data['start'], data['end'])
        elif datatype == 'bundle':
            for recording in self.recordings:
                success = recording.parse_bundle(data)
                if not success and len(self.recordings) == 1:
                    # there's a new song and we need a new recording
                    print('foreign data! starting new')
                    self.start_next_recording()
                    self.recordings[-1].parse_bundle(data)
                if data.get('Persistent ID') == recording.song_data.hex_id.value:
                    break
        elif datatype == 'streamtype':
            st = data['value']
            if st != self.stream_type:
                print(f'Stream type == {st}')
                for rec in self.recordings:
                    rec.set_stream_type(st)
                self.stream_type = st
        elif datatype == 'active':
            self.active = data['value']
            if data['value']:
                if len(self.recordings) == 0:
                    self.start_next_recording()
            else:
                self.stop_all_recordings('exit active state')
        elif datatype == 'playing':
            self.playing = data['value']
            if data['value']:
                if len(self.recordings) == 0:
                    self.start_next_recording()
            else:
                self.stop_all_recordings('play session end')
        elif datatype == 'conn':
            self.conn = data['value']
            if data['value']:
                if len(self.recordings) == 0:
                    self.start_next_recording()
            else:
                self.stop_all_recordings('disconnected')
        elif datatype == 'control':
            if data['cmd'] == 'Pause':
                print(self.recordings[0].song_data.title,
                      'stopping: pause')
                self.stop_recording(0)
                if len(self.recordings) == 0:
                    print('paused and no recordings, starting new')
                    self.start_next_recording()
        else:
            print(f'UNKNOWN DATATYPE: {data}')

    def print_metadata(self, data):
        print('-----'*10)
        if list(data.keys()) == ['type', 'value']:
            t = data['type']
            val = data['value']
            print(f'{t:>10.10} = {val}')
        else:
            for key in data.keys():
                print(f'{key:>10.10} = {data[key]}')

    def main(self):
        clear_temp_files()
        ready = False
        while not ready:
            time.sleep(0.5)
            ready = self.update_redis_status()

        print('starting first recording')
        self.start_next_recording()

        self.in_bundle = False
        self.bundle = {}

        while self.running:
            message = self.redis_pubsub.get_message(timeout=2)
            if message and message['type'] == 'message':
                data = json.loads(message['data'].decode())
                self.print_metadata(data)
                self.process_metadata(data)
                self.manage_recordings()

            if not self.recordings:
                print('no recordings! starting one')
                self.start_next_recording()

            # To avoid busy waiting; adjust the sleep time as needed
            self.update_redis_status(update=False)
            self.led.update()

        self.cleanup()

    def stop_recording(self, idx):
        self.recordings[idx].stop_recording()
        self.recordings[idx].save_song()
        self.led.turn_off_rec(self.recordings[idx].device)
        self.recordings.remove(self.recordings[idx])

    def stop_start_save(self, idx):
        self.recordings[idx].stop_recording()
        if len(self.recordings) == 1:
            print(
                f'{idx} should stop and theres no one else, starting next')
            self.start_next_recording()
        self.recordings[idx].save_song()
        self.led.turn_off_rec(self.recordings[idx].device)
        self.recordings.remove(self.recordings[idx])

    def manage_recordings(self):
        if len(self.recordings) > 0:
            if self.recordings[0].should_start_next() and len(self.recordings) == 1:
                print(
                    'only one rec and should_start_next, starting next')
                self.start_next_recording()
            elif self.recordings[0].should_stop():
                print(self.recordings[0].song_data.title,
                      'stopping: should_stop')
                self.stop_start_save(0)

        for rec in self.recordings:
            if rec.is_dead():
                self.led.turn_off_rec(rec.device)
                self.recordings.remove(rec)
        if self.running and len(self.recordings) == 0:
            print('no recordings! (end) starting next')
            self.start_next_recording()

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
        sys.exit(0)


if __name__ == '__main__':
    recorder = AirplayRecorder()
    recorder.main()
