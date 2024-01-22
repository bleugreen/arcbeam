import sys
from backend import RedisClient
from gui import App
from app import make_title_page, make_main_menu, make_recorder, make_browser, make_player
from config import PYTHON_PATH
import subprocess
import threading

redis_client = RedisClient()


def start_process_thread():
    command = [PYTHON_PATH, '-m', 'process']
    return threading.Thread(target=subprocess.Popen, args=(command,)).start()

proc_thread = start_process_thread()

# Create the app instance
app = App()

make_title_page(app)
make_main_menu(app, redis_client)
make_recorder(app, redis_client)
make_browser(app, redis_client)
make_player(app, redis_client)

app.set_active_page("main_menu")

try:
    app.run()
finally:
    redis_client.publish('stop:all', 'process')
    app.set_active_page("title")
    app.stop()
    if proc_thread:
        proc_thread.join()
    sys.exit()