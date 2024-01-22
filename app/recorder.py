from gui import (Button, LivePage, LiveSongBox, ProgressBar,
                 RecStatusBar)


def make_recorder(app, redis_client):
    def end_process_callback():
        redis_client.publish('stop', 'process')
        app.set_active_page("main_menu")

    record_page = LivePage()
    song_box = LiveSongBox(0,5,296, 100, redis_client)
    progress_bar = ProgressBar(46, 105, 204, 16, bg_color=0, fg_color=255, circle_radius=10, update_function=redis_client.get_current_song_field, function_args=['progress'], )
    status_bar_1 = RecStatusBar(4, 105, 16, redis_client.redis, device_id=1)
    status_bar_3 = RecStatusBar(260, 105, 16, redis_client.redis, device_id=3)
    end_btn = Button(0, 0, 296, 128, end_process_callback, duration=1.0)
    record_page.add_elements(end_btn, song_box, progress_bar, status_bar_1, status_bar_3)
    app.add_page("record", record_page)