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
device = AirplayDevice()
db = MusicDatabase()
led = StatusLed()
recordings = []
running = True
alt_loop = False
stream_type = 'Realtime'
proc = None
print(f'recording {LIB_FILETYPE} files to {LIB_PATH}')


def clear_temp_files():
    for folder in [REC_FOLDER_RAW, REC_FOLDER_TRIM]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')


def start_next_recording():
    global recordings, alt_loop, stream_type, led, db
    recordings.append(RecordingProcess(
        LIB_PATH, LIB_FILETYPE, stream_type, led=led, db=db))
    recordings[-1].start_recording(alt_loop)
    alt_loop = not alt_loop


def main():
    global recordings, alt_loop, stream_type, led, db, running, proc, device
    # Start the subprocess for shairport-sync-metadata-reader
    led.set_sesh_status('Active')
    led.update()
    with subprocess.Popen("/home/dev/shairport-sync-metadata-reader/shairport-sync-metadata-reader < /tmp/shairport-sync-metadata",
                          shell=True, stdout=subprocess.PIPE, text=True) as proc:

        in_bundle = False
        bundle = {}
        print('starting first recording')
        start_next_recording()
        while running:

            if len(recordings) == 0:
                print('no recordings! starting one')
                start_next_recording()
            try:
                if select.select([proc.stdout], [], [], 2)[0]:
                    line = proc.stdout.readline()
                    if not line:
                        print('no data')
                        # # Stop all recordings when there's no more data
                        for recording in recordings:
                            print(recording.song_data.title,
                                  'stopping: no data')
                            recording.stop_recording()
                        break  # Exit the loop if there is no more data
                    if not device.parse_line(line):
                        if 'Metadata bundle' in line:
                            rtp_id = line.split('"')[1]
                            if 'start' in line:
                                bundle = {'rtp': rtp_id}
                                in_bundle = True
                            elif 'end' in line:
                                for recording in recordings:
                                    success = recording.parse_bundle(bundle)
                                    if not success and len(recordings) == 1:
                                        # there's a new song and we need a new recording
                                        print('foreign data! starting new')
                                        start_next_recording()
                                        recordings[-1].parse_bundle(bundle)
                                    if bundle.get('Persistent ID') == recording.song_data.hex_id.value:
                                        break
                                bundle = {}
                                in_bundle = False
                        elif 'Playing frame/time:' in line:
                            rtp = int(line.split('"')[1].split('/')[0])
                            ss_ns = int(line.split('"')[1].split('/')[1])
                            ss_ms = amt_ns_to_ms(ss_ns)
                            for recording in recordings:
                                recording.parse_rtp(rtp, ss_ms)
                        elif 'First frame/time:' in line:
                            rtp = int(line.split('"')[1].split('/')[0])
                            ss_ns = int(line.split('"')[1].split('/')[1])
                            ss_ms = amt_ns_to_ms(ss_ns)

                            for recording in recordings:
                                recording.parse_first_frame(rtp, ss_ms)
                        elif 'Progress String' in line:
                            start, _, end = map(
                                int, line.split('"')[1].split('/'))
                            for recording in recordings:
                                recording.parse_progress(start, end)
                        elif in_bundle:
                            key = line.split(':')[0]
                            if '"' in line:
                                value = line.split('"')[1]
                            else:
                                value = line.split(':')[1].strip('. \n')
                            bundle[key] = value
                        elif 'Stream type' in line:
                            st = line.split('"')[1]
                            if st != stream_type:
                                print(f'Stream type == {st}')
                                for rec in recordings:
                                    rec.set_stream_type(st)
                                stream_type = st
                        elif 'Pause' in line:
                            print(recordings[0].song_data.title,
                                  'stopping: pause')
                            recordings[0].stop_recording()
                            recordings[0].save_song()
                            led.turn_off_rec(recordings[0].device)
                            del recordings[0]
                            if len(recordings) == 0:
                                print('paused and no recordings, starting new')
                                start_next_recording()
                        elif "Play Session Begin." in line:
                            if len(recordings) == 0:
                                start_next_recording()

                        elif "Play Session End." in line:
                            for rec in recordings:
                                print(rec.song_data.title,
                                      'stopping: play session end')
                                rec.stop_recording()
                                rec.save_song()
                                led.turn_off_rec(rec.device)
                            recordings = []
                        elif "Exit Active State" in line:
                            for rec in recordings:
                                print(rec.song_data.title,
                                      'stopping: exit active state')
                                rec.stop_recording()
                                rec.save_song()
                                led.turn_off_rec(rec.device)
                            recordings = []
                        else:
                            print(line.strip())

                        if recordings[0].should_start_next() and len(recordings) == 1:
                            print(
                                'only one rec and should_start_next, starting next')
                            start_next_recording()
                        elif recordings[0].should_stop():
                            print(recordings[0].song_data.title,
                                  'stopping: should_stop')
                            recordings[0].stop_recording()
                            if len(recordings) == 1:
                                print(
                                    '0 should stop and theres no one else, starting next')
                                start_next_recording()
                            recordings[0].save_song()
                            led.turn_off_rec(recordings[0].device)
                            recordings.remove(recordings[0])

                        for rec in recordings:
                            if rec.is_dead():
                                led.turn_off_rec(rec.device)
                                recordings.remove(rec)
                        if running and len(recordings) == 0:
                            print('no recordings! (end) starting next')
                            start_next_recording()
                else:
                    print('no data')
                    time.sleep(1)
            except Exception as e:
                print(e)
            led.update()

            if not running:
                print('ending')
                proc.terminate()
                proc.wait()
                return


def signal_handler(sig, frame):
    global recordings, running, proc
    print('Shutting Down!')
    running = False
    led.set_sesh_status('Stop')
    led.update()
    for rec in recordings:
        rec.stop_recording()
        rec.save_song()
        led.turn_off_rec(rec.device)
    led.update()
    recordings = []
    print('hitting exit')
    if proc is not None:
        proc.terminate()
        proc.wait()
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    clear_temp_files()
    main()
