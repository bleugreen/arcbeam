import os
import json
import time
from gui import PaginatedList, LivePage, LiveMenu, BrowserMenu, KeyboardMenu
from config import LIB_PATH




def make_browser(app, redis_client):
    artist_list = sorted(os.listdir(LIB_PATH))
    redis_client.reset_browse()
    artist_browser = BrowserMenu(artist_list, (0,0,266,128))
    filter_text = {
        'artist': '',
        'album': '',
        'track': ''
    }
    playing = False

    def keyboard_submit(text):
        print(f'Keyboard submitted: {text}')
        nonlocal filter_text
        filter_text[artist_browser.level] = text
        # items = get_list_items(artist_browser.level)
        # artist_browser.update_items(items, artist_browser.level)
        artist_browser.navigate_to_match(text)
        filter_text[artist_browser.level] = ''
        app.set_active_page("browser")

    def get_list_items(level):
        if level == 'artist':
            artists = os.listdir(LIB_PATH)
            return sorted(artists, key=lambda s: s.lower())
        elif level == 'album':
            artist = redis_client.get_browse('artist')
            albums = os.listdir(os.path.join(LIB_PATH, artist))
            return sorted(albums, key=lambda s: s.lower())
        elif level == 'track':
            artist = redis_client.get_browse('artist')
            album = redis_client.get_browse('album')
            path = os.path.join(LIB_PATH, artist, album)
            tracks = os.listdir(path)
            return sorted([s.rsplit('.', 1)[0] for s in tracks], key=lambda s: s.lower())

    def keyboard_cancel():
        print('Keyboard cancelled')
        nonlocal filter_text
        filter_text[artist_browser.level] = ''
        items = get_list_items(artist_browser.level)
        artist_browser.update_items(items, artist_browser.level)
        app.set_active_page("browser")

    filter_page = KeyboardMenu(on_submit=keyboard_submit, on_cancel=keyboard_cancel)
    artist_browser.get_data = get_list_items

    def play_track(track):
        nonlocal playing
        if not track:
            print("No track selected")
            return
        redis_client.publish('start:player', 'process')
        artist = redis_client.get_browse('artist')
        album = redis_client.get_browse('album')
        redis_client.set_current_song({'title': track, 'artist': artist, 'album': album}, page='player')
        app.set_active_page("player")
        playing = True
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
        nonlocal filter_text, playing
        if filter_text[level]:
                filter_text[level] = ''
                items = get_list_items(level)
                artist_browser.update_items(items, level)
                return
        if level == 'artist':
            redis_client.reset_browse()
            redis_client.publish('stop', 'process')
            app.set_active_page("main_menu")
            playing = False
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

    def on_btn(btn):
        nonlocal playing
        print(f"Button pressed: {btn}")
        if btn.button_name == 'mid' and btn.event_type == 'up':
            if btn.duration > 1:
                playing = False
                redis_client.reset_browse()
                redis_client.publish('stop', 'process')
                app.set_active_page("main_menu")
            elif playing:
                app.set_active_page("player")
            else:
                on_back(artist_browser.level)



    # def on_filter
    artist_browser.on_select = on_select
    artist_browser.on_btn = on_btn
    artist_browser.on_back = on_back
    artist_browser.on_filter = on_filter
    artist_browser.make_elements()
    app.add_page("browser", artist_browser)
    app.add_page("filter", filter_page)