
import subprocess
import time
from status_led import StatusLed
import threading
from db import MusicDatabase
from config import LIB_DELETE_ON_EXPORT

def mount_drive(drive):
    command = ['sudo', 'udisksctl', 'mount', '-b', drive]
    result = subprocess.run(command, capture_output=True, text=True)
    mounted_path = result.stdout.split(' ')[-1]
    return mounted_path


def unmount_drive(drive):
    command = ['sudo', 'udisksctl', 'unmount', '-b', drive]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout


# def export_chunes(mount_path):
#     create_dir_cmd = ['sudo', 'mkdir', '-p', f'{mount_path}/music']
#     subprocess.run(create_dir_cmd, capture_output=True, text=True)
#     print(mount_path)
#     dry_run_cmd = ['sudo', 'rsync', '-rvn',
#                    '/home/dev/crec/', f'{mount_path}/music']
#     result = subprocess.run(
#         dry_run_cmd, capture_output=True)
#     files = result.stdout.splitlines()[1:-3]
#     for file in files:
#         line = file.decode('utf-8').strip()
#         parts = line.strip().split('/')
#         if len(parts) >= 3 and line.endswith('.flac'):
#             song = parts[-1].replace('.flac', '')
#             album = parts[-2]
#             artist = parts[-3]
#             print(f"{song} - {artist} - {album}")

def export_chunes(mount_path, led, db):
    create_dir_cmd = ['sudo', 'mkdir', '-p', f'{mount_path}/music']
    subprocess.run(create_dir_cmd, capture_output=True, text=True)
    print(mount_path)

    dry_run_cmd = ['sudo', 'rsync', '-rvn',
                   '/home/dev/crec/', f'{mount_path}/music/']
    real_cmd = ['sudo', 'rsync', '-rv',]
    if LIB_DELETE_ON_EXPORT:
        real_cmd.append('--remove-source-files')
    real_cmd.extend(['/home/dev/crec/', f'{mount_path}/music/'])
    result = subprocess.run(
        dry_run_cmd, capture_output=True)
    to_copy = result.stdout.splitlines()[1:-3]
    files = []
    for file in to_copy:
        line = file.decode('utf-8').strip()
        if line.endswith('.flac'):
            files.append(line)
    print(f'Copying {len(files)} files to {mount_path}/music/')
    with subprocess.Popen(real_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as proc:
        for line in proc.stdout:
            # Call a function to process each line
            process_output_line(line, files, led, db)

        if proc.returncode != 0:
            # Handle error
            error_output = proc.stderr.read()
            print(f'Error copying files: {error_output}')


def process_output_line(line, files, led, db: MusicDatabase):
    line = line.strip()
    try:
        idx = files.index(line)
        progress = (float(idx+1)/len(files))
        parts = line.strip().split('/')
        if len(parts) >= 3 and line.endswith('.flac'):
            song = parts[-1].replace('.flac', '')
            album = parts[-2]
            artist = parts[-3]
            print(f"{song} - {artist} - {album} - {progress}")
            song_id, _ = db.song_exists(song, artist, album)
            if song_id is not None:
                print('export', song_id)
                db.set_exported(song_id)
            else:
                print("Song not found")
            led.set_progress(progress)
            led.update()
            time.sleep(0.1)
    except ValueError:
        pass


def sync_music(drive, led: StatusLed, ):
    db = MusicDatabase()
    led.set_sesh_status('Save', update=True)
    path = mount_drive(drive)
    if '/media/root/' in path:
        led.set_drive_status('Good', update=True)
        export_chunes(path.strip(), led, db)
        print(unmount_drive(drive))
        led.set_drive_status('Off')
        led.set_progress(-1)
        led.set_sesh_status('Good', update=True)
        time.sleep(1)
        led.set_sesh_status('Stop', update=True)
    else:
        led.set_drive_status('Error', update=True)
        time.sleep(1)
