import random
from collections import defaultdict
from .textbutton import TextButton
from .live import LiveComponent
MIN_FONT_SIZE = 12

class WordCloud(LiveComponent):
    def __init__(self, words, screen_width=296, screen_height=128, callbacks=None):
        self.words = words
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.callbacks = [lambda word=word: print(word) for word in words]
        self.text_buttons:list[TextButton] = []
        self.grid_size = 1  # Size of grid cells
        self.grid_cols = self.screen_width // self.grid_size
        self.grid_rows = self.screen_height // self.grid_size
        self.grid = [[None for _ in range(self.grid_cols)] for _ in range(self.grid_rows)]
        self.needs_update = True

    def generate_spiral(self, stretch_factor=3, max_steps=1000):
        """Generate a horizontally stretched spiral sequence of coordinates."""
        dx, dy = 1, 0  # Initial movement direction
        x, y = 296/2, 128/2  # Start from the center
        steps = 1

        for _ in range(max_steps):
            for _ in range(steps):
                yield x, y
                x, y = x + dx * stretch_factor, y + dy  # Move horizontally stretched
            dx, dy = -dy, dx  # Change direction
            if dy == 0:  # Increase step every full cycle (2 turns)
                steps += 1

    def draw(self, draw_context):
        print("Drawing word cloud", len(self.text_buttons))
        self.place_words()
        self.adjust_sizing()
        for text_button in self.text_buttons:
            text_button.draw(draw_context)

    def handle_touch(self, eventType, touch_event):
        for text_button in self.text_buttons:
            text_button.handle_touch(eventType, touch_event)

    def update_data(self):
        # No data to update
        pass

    def place_words(self):
        spiral = self.generate_spiral()
        for word, callback in zip(self.words, self.callbacks):
            font_size = self.estimate_font_size(word)  # Implement this method
            text_button = TextButton(word, 0, 0, font_size, callback)
            for x, y in spiral:
                text_button.update(new_x=x, new_y=y)
                if not self.check_overlap(text_button):
                    self.text_buttons.append(text_button)

                    print(f"Placed word: {word}")
                    break
            else:
                print(f"Could not place word: {word}")

    def estimate_font_size(self, word):
        """
        Estimate font size based on the length of the word and screen dimensions.
        Shorter words start with a larger font size.
        """
        max_font_size = self.screen_height // 4  # Maximum font size
        min_font_size = 10  # Minimum font size

        # Adjust font size based on word length
        font_size = max_font_size - len(word)  # Decrease font size as word length increases
        return max(min_font_size, min(font_size, max_font_size))

    def check_overlap(self, new_button):
        """
        Check if the new_button overlaps with any existing buttons.
        """
        if not self.is_box_in_screen(new_button.bounding_box):
            return True
        for button in self.text_buttons:
            if self.do_boxes_intersect(new_button.bounding_box, button.bounding_box):
                return True  # Overlap detected
        return False

    def is_box_in_screen(self, box):
        return box[0] >= 0 and box[1] >= 0 and box[2] <= self.screen_width and box[3] <= self.screen_height

    def do_boxes_intersect(self, box1, box2):
        """
        Check if two bounding boxes intersect.
        """
        x0_1, y0_1, x1_1, y1_1 = box1
        x0_2, y0_2, x1_2, y1_2 = box2

        return not (x1_1 < x0_2 or x1_2 < x0_1 or y1_1 < y0_2 or y1_2 < y0_1)

    def adjust_sizing(self):
        for text_button in self.text_buttons:
            original_font_size = text_button.font_size
            while True:
                text_button.update(new_font_size=text_button.font_size + 1)
                if self.check_overlap(text_button):
                    text_button.update(new_font_size=original_font_size)  # Revert if overlap
                    break
                else:
                    original_font_size += 1  # Update successfully
                    print("Updating font size to", original_font_size)