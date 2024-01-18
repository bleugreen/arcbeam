from PIL import ImageFont, ImageDraw, Image


DEFAULT_FONT_PATH = "/usr/share/fonts/truetype/arcade/ARCADE_R.TTF"
DEFAULT_FONT_SIZE = 18

BG_MARGIN = 5

class LiveTextBox:
    def __init__(self, x, y, width, height, redis_client, hash_key, field, font_path=DEFAULT_FONT_PATH, font_size=DEFAULT_FONT_SIZE, default_text="No Data"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.redis_client = redis_client
        self.hash_key = hash_key
        self.field = field
        self.font = ImageFont.truetype(font_path, font_size)
        self.default_text = default_text
        self.text = ""

    def update_data(self):
        # Fetch data from Redis
        new_data = self.redis_client.hget(self.hash_key, self.field)
        new_text = new_data.decode('utf-8') if new_data else self.default_text

        if new_text != self.text:
            self.text = new_text
            self.needs_update = True

        print(f'Updated text to {self.text} (needs update: {self.needs_update})')

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
            print(f"Reducing font size to {font.size}")
        if text_width > self.width - (2 * BG_MARGIN):
            while font.getlength(text + ABBREVIATION_SUFFIX) >= self.width - (2 * BG_MARGIN):
                text = text[:-1]
            text += ABBREVIATION_SUFFIX
        print(f"Drawing text: {text}")
        # Draw a white rectangle
        drawContext.rectangle((self.x, self.y, self.x + self.width, self.y + self.height), fill=255)
        # Draw the text
        x_offset = (self.width - font.getlength(text) - (2 * BG_MARGIN)) // 2
        drawContext.text((self.x + x_offset + BG_MARGIN, self.y + BG_MARGIN), text, font=font, fill=0)
