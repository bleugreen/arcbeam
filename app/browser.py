import subprocess
import os
import json
import time
from gui import ListBrowser, LivePage
from config import PYTHON_PATH, LIB_PATH

def make_browser(app, redis_client):
    artist_browser = LivePage()
    album_browser = LivePage()
    track_browser = LivePage()

    def get_album_list(artist):
        return sorted(os.listdir(os.path.join(LIB_PATH, artist)))

    def get_track_list(artist, album):
        path = os.path.join(LIB_PATH, artist, album)
        return [track.rsplit('.', 1)[0] for track in sorted(os.listdir(path))]

    def play_track_callback(track):
        if not track:
            print("No track selected")
            return
        redis_client.publish('start:player', 'process')
        artist = redis_client.get_browse('artist')
        album = redis_client.get_browse('album')
        redis_client.set_current_song({'title': track, 'artist': artist, 'album': album}, page='player')
        app.set_active_page("player")
        time.sleep(1)
        redis_client.publish(json.dumps({'command': 'play', 'artist': artist, 'album': album, 'title': track}), 'player')
        print(f"Playing {track} from {album} by {artist}")

    def album_callback(val):
        if val:
            print(f"Album selected: {val}")
            redis_client.set_browse('album', val)
            artist = redis_client.get_browse('artist')
            track_list = get_track_list(artist, val)
            track_browser.elements = [ListBrowser(track_list, (0,0,266, 128), play_track_callback, font_size=24)]
            track_browser.needs_update = True
            app.set_active_page("track_browser")

    def browse_callback(val):
        if val:
            redis_client.set_browse('artist', val)
            album_list = get_album_list(val)
            album_browser.elements = [ListBrowser(album_list, (0,0,266, 128), album_callback, font_size=24)]
            album_browser.needs_update = True
            app.set_active_page("album_browser")

    artist_list = sorted(os.listdir(LIB_PATH))
    artist_browser.add_elements(ListBrowser(artist_list, (0,0,266, 128), browse_callback, font_size=24))

    app.add_page("browser", artist_browser)
    app.add_page("album_browser", album_browser)
    app.add_page("track_browser", track_browser)
