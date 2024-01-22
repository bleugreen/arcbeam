import subprocess
import sys
import os
from backend import RedisClient
import json
import time
from gui import (App, Button, LivePage, LiveSongBox, Menu, ProgressBar,
                 RecStatusBar, ListBrowser, KeyboardMenu)
from config import PYTHON_PATH, LIB_PATH

process = None
running = False
artist_list = sorted(os.listdir(LIB_PATH))
artist = None
album = None
track = None
process = None
running = False

redis_client = RedisClient()
keep_running = True
# Callback functions for the buttons
def record_callback():
    global process, running
    if not running:
        running = True
        redis_client.reset_song()
        project_root = os.path.dirname(os.path.abspath(__file__))
        command = [PYTHON_PATH, '-m', 'recording.recorder']
        process = subprocess.Popen(command, cwd=project_root)
    app.set_active_page("record")

def play_callback():
    print("play pressed")
    app.set_active_page("browser")

def blend_callback():
    print("blend pressed")  # TODO

def transfer_callback():
    print("transfer pressed")  # TODO

def end_process_callback():
    global process, running
    if running:
        running = False
        process.terminate()
        process.wait()
        process = None
    app.set_active_page("main_menu")

def player_back_callback():
    global artist, album, track, process, running
    if running:
        running = False
        process.terminate()
        process.wait()
        process = None
    artist = None
    album = None
    track = None
    browse_page.elements = []
    browse_page.add_elements(ListBrowser(artist_list, (0,0,266, 128), browse_callback, font_size=24))
    browse_page.needs_update = True
    app.set_active_page("browser")


def get_album_list(artist):
    return sorted(os.listdir(os.path.join(LIB_PATH, artist)))

def get_track_list(artist, album):
    path = os.path.join(LIB_PATH, artist, album)
    return [track.rsplit('.', 1)[0] for track in sorted(os.listdir(path))]

def play_track_callback(track):
    global process, running
    if not running:
        running = True
        redis_client.reset_song()
        project_root = os.path.dirname(os.path.abspath(__file__))
        command = [PYTHON_PATH, '-m', 'player']
        process = subprocess.Popen(command, cwd=project_root)
    redis_client.set_current_song({'title': track, 'artist': artist, 'album': album}, page='player')
    app.set_active_page("player")
    time.sleep(1)
    redis_client.publish(json.dumps({'command': 'play', 'artist': artist, 'album': album, 'title': track}), 'player')
    print(f"Playing {track} from {album} by {artist}")

def album_callback(val):
    global album
    album = val
    track_list = get_track_list(artist, album)
    browse_page.elements = []
    browse_page.add_elements(ListBrowser(track_list, (0,0,266, 128), play_track_callback, font_size=24))
    browse_page.needs_update = True


def browse_callback(val):
    global artist, browse_page
    artist = val
    print(f"Artist: {artist}")
    album_list = get_album_list(artist)
    browse_page.elements = []
    browse_page.add_elements(ListBrowser(album_list, (0,0,266, 128), album_callback, font_size=24))
    print(browse_page.elements[0].items)
    browse_page.needs_update = True

def pause_callback():
    global redis_client
    is_paused = redis_client.get_current_song_field('is_paused', 'player')
    if is_paused == '1' or is_paused.lower() == 'true':
        redis_client.publish(json.dumps({'command': 'resume'}), 'player')
    else:
        redis_client.publish(json.dumps({'command': 'pause'}), 'player')

def next_callback():
    global redis_client
    redis_client.publish(json.dumps({'command': 'next'}), 'player')

def title_callback():
    app.set_active_page("main_menu")



# Create the app instance
app = App()


def keyboard_submit(text):
    print(f'Keyboard submitted: {text}')

def keyboard_cancel():
    print('Keyboard cancelled')

title_page = KeyboardMenu(on_submit=keyboard_submit, on_cancel=keyboard_cancel)



app.add_page("title", title_page)

app.set_active_page("title")

try:
    app.run()
finally:
    if process is not None:
        process.terminate()
        process.wait()
        process = None
    app.stop()
    sys.exit()