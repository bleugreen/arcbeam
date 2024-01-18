from eink import EInkDisplay
from PIL import ImageDraw
from livepage import LivePage
import time

class App:
    def __init__(self):
        """
        Initialize the application with an EInk display, a drawing context, and page management.
        """
        self.display = EInkDisplay(self.handle_global_touch)
        self.drawContext = ImageDraw.Draw(self.display.image)
        self.pages = {}
        self.active_page = None

    def draw_active_page(self):
        """
        Pass the display and drawing context to the active page for drawing.
        """
        if self.active_page is not None:
            self.active_page.draw(self.display, self.drawContext)

    def add_page(self, name, page):
        """
        Add a page to the app.

        :param name: The name of the page (used for referencing).
        :param page: The Page object.
        """
        self.pages[name] = page

    def set_active_page(self, name):
        """
        Set the active page to be displayed.

        :param name: The name of the page to set as active.
        """
        if name in self.pages:
            self.active_page = self.pages[name]
            self.display.clear()
            self.active_page.activate()
            self.draw_active_page()
        else:
            print(f"Page '{name}' not found")

    def handle_global_touch(self, eventType, touch_event):
        """
        Global touch event handler. Delegates the event to the active page.

        :param eventType: The type of touch event ('start', 'end', etc.).
        :param touch_event: The TouchEvent object.
        """
        if self.active_page is not None:
            if eventType == 'start':
                self.active_page.handle_touch(touch_event.start_x, touch_event.start_y)
            else:
                print(f"Unhandled touch event: {eventType}")

    def run(self, refresh_interval=5):
        """
        Run the application with periodic refresh for LiveData pages.

        :param refresh_interval: The time interval (in seconds) for refreshing LiveData pages.
        """
        try:
            while True:
                if isinstance(self.active_page, LivePage):
                    print("Refreshing live page...")
                    self.draw_active_page()
                time.sleep(refresh_interval)
        except KeyboardInterrupt:
            # Handle any cleanup here if necessary before exiting
            self.stop()
            print("Application closed.")

    def stop(self):
        self.display.stop()