import audioop
import os
import shutil
import subprocess
import sys
import time
import uuid
import wave
from pydub import AudioSegment
from backend import MusicDatabase, RedisClient
from .metadata_tagger import MetadataTagger
from structs import SongData
from time_mgmt import (TimeSegment, amt_ms_to_rtp, amt_rtp_to_ms,
                       current_time_ms)
from config import (CHANNELS, LIB_FILETYPE, LIB_PATH, REC_BUFFER, REC_FILETYPE,
                    REC_FOLDER_RAW, REC_FOLDER_TRIM, REC_FORMAT, REC_NICE,
                    REC_OVERLAP, SAMPLE_RATE)

class RecordingProcess:
    def __init__(self, library_path=LIB_PATH, filetype=LIB_FILETYPE, stream_type='Realtime', buffer_len=REC_OVERLAP, led = None, db: MusicDatabase = None, redis:RedisClient=None):
        self.db = db if db is not None else MusicDatabase()
        self.redis = redis if redis is not None else RedisClient()
        self.library_path = library_path
        self.filetype = filetype
        self.stream_type = stream_type
        self.buffer_len_ms = buffer_len * 1000
        self.process = None
        self.rec_id = uuid.uuid4()
        print(f'id = {self.rec_id}')

        self.rec_filename = os.path.join(
            REC_FOLDER_RAW, f"{self.rec_id}.{REC_FILETYPE}")
        self.song_filepath = None
        self.song_data = SongData(self.rec_id, self.db)
        self.segments = [TimeSegment(self.stream_type)]
        self.rec_start_ms = None
        self.rec_end_ms = None

        self.song_start_rtp = None
        self.song_end_rtp = None
        self.rtp_type = None

        self.is_recording = False
        self.has_stopped = False
        self.has_saved = False
        self.device = 1
        self.data_strikes = 0

    def set_stream_type(self, st):
        self.stream_type = st
        for seg in self.segments:
            seg.stream_type = st

    def start_recording(self, use_alt=False):
        self.device = 3 if use_alt else 1
        print(f'REC START {self.rec_id} --- {self.device}')
        command = ['sudo',
                   'nice',
                   '-n', str(REC_NICE),
                   'arecord',
                   '-B', str(int(REC_BUFFER*1_000_000)),
                   '-D', f'hw:Loopback,0,{self.device}',
                   '-c', str(CHANNELS),
                   '-r', str(SAMPLE_RATE),
                   '-f', str(REC_FORMAT),
                   self.rec_filename
                   ]
        self.redis.set_rec_time_status(self.device, 'inactive')
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE)
        self.rec_start_ms = current_time_ms()
        self.is_recording = True

    def is_silent(self, threshold=1000):
        with wave.open(self.rec_filename, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            avg = audioop.rms(frames, wf.getsampwidth())  # Get average of RMS
            return avg < threshold

    def stop_recording(self):
        if self.has_stopped:
            print('already stopped')
            return

        print(f'REC STOP {self.rec_id}')
        if self.process and self.song_data.hex_id is not None:
            self.process.terminate()
            self.process.wait()
            self.rec_end_ms = current_time_ms()

            self.process = None
            self.is_recording = False
            self.has_stopped = True
        print('stop complete')
        self.redis.set_rec_time_status(self.device, 'default')

    def parse_bundle(self, bundle):
        result = self.song_data.eat_bundle(bundle)

        if self.song_data.db_state is not None:
            self.redis.set_rec_db_status(self.device, self.song_data.db_state)
            if (self.song_data.db_state == 'SAVED' or self.song_data.db_state == 'EXPORTED') and self.is_recording:
                self.stop_recording()
        if result == True:
            self.redis.set_current_song(self.song_data.to_dict())
        if result == False:
            self.data_strikes += 1
        if self.data_strikes >= 3:
            print('3rd "Not my data", Im gettin outta here')
            self.stop_recording()
            self.save_song()
            return False
        return result

    def ms_since_start(self):
        if self.song_start_rtp is None:
            start_ms = self.rec_start_ms+self.buffer_len_ms
        else:
            last_stamp = self.segments[-1].get_last()
            if last_stamp is None:
                print('no stamps')
                return sys.maxsize
            start_ms = last_stamp.py_ms - \
                amt_rtp_to_ms(last_stamp.rtp - self.song_start_rtp)

        return current_time_ms() - start_ms

    def parse_rtp(self, rtp, ms):
        is_good = self.segments[-1].add_stamp(rtp, ms)
        left = self.ms_left()
        print(f'{self.song_data.title} -- {int(left)}ms left')
        if self.song_data.length.value and left and left > 0:
            length = self.song_data.length.value
            progress = (self.ms_since_start()) / length
            self.redis.set_current_song_field('progress',progress)
        if not is_good:
            if left < 0 and left > -self.buffer_len_ms*2:
                print('new song rtp base, ignoring')
            else:
                print('new seg')
                self.segments.append(TimeSegment(self.stream_type))
                self.segments[-1].add_stamp(rtp, ms)
        if left < 0 and self.ms_since_start() > 10_000 and self.is_recording:
            self.redis.set_rec_time_status(self.device, 'done')


    def parse_progress(self, start, end):
        if (self.rtp_type is None or self.rtp_type == 'firstframe'):
            ms_left = self.ms_left()
            if ms_left < 0:
                self.song_end_rtp = start
                if self.song_data.length.value is not None:
                    self.song_start_rtp = self.song_end_rtp - \
                        amt_ms_to_rtp(self.song_data.length.value)
                print('hoping this is an approx ending ;)')
            # elif self.ms_length() < 2000:
            #     print(
            #         f'{self.song_data.title} -- ignoring prog, hasnt started (i hope)')
            #     # return
            self.song_start_rtp = start
            self.song_end_rtp = end
            self.rtp_type = 'prog'
            if self.is_recording:
                self.redis.set_rec_time_status(self.device, 'locked')
            print('setting prog rtp')
        elif self.rtp_type == 'prog':
            ms_change = amt_rtp_to_ms(abs(start - self.song_start_rtp))
            if ms_change < 1000:  # typically indicates an adjustment
                self.song_start_rtp = start
                self.song_end_rtp = end
                print('updating prog rtp')

    def parse_first_frame(self, rtp, ms):
        self.segments[-1].add_stamp(rtp, ms)
        print(f'{self.song_data.title} -- {int(self.ms_left())}ms left -- First Frame')

        if self.song_start_rtp is None:
            self.song_start_rtp = rtp
            self.rtp_type = 'firstframe'
            print('setting firstframe start rtp')
        if self.song_end_rtp is None and self.song_data.length.value is not None:
            self.song_end_rtp = rtp + \
                amt_ms_to_rtp(self.song_data.length.value)
            self.rtp_type = 'firstframe'
            print('setting firstframe end rtp')

    def trim_wav(self):
        if self.song_start_rtp is None:
            if self.song_data.length.value is not None:
                song_start_ms = max(self.rec_start_ms+(self.buffer_len_ms),
                                    self.rec_end_ms - (self.song_data.length.value+self.buffer_len_ms))
            else:
                song_start_ms = self.rec_start_ms+self.buffer_len_ms
        else:
            song_start_ms = self.predict_ms(self.song_start_rtp)
        if self.song_end_rtp is None:
            if self.song_data.length.value is not None:
                song_end_ms = min(
                    song_start_ms + self.song_data.length.value, self.rec_end_ms)
            else:
                song_end_ms = self.rec_end_ms

        else:
            song_end_ms = self.predict_ms(self.song_end_rtp)


        try:
            song_duration = (song_end_ms - song_start_ms)
            print(
                f'Measured Duration: {song_duration} -- Reported Duration: {self.song_data.length} -- Recording Duration: {self.rec_end_ms - self.rec_start_ms}')
            audio = AudioSegment.from_wav(self.rec_filename)
        except:
            print('RECORDING ERROR : ABORT')
            self.redis.set_rec_time_status(self.device, 'error')
            return None, 0

        if len(audio) < song_duration:
            print('RECORDING INCOMPLETE : ABORT')
            self.redis.set_rec_time_status(self.device, 'error')
            return None, 0

        rel_start = int(max(song_start_ms-self.rec_start_ms, 0))
        rel_duration = int(min(song_duration, len(audio)-rel_start))
        print(
            f'Audio Len = {len(audio)}, trim start: {rel_start}, trim end: {rel_start+rel_duration}')
        trimmed_audio = audio[rel_start:rel_start+rel_duration]
        # trimmed_audio = trim_silence(trimmed_audio)
        trimmed_filename = os.path.join(
            REC_FOLDER_TRIM, f"{self.rec_id}.{self.filetype}")
        trimmed_audio.export(trimmed_filename, format=self.filetype)
        self.delete_temp_files(trim=False)
        return trimmed_filename, rel_duration

    def should_start_next(self):
        return self.ms_left() < self.buffer_len_ms and self.ms_length() > 20_000

    def should_stop(self):
        min_len = self.song_data.length.value if self.song_data.length.value is not None else 20_000
        return self.ms_left() <= -1*self.buffer_len_ms and self.ms_length() > min_len

    def ms_left(self):
        if self.song_end_rtp is None:
            if self.song_start_rtp is not None and self.song_data.length.value is not None:
                self.song_end_rtp = self.song_start_rtp + \
                    amt_ms_to_rtp(self.song_data.length.value)
            elif self.song_data.length.value is not None:
                print('~~~approx~~~')
                return (self.rec_start_ms + self.song_data.length.value + self.buffer_len_ms) - current_time_ms()
            else:
                return sys.maxsize

        last_stamp = self.segments[-1].get_last()
        if last_stamp is None:
            return sys.maxsize

        end_ms = last_stamp.py_ms + \
            amt_rtp_to_ms(self.song_end_rtp - last_stamp.rtp)
        ms_left = end_ms - current_time_ms()
        return ms_left

    def ms_length(self):
        if self.rec_start_ms is None:
            return 0
        return int(current_time_ms()) - self.rec_start_ms

    def save_song(self):
        self.redis.set_rec_time_status(self.device, 'save')
        if self.has_saved:
            print('already saved')
            return
        if self.song_data.hex_id is None:
            return
        self.has_saved = True
        if self.song_data.artist.value is None or self.song_data.album.value is None or self.song_data.title.value is None:
            print(f"Metadata incomplete.")
            self.delete_temp_files()
            return
        target_dir = os.path.join(
            self.library_path, self.song_data.artist.value, self.song_data.album.value)
        self.song_filepath = os.path.join(
            target_dir, f"{self.song_data.title.value}.{self.filetype}")

        if os.path.exists(self.song_filepath):
            print(f"File {self.song_filepath} already exists.")
            self.delete_temp_files()
            return
        trimmed_path, duration = self.trim_wav()
        if trimmed_path is None:
            print(f"Recording not saved.")
            self.delete_temp_files()
            return
        if self.song_data.length.value is not None and self.song_data.length.value > 0:
            if duration < self.song_data.length.value * 0.9:
                print(f"Recording incomplete.")
                self.delete_temp_files()
                return
            else:
                if self.song_data.db_id is not None:
                    self.db.add_recording(self.song_data.db_id, duration)
                os.makedirs(target_dir, exist_ok=True)
                shutil.move(trimmed_path, self.song_filepath)
                # tag
                MetadataTagger.tag_file(self.song_filepath, self.song_data)
                print(f'{self.rec_id} -- saved and tagged')
                # self.redis.set_rec_time_status(self.device, 'default')
                self.redis.set_rec_db_status(self.device, 'SAVED')
                time.sleep(0.2)

    def delete_temp_files(self, raw=True, trim=True):
        if raw:
            for root, dirs, files in os.walk('./data/raw'):
                for file in files:
                    if str(self.rec_id) in file:
                        os.remove(os.path.join(root, file))
        if trim:
            for root, dirs, files in os.walk('./data/trim'):
                for file in files:
                    if str(self.rec_id) in file:
                        os.remove(os.path.join(root, file))

    def is_dead(self):
        return self.has_stopped and self.has_saved

    def predict_ms(self, rtp):
        nearest_segment = None
        nearest_distance = float('inf')

        for segment in self.segments:
            if len(segment.timestamps) > 1:
                end_rtp = segment.get_last().rtp
                if segment.start.rtp <= rtp <= end_rtp:
                    # Found the relevant segment
                    return self.interpolate_ms(segment, rtp)

                # Track the nearest segment for potential extrapolation
                start_distance = abs(segment.start.rtp - rtp)
                end_distance = abs(end_rtp - rtp)
                segment_distance = min(start_distance, end_distance)
                if segment_distance < nearest_distance:
                    nearest_distance = segment_distance
                    nearest_segment = segment

        # Extrapolate using the nearest segment
        if nearest_segment:
            return self.extrapolate_ms(nearest_segment, rtp)
        return None

    def extrapolate_ms(self, segment, rtp):
        # Assuming linear extrapolation
        # Using the first two or last two timestamps in the segment for extrapolation
        if rtp < segment.start.rtp:
            # Use the first two timestamps
            stamps = segment.timestamps[:2]
        else:
            # Use the last two timestamps
            stamps = segment.timestamps[-2:]

        rtp_range = stamps[1].rtp - stamps[0].rtp
        ms_range = stamps[1].py_ms - stamps[0].py_ms
        rtp_diff = rtp - stamps[0].rtp

        # Calculate the extrapolated ms
        return stamps[0].py_ms + (rtp_diff / rtp_range) * ms_range

    def interpolate_ms(self, segment, rtp):
        # Find two timestamps around the given rtp
        for i in range(len(segment.timestamps) - 1):
            if segment.timestamps[i].rtp <= rtp <= segment.timestamps[i + 1].rtp:
                # Linear interpolation
                start_stamp = segment.timestamps[i]
                end_stamp = segment.timestamps[i + 1]
                rtp_range = end_stamp.rtp - start_stamp.rtp
                ms_range = end_stamp.py_ms - start_stamp.py_ms
                rtp_diff = rtp - start_stamp.rtp

                # Calculate the interpolated ms
                return start_stamp.py_ms + (rtp_diff / rtp_range) * ms_range

        # Handle case where rtp is outside the range in the segment
        return None
