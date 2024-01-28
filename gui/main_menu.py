import subprocess
import os
from application import App, Button, Menu
from config import PYTHON_PATH

def make_main_menu(app:App, redis_client):
    def record_callback():
        redis_client.reset_song()
        redis_client.publish('start:recorder', 'process')
        app.set_active_page("record")

    def play_callback():
        print("play pressed")
        app.set_active_page("browser")

    def blend_callback():
        print("blend pressed")  # TODO

    def transfer_callback():
        print("transfer pressed")  # TODO

    menu_page = Menu("gui/images/menu.png")
    record_btn = Button(0, 0, 82, 128, record_callback)
    play_btn = Button(82, 0, 59, 128, play_callback)
    blend_btn = Button(141, 0, 67, 128, blend_callback)
    transfer_btn = Button(208, 0, 88, 128, transfer_callback)
    menu_page.add_elements(record_btn, play_btn, blend_btn, transfer_btn)

    app.add_page("main_menu", menu_page)