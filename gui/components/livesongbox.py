from PIL import ImageDraw, ImageFont
from backend import RedisClient
from . import LiveComponent

DEFAULT_FONT_PATH = "gui/fonts/ARCADE_R.TTF"
DEFAULT_FONT_SIZE = 18
BG_MARGIN = 5
MIN_FONT_SIZE = 8


class LiveSongBox(LiveComponent):
    def __init__(self, x, y, width, height,  redis:RedisClient=None, margin=4, font_path=DEFAULT_FONT_PATH, font_size=DEFAULT_FONT_SIZE, default_text="", page='rec'):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.redis = redis if redis is not None else RedisClient()
        self.font_path = font_path
        self.margin = margin
        self.font = ImageFont.truetype(font_path, font_size)
        self.default_text = default_text
        self.text = {"title": "", 'artist': '', 'album': ''}
        self.needs_update = False
        self.page = page

    def update_field(self, field):
        new_data = self.redis.get_current_song_field(field, page=self.page)
        new_text = str(new_data) if new_data is not None else self.default_text
        new_text = new_text.split(' (')[0]
        if new_text != self.text[field]:
            self.text[field] = new_text
            self.needs_update = True

    def update_data(self):
        self.update_field('title')
        self.update_field('artist')
        self.update_field('album')

    def draw(self, draw: ImageDraw):
        fg_color = 255
        bg_color = 0

        def textsize(text, font: ImageFont):
            width = font.getlength(text)
            return width, font.size

        def abbreviate_text(text, font, max_width):
            while font.getlength(text + '...') > max_width and len(text) > 0:
                text = text[:-1]
            return text + '...' if len(text) < len(self.text) else text

        def calculate_max_font_size(text, max_width, max_height):
            font_size = 1
            font = ImageFont.truetype(self.font_path, font_size)
            text_width, text_height = textsize(text, font)
            width_constrained = False
            while text_width <= max_width and text_height <= max_height:
                font_size += 1
                font = ImageFont.truetype(self.font_path, font_size)
                text_width, text_height = textsize(text, font)
            if text_width > max_width:
                width_constrained = True
                font_size -= 1
            font_size = max(MIN_FONT_SIZE, font_size)
            if font_size == MIN_FONT_SIZE:
                text = abbreviate_text(text, ImageFont.truetype(self.font_path, MIN_FONT_SIZE), max_width)
            return font_size, text, width_constrained

        # Calculate maximum font sizes
        title_font_size, title, _ = calculate_max_font_size(self.text['title'], self.width, self.height *0.5)
        album_font_size, album, _ = calculate_max_font_size(self.text['album'], self.width, (self.height-title_font_size) * 0.4)
        artist_font_size, artist, _ = calculate_max_font_size(self.text['artist'], self.width, (self.height-title_font_size-album_font_size))

        # Fonts with the calculated sizes
        title_font = ImageFont.truetype(self.font_path, title_font_size)
        album_font = ImageFont.truetype(self.font_path, album_font_size)
        artist_font = ImageFont.truetype(self.font_path, artist_font_size)

        # Calculate text sizes
        title_width, title_height = textsize(title, title_font)
        album_width, album_height = textsize(album, album_font)
        artist_width, artist_height = textsize(artist, artist_font)

        # Drawing the background
        draw.rectangle((self.x, self.y, self.x + self.width, self.y + self.height), fill=bg_color)

        total_text_height = title_height + album_height + artist_height
        extra_space = self.height - total_text_height
        title_y_position = self.y+ extra_space / 4
        artist_y_position = title_y_position + title_height + extra_space / 4
        album_y_position = artist_y_position + artist_height + extra_space / 4

        # Drawing title
        draw.text((self.x + (self.width - title_width) / 2, title_y_position), title, fill=fg_color, font=title_font)

        # Drawing artist
        draw.text((self.x + (self.width - artist_width) / 2, artist_y_position), artist, fill=fg_color, font=artist_font)

        # Drawing album
        draw.text((self.x + (self.width - album_width) / 2, album_y_position), album, fill=fg_color, font=album_font)
