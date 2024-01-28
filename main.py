import logging
import sys
from gui import (make_browser, make_main_menu, make_player, make_recorder,
                 make_title_page)
from backend import RedisClient
from application import App
from process import ProcessManager

logging.basicConfig(level=logging.INFO)
redis_client = RedisClient()

proc_manager = ProcessManager()

app = App()

make_title_page(app)
make_main_menu(app, redis_client)
make_recorder(app, redis_client)
make_browser(app, redis_client)
make_player(app, redis_client)

app.set_active_page("main_menu")

def graceful_exit(signum, frame):
    logging.info("Graceful exit initiated.")
    redis_client.publish('process', 'stop:all')
    # app.set_active_page("title", force_refresh=True)
    # time.sleep(1)
    app.stop()
    proc_manager.stop()
    sys.exit(0)

try:
    proc_manager.start()
    app.run()
except Exception as e:
    logging.error(f"Error running app: {e}")
finally:
    graceful_exit(None, None)
