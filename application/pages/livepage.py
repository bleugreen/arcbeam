import time
from ..components import LiveComponent, LiveTextBox, Icon
from . import Page


class LivePage(Page):
    def __init__(self, full_refresh_interval=180, always_refresh=False, on_btn=None):  # full_refresh_interval in seconds
        super().__init__()
        self.full_refresh_interval = full_refresh_interval
        self.last_full_refresh = time.time()
        self.always_refresh = always_refresh
        self.on_btn = on_btn

    def draw(self, display, drawContext, force_refresh=False):
        current_time = time.time()
        # Check if the full refresh interval has elapsed
        full_refresh_due = current_time - self.last_full_refresh > self.full_refresh_interval
        needs_update = False
        text_update = False

        for element in self.elements:
            if isinstance(element, LiveComponent):
                element.update_data()
                if element.needs_update:
                    needs_update = True
                    element.draw(drawContext)
                    if isinstance(element, LiveTextBox):
                        text_update = True
            elif isinstance(element, Icon):
                if not element.has_drawn:
                    needs_update = True
                    element.draw(drawContext)

        # Full refresh is needed if it's due and there's a text update
        full_refresh_needed = full_refresh_due and text_update



        if full_refresh_needed or force_refresh:
            print(f'FULLREFRESHING ::: Due: {full_refresh_due}, Text: {text_update}, force_refresh: {force_refresh}, timesincelast:{ current_time - self.last_full_refresh}')
            display.draw(partial=False , static=False)  # Full refresh
            self.last_full_refresh = current_time
            for element in self.elements:
                element.has_drawn = True
                element.needs_update = False
        elif needs_update:
            print(f'PARTIAL ::: Due: {full_refresh_due}, Text: {text_update}, force_refresh: {force_refresh}, timesincelast:{ current_time - self.last_full_refresh}')
            display.draw(partial=True, static=False)  # Partial refresh
            for element in self.elements:
                element.has_drawn = True
                element.needs_update = False
        # Reset the needs_update flag for all elements

    def handle_button(self, button_event):
        """
        Handle a button event by delegating it to the appropriate UI element.

        :param button_event: The ButtonEvent object.
        """
        if self.on_btn is not None:
            self.on_btn(button_event)

    def activate(self):
        self.last_full_refresh = time.time()
        for element in self.elements:
            if isinstance(element, LiveComponent):
                element.update_data()
                element.needs_update = True