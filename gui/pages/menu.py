from PIL import Image, ImageOps
from . import Page

class Menu(Page):
    def __init__(self, img_path):
        """
        Initialize a Menu with a specific image path.

        :param img_path: Path to the image to be displayed.
        """
        super().__init__()
        self.img_path = img_path
        self.has_drawn = False

    def activate(self):
        self.has_drawn = False

    def draw(self, display, drawContext, force_refresh=False):
        if not self.has_drawn:
            image = Image.open(self.img_path)
            image = image.convert("L")
            if self.img_path == "gui/images/menu.png":
                image = ImageOps.invert(image)
            display.image.paste(image, (0, 0))

            display.draw(partial=False, static=True)
            self.has_drawn = True
