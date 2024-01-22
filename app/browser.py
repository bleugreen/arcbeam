import os
import json
import time
from gui import PaginatedList, LivePage, LiveMenu, BrowserMenu, KeyboardMenu
from config import LIB_PATH

def rstrstr(app, redis_client):
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
            track_browser.elements = [PaginatedList(track_list, (0,0,266, 128), play_track_callback, font_size=24)]
            track_browser.needs_update = True
            app.set_active_page("track_browser")

    def browse_callback(val):
        if val:
            redis_client.set_browse('artist', val)
            album_list = get_album_list(val)
            album_browser.elements = [PaginatedList(album_list, (0,0,266, 128), album_callback, font_size=24)]
            album_browser.needs_update = True
            app.set_active_page("album_browser")

    artist_list = sorted(os.listdir(LIB_PATH))
    artist_browser.add_elements(PaginatedList(artist_list, (0,0,266, 128), browse_callback, font_size=24))

    app.add_page("album_browser", album_browser)
    app.add_page("track_browser", track_browser)



def make_browser(app, redis_client):
    artist_list = sorted(os.listdir(LIB_PATH))
    redis_client.reset_browse()
    artist_browser = BrowserMenu(artist_list, (0,0,266,128))
    filter_text = {
        'artist': '',
        'album': '',
        'track': ''
    }

    def keyboard_submit(text):
        print(f'Keyboard submitted: {text}')
        nonlocal filter_text
        filter_text[artist_browser.level] = text
        items = get_list_items(artist_browser.level)
        artist_browser.update_items(items, artist_browser.level)
        app.set_active_page("browser")

    def keyboard_cancel():
        print('Keyboard cancelled')
        nonlocal filter_text
        filter_text[artist_browser.level] = ''
        items = get_list_items(artist_browser.level)
        artist_browser.update_items(items, artist_browser.level)
        app.set_active_page("browser")

    filter_page = KeyboardMenu(on_submit=keyboard_submit, on_cancel=keyboard_cancel)

    def get_list_items(level):
        nonlocal filter_text
        if level == 'artist':
            artist_list = sorted(os.listdir(LIB_PATH))
            if filter_text[level]:
                return [artist for artist in artist_list if artist.lower().startswith(filter_text[level].lower())]
            return artist_list
        elif level == 'album':
            artist = redis_client.get_browse('artist')
            album_list= sorted(os.listdir(os.path.join(LIB_PATH, artist)))
            if filter_text[level]:
                return [album for album in album_list if album.lower().startswith(filter_text[level].lower())]
            return album_list
        elif level == 'track':
            artist = redis_client.get_browse('artist')
            album = redis_client.get_browse('album')
            path = os.path.join(LIB_PATH, artist, album)
            track_list= [track.rsplit('.', 1)[0] for track in sorted(os.listdir(path))]
            if filter_text[level]:
                return [track for track in track_list if track.lower().startswith(filter_text[level].lower())]
            return track_list

    def play_track(track):
        if not track:
            print("No track selected")
            return
        redis_client.publish('start:player', 'process')
        artist = redis_client.get_browse('artist')
        album = redis_client.get_browse('album')
        redis_client.set_current_song({'title': track, 'artist': artist, 'album': album}, page='player')
        app.set_active_page("player")
        next_level = 'track'
        print(f'setting {next_level} page')
        items = get_list_items(next_level)
        artist_browser.update_items(items, next_level)
        time.sleep(1)

        redis_client.publish(json.dumps({'command': 'play', 'artist': artist, 'album': album, 'title': track}), 'player')
        print(f"Playing {track} from {album} by {artist}")

    def on_select(level, val):
        if not val:
            print("Nothing selected")
            return
        if level == 'track':
            play_track(val)
            return
        print(f"{level} selected: {val}")
        redis_client.set_browse(level, val)
        next_level = 'album' if level == 'artist' else 'track'
        print(f'setting {next_level} page')
        items = get_list_items(next_level)
        artist_browser.update_items(items, next_level)
        # app.set_active_page("album_browser")

    def on_back(level):
        print("Back pressed")
        nonlocal filter_text
        if filter_text[level]:
                filter_text[level] = ''
                items = get_list_items(level)
                artist_browser.update_items(items, level)
                return
        if level == 'artist':
            redis_client.reset_browse()
            redis_client.publish('stop', 'process')
            app.set_active_page("main_menu")
        elif level == 'album':
            redis_client.redis.hdel('browse', 'artist')
            next_level = 'artist'
            print(f'setting {next_level} page')
            items = get_list_items(next_level)
            artist_browser.update_items(items, next_level)
        elif level == 'track':
            redis_client.redis.hdel('browse', 'album')
            next_level = 'album'
            print(f'setting {next_level} page')
            items = get_list_items(next_level)
            artist_browser.update_items(items, next_level)

    def on_filter():
        filter_page.text_state = filter_text[artist_browser.level]
        app.set_active_page("filter")

    # def on_filter
    artist_browser.on_select = on_select
    artist_browser.on_back = on_back
    artist_browser.on_filter = on_filter
    artist_browser.make_elements()
    app.add_page("browser", artist_browser)
    app.add_page("filter", filter_page)