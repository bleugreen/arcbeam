from PIL import ImageFont
from . import LiveComponent

DEFAULT_FONT_PATH = "gui/fonts/ARCADE_R.TTF"
DEFAULT_FONT_SIZE = 14
BG_MARGIN = 5

class LiveTextBox(LiveComponent):
    def __init__(self, x, y, width, height, update_function, function_args=(), font_path=DEFAULT_FONT_PATH, font_size=DEFAULT_FONT_SIZE, default_text=""):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.update_function = update_function
        self.function_args = function_args
        self.font = ImageFont.truetype(font_path, font_size)
        self.default_text = default_text
        self.text = ""
        self.needs_update = False

    def update_data(self):
        # Fetch data using the provided function and arguments
        new_data = self.update_function(*self.function_args)
        new_text = str(new_data) if new_data is not None else self.default_text

        if new_text != self.text:
            self.text = new_text
            self.needs_update = True

    def draw(self, drawContext):
        # Abbreviate text if it's too long and reduce font size to MIN_FONT_SIZE if necessary
        MIN_FONT_SIZE = 10
        ABBREVIATION_SUFFIX = "..."
        text = self.text
        font = self.font
        text_width = font.getlength(text)
        while text_width > self.width - (2 * BG_MARGIN) and font.size > MIN_FONT_SIZE:
            font = ImageFont.truetype(font.path, max(font.size - 1, MIN_FONT_SIZE))
            text_width = font.getlength(text)
        if text_width > self.width - (2 * BG_MARGIN):
            while font.getlength(text + ABBREVIATION_SUFFIX) >= self.width - (2 * BG_MARGIN):
                text = text[:-1]
            text += ABBREVIATION_SUFFIX
        # Draw a white rectangle
        drawContext.rectangle((self.x, self.y, self.x + self.width, self.y + self.height), fill=0)
        # Draw the text

        x_offset = (self.width - font.getlength(text) - (2 * BG_MARGIN)) // 2
        y_offset = (self.height - font.size - (2 * BG_MARGIN)) // 2
        drawContext.text((self.x + x_offset + BG_MARGIN, self.y + y_offset + BG_MARGIN), text, font=font, fill=255)
