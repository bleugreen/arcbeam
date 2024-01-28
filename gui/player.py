import json
from application import (Button, LivePage, LiveSongBox, ProgressBar)


def make_player(app, redis_client):
    def player_back_callback():
        app.set_active_page("browser")

    def on_btn(btn):
        print(f"Button pressed: {btn}")
        if btn.button_name == 'mid' and btn.event_type == 'up':
            if btn.duration > 1:
                redis_client.reset_browse()
                redis_client.publish('stop', 'process')
                redis_client.reset_song()
                app.set_active_page("main_menu")
            else:
                app.set_active_page("browser")


    def pause_callback():
        is_paused = redis_client.get_current_song_field('is_paused', 'player')
        if is_paused == '1' or is_paused.lower() == 'true':
            redis_client.publish(json.dumps({'command': 'resume'}), 'player')
        else:
            redis_client.publish(json.dumps({'command': 'pause'}), 'player')

    def next_callback():
        redis_client.publish(json.dumps({'command': 'next'}), 'player')


    player_page = LivePage(on_btn=on_btn)
    song_box_play = LiveSongBox(0,0,296, 100, redis_client, page='player')
    progress_bar_play = ProgressBar(46, 105, 204, 16, bg_color=0, fg_color=255, circle_radius=10, update_function=redis_client.get_current_song_field, function_args=['progress', 'player'], )
    end_btn = Button(0, 0, 96, 128, player_back_callback, duration=0.2)
    pause_btn = Button(100, 0, 96, 128, pause_callback, duration=0.01)
    next_btn = Button(196, 0, 100, 128, next_callback, duration=0.01)
    player_page.add_elements(pause_btn, next_btn, end_btn, song_box_play, progress_bar_play)

    app.add_page("player", player_page)