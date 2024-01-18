from app import App
from menu import Menu
from components.button import Button
from components.livetext import LiveTextBox
from livepage import LivePage
import time
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)
# Assuming all the required classes are already defined

# Callback functions for the buttons
def play_callback():
    print("play pressed")

def record_callback():
    print("record pressed")
    app.set_active_page("record")

def blend_callback():
    print("blend pressed")

def transfer_callback():
    print("transfer pressed")

def end_recording_callback():
    print("end recording pressed")
    app.set_active_page("main_menu")

# Create the app instance
app = App()

# Create a Menu page with an image
menu_page = Menu("/home/dev/cymatic-rec/gui/playerdemo.png")  # Replace with your image path

# Create two buttons
record_btn = Button(0, 0, 82, 128, record_callback)  # Left half of the screen
play_btn = Button(82, 0, 59, 128, play_callback)  # Right half of the screen
blend_btn = Button(141, 0, 67, 128, blend_callback)  # Left half of the screen
transfer_btn = Button(208, 0, 88, 128, transfer_callback)
# Add buttons to the menu page
menu_page.add_elements(record_btn, play_btn, blend_btn, transfer_btn)

# Add the menu page to the app and set it as active
app.add_page("main_menu", menu_page)


test_page = LivePage()

# Create a LiveTextBox for displaying the artist
# Parameters: x, y, width, height, redis_client, hash_key, field, font_path, font_size
title_box = LiveTextBox(0, 40, 296, 84, redis_client, "current_song", "title", font_size=38)
# artist_box = LiveTextBox(10, 45, 286, 65, redis_client, "current_song", "artist", font_size=14)
end_btn = Button(0, 0, 296, 128, end_recording_callback)
# artist_box.update_data()  # Update the data once before drawing

# Add the LiveTextBox to the test page
test_page.add_elements(end_btn, title_box)
app.add_page("record", test_page)

app.set_active_page("record")

app.run()
