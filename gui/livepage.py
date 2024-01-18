from page import Page
from components.livetext import LiveTextBox
from eink import EInkDisplay

import time

class LivePage(Page):
    def __init__(self, full_refresh_interval=120):  # full_refresh_interval in seconds
        super().__init__()
        self.full_refresh_interval = full_refresh_interval
        self.last_full_refresh = 0

    def draw(self, display, drawContext):
        current_time = time.time()
        partial = self.last_full_refresh == 0 or \
            current_time - self.last_full_refresh <= self.full_refresh_interval
        needs_update = False

        for element in self.elements:
            if isinstance(element, LiveTextBox):
                element.update_data()
                if element.needs_update:
                    needs_update = True
                    element.draw(drawContext)

        if needs_update or self.last_full_refresh == 0:
            display.draw(partial, static=False)
            for element in self.elements:
                element.needs_update = False

        if not partial:
            self.last_full_refresh = current_time

    def activate(self):
        self.last_full_refresh = 0
        for element in self.elements:
            if isinstance(element, LiveTextBox):
                element.update_data()
                element.needs_update = True