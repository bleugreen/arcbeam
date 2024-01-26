import time
from PIL import ImageDraw
from .display import EInkDisplay
from . import LivePage, Page, Menu, LiveMenu
import threading
import redis
from structs.buttonevent import ButtonEvent

class App:
    def __init__(self):
        """
        Initialize the application with an EInk display, a drawing context, and page management.
        """
        self.display = EInkDisplay(self.handle_global_touch)
        self.drawContext = ImageDraw.Draw(self.display.image)
        self.pages = {}
        self.active_page:Page = None
        self.button_listener_thread = threading.Thread(target=self.button_listener)
        self.button_listener_thread.start()

    def button_listener(self):
        """
        Listen for button events from the Redis 'button' channel.
        """
        r = redis.Redis(host='localhost', port=6379, db=0)
        pubsub = r.pubsub()
        pubsub.subscribe('button')

        for message in pubsub.listen():
            if message['type'] == 'message':
                button_event = ButtonEvent.from_string(message['data'].decode())
                self.handle_button_event(button_event)

    def draw_active_page(self, force_refresh=False):
        """
        Pass the display and drawing context to the active page for drawing.
        """
        if self.active_page is not None:
            self.active_page.draw(self.display, self.drawContext, force_refresh=force_refresh)

    def add_page(self, name, page):
        """
        Add a page to the app.

        :param name: The name of the page (used for referencing).
        :param page: The Page object.
        """
        self.pages[name] = page

    def set_active_page(self, name, force_refresh=False):
        """
        Set the active page to be displayed.

        :param name: The name of the page to set as active.
        """
        if name in self.pages and self.pages[name] is not self.active_page:
            self.active_page = self.pages[name]
            self.drawContext.rectangle((0, 0, self.display.width, self.display.height), fill=0)
            self.active_page.activate()
            if force_refresh:
                if isinstance(self.active_page, LivePage):
                    self.draw_active_page(force_refresh=True)
                elif isinstance(self.active_page, LiveMenu):
                    self.draw_active_page()
        elif name in self.pages:
            print(f"Page '{name}' is already active")
        else:
            print(f"Page '{name}' not found")

    def handle_button_event(self, button_event:ButtonEvent):
        """
        Handle button events.

        :param button_event: The ButtonEvent object.
        """
        self.active_page.handle_button(button_event)

    def handle_global_touch(self, eventType, touch_event):
        """
        Global touch event handler. Delegates the event to the active page.

        :param eventType: The type of touch event ('start', 'end', etc.).
        :param touch_event: The TouchEvent object.
        """
        if self.active_page is not None:
            self.active_page.handle_touch(eventType, touch_event)
        else:
            print(f"Unhandled touch event: {eventType}")

    def run(self, refresh_interval=(1.0/30)):
        """
        Run the application with periodic refresh for LiveData pages.

        :param refresh_interval: The time interval (in seconds) for refreshing LiveData pages.
        """
        while True:
            if isinstance(self.active_page, LivePage):
                self.draw_active_page()
            elif isinstance(self.active_page, LiveMenu):
                self.draw_active_page()
            elif isinstance(self.active_page, Menu):
                if not self.active_page.has_drawn:
                    self.draw_active_page()
            time.sleep(refresh_interval)


    def stop(self):
        self.display.stop()
        self.button_listener_thread.do_run = False