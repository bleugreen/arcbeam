from .page import Page
from ..components import LiveComponent, LiveTextBox, Icon
from PIL import Image, ImageOps
import time


class LiveMenu(Page):
    def __init__(self, img_path, full_refresh_interval=180, always_refresh=False):
        super().__init__()
        self.img_path = img_path
        self.has_drawn = False
        self.full_refresh_interval = full_refresh_interval
        self.last_full_refresh = time.time()
        self.always_refresh = always_refresh

    def draw(self, display, drawContext, force_refresh=False):
        # Draw the static image if it has not been drawn yet
        print(f"Drawing LiveMenu: has_drawn={self.has_drawn}" )
        if not self.has_drawn:
            print("Drawing static image", self.img_path)
            image = Image.open(self.img_path)
            image = image.convert("L")
            if self.img_path == "gui/images/menu.png":
                image = ImageOps.invert(image)
            display.image.paste(image, (0, 0))
            display.draw(partial=False , static=False)
            self.has_drawn = True

        # Now handle the dynamic parts as in LivePage
        current_time = time.time()
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

        if needs_update:
            print(f'PARTIAL ::: Due: {full_refresh_due}, Text: {text_update}, force_refresh: {force_refresh}, timesincelast:{ current_time - self.last_full_refresh}')
            display.draw(partial=True, static=False)  # Partial refresh
            for element in self.elements:
                element.has_drawn = True
                element.needs_update = False

    def activate(self):
        self.has_drawn = False
        self.last_full_refresh = time.time()
        for element in self.elements:
            if isinstance(element, LiveComponent):
                element.update_data()
