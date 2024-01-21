import subprocess
import sys
import os
from backend import RedisClient
import json
import time
from gui import (App, Button, LivePage, LiveSongBox, Menu, ProgressBar,
                 RecStatusBar, ListBrowser)
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

title_page = Menu("gui/images/title.png")
enter_btn = Button(0, 0, 296, 128, title_callback)
title_page.add_elements(enter_btn)

menu_page = Menu("gui/images/menu.png")
record_btn = Button(0, 0, 82, 128, record_callback)
play_btn = Button(82, 0, 59, 128, play_callback)
blend_btn = Button(141, 0, 67, 128, blend_callback)
transfer_btn = Button(208, 0, 88, 128, transfer_callback)
menu_page.add_elements(record_btn, play_btn, blend_btn, transfer_btn)

record_page = LivePage()
song_box = LiveSongBox(0,5,296, 100, redis_client)
progress_bar = ProgressBar(46, 105, 204, 16, bg_color=0, fg_color=255, circle_radius=10, update_function=redis_client.get_current_song_field, function_args=['progress'], )
status_bar_1 = RecStatusBar(4, 105, 16, redis_client.redis, device_id=1)
status_bar_3 = RecStatusBar(260, 105, 16, redis_client.redis, device_id=3)
end_btn = Button(0, 0, 296, 128, end_process_callback, duration=1.0)
record_page.add_elements(end_btn, song_box, progress_bar, status_bar_1, status_bar_3)


browse_page = LivePage()
browse_page.add_elements(ListBrowser(artist_list, (0,0,266, 128), browse_callback, font_size=24))

player_page = LivePage()
song_box_play = LiveSongBox(0,0,296, 100, redis_client, page='player')
progress_bar_play = ProgressBar(46, 105, 204, 16, bg_color=0, fg_color=255, circle_radius=10, update_function=redis_client.get_current_song_field, function_args=['progress', 'player'], )
end_btn = Button(0, 0, 96, 128, player_back_callback, duration=0.5)
pause_btn = Button(100, 0, 96, 128, pause_callback, duration=0.01)
next_btn = Button(196, 0, 100, 128, next_callback, duration=0.01)
player_page.add_elements(pause_btn, next_btn, end_btn, song_box_play, progress_bar_play)


app.add_page("title", title_page)
app.add_page("main_menu", menu_page)
app.add_page("record", record_page)
app.add_page("browser", browse_page)
app.add_page("player", player_page)

app.set_active_page("main_menu")

try:
    app.run()
finally:
    if process is not None:
        process.terminate()
        process.wait()
        process = None
    app.set_active_page("title")
    app.stop()
    sys.exit()