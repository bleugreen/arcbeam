import sys
import os
from db import MusicDatabase
from status_led import StatusLed
import time


def process_line(line):
    # Check if the line ends with '.flac'
    if line.strip().endswith('.flac'):
        # Extract song, artist, and album from the line
        parts = line.strip().split('/')
        if len(parts) >= 3:
            song = parts[-1].replace('.flac', '')
            album = parts[-2]
            artist = parts[-3]
            print(f"{song} - {artist} - {album}")
            return artist, album, song
    return None


def main():
    moved_files = []
    led = StatusLed()
    led.turn_off()
    num_files = sum([len(files) for r, d, files in os.walk('/home/dev/crec')])
    # Read from standard input
    count = 0
    for line in sys.stdin:

        result = process_line(line)
        if result:
            moved_files.append(result)
        count += 1
        progress = float(count) / num_files
        led.set_progress(progress)
        led.update()
        time.sleep(0.1)
    db = MusicDatabase()
    # Print each moved file as a tuple
    for file in moved_files:
        song_id, _ = db.song_exists(file[2], file[0], file[1])
        if song_id is not None:
            db.set_exported(song_id)
        else:
            print(f"Song not found: {file}")
    led.turn_off()


if __name__ == "__main__":
    main()
