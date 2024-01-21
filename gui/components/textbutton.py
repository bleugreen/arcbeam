from PIL import ImageFont
from .live import LiveComponent

class TextButton(LiveComponent):
    def __init__(self, text, x, y, font_size, callback, font_path="fonts/ARCADE_R.TTF"):
        self.text = text
        self.x = x
        self.y = y
        self.font_size = font_size
        self.callback = callback
        self.font = ImageFont.truetype(font_path, font_size)
        self.bounding_box = self.calculate_bounding_box()
        self.needs_update = True

    def calculate_bounding_box(self):
        # Calculate text width and height
        text_width, text_height = self.font.getlength(self.text), self.font.size
        # Calculate bounding box
        x0 = self.x
        y0 = self.y
        x1 = self.x + text_width
        y1 = self.y + text_height
        return (x0, y0, x1, y1)

    def update(self, new_text=None, new_x=None, new_y=None, new_font_size=None):
        # Update properties if new values are provided
        if new_text is not None:
            self.text = new_text
        if new_x is not None:
            self.x = new_x
        if new_y is not None:
            self.y = new_y
        if new_font_size is not None:
            self.font_size = new_font_size
            self.font = ImageFont.truetype(self.font.path, new_font_size)
        # Recalculate the bounding box
        self.bounding_box = self.calculate_bounding_box()
        return self.bounding_box

    def update_data(self):
        # No data to update
        pass

    def draw(self, draw_context):
        # Draw the button text
        print(f"Drawing button {self.text} at {self.x}, {self.y}")
        draw_context.text((self.x, self.y), self.text, font=self.font, fill=255)

    def is_pressed(self, touch_x, touch_y):
        # Check if the given coordinates are within the bounding box
        x0, y0, x1, y1 = self.bounding_box
        return x0 <= int(touch_x) <= x1 and y0 <= int(touch_y) <= y1

    def handle_touch(self, eventType, touch_event):
        if self.is_pressed(touch_event.start_x, touch_event.start_y):
            self.callback()  # Call the callback function
