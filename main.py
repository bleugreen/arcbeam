import subprocess
import sys
from backend import RedisClient
from gui import (App, Button, LivePage, LiveSongBox, Menu, ProgressBar,
                 RecStatusBar)

process = None
running = False

redis_client = RedisClient()

# Callback functions for the buttons
def record_callback():
    global process, running
    if not running:
        running = True
        redis_client.reset_song()
        command = ['/home/dev/env/bin/python',
                    '/home/dev/cymatic-rec/recorder.py']
        process = subprocess.Popen(command)
    app.set_active_page("record")


redis_client.get_current_song_field('title')

def play_callback():
    print("play pressed")

def blend_callback():
    print("blend pressed")

def transfer_callback():
    print("transfer pressed")

def end_recording_callback():
    print("end recording pressed")
    global process, running
    if running:
        running = False
        process.terminate()
        process.wait()
        process = None
    app.set_active_page("main_menu")

# Create the app instance
app = App()

title_page = Menu("gui/images/title.png")
def title_callback():
    app.set_active_page("main_menu")
enter_btn = Button(0, 0, 296, 128, title_callback)
title_page.add_elements(enter_btn)

menu_page = Menu("gui/images/crecmenu2.png")  # Replace with your image path
record_btn = Button(0, 0, 82, 128, record_callback)
play_btn = Button(82, 0, 59, 128, play_callback)
blend_btn = Button(141, 0, 67, 128, blend_callback)
transfer_btn = Button(208, 0, 88, 128, transfer_callback)
menu_page.add_elements(record_btn, play_btn, blend_btn, transfer_btn)

record_page = LivePage()

def remove_parentheses(string):
    return string.split(' (')[0]


def get_song_data_clean(field):
    data = redis_client.get_current_song_field(field)
    if data is None:
        return ''
    return remove_parentheses(data)

song_box = LiveSongBox(0,5,296, 100, redis_client)
progress_bar = ProgressBar(46, 105, 204, 16, bg_color=0, fg_color=255, circle_radius=10, update_function=redis_client.get_current_song_field, function_args=['progress'], )
status_bar_1 = RecStatusBar(4, 105, 16, redis_client.redis, device_id=1)
status_bar_3 = RecStatusBar(260, 105, 16, redis_client.redis, device_id=3)
def get_artist_album():
    artist = redis_client.get_current_song_field('artist')
    album = redis_client.get_current_song_field('album')
    if artist is None or album is None:
        return None
    return f"{artist} - {album}"


# artistalbum_box = LiveTextBox(0, 65, 296, 90, get_artist_album, function_args=[], font_size=38)
end_btn = Button(0, 0, 296, 128, end_recording_callback, duration=1.0)
record_page.add_elements(end_btn, song_box, progress_bar, status_bar_1, status_bar_3)
app.add_page("title", title_page)
app.add_page("main_menu", menu_page)
app.add_page("record", record_page)

app.set_active_page("title")
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