from .textbutton import TextButton
from .live import LiveComponent

FONT = "/home/dev/cymatic-rec/gui/fonts/ARCADE_R.TTF"
MIN_FONT_SIZE = 14
class PaginatedList(LiveComponent):
    def __init__(self, items, rect, callback, font_path=FONT, font_size=24):
        self.items = items
        self.x, self.y, self.width, self.height = rect
        self.callback = callback
        self.font_size = font_size
        self.item_buttons = []
        self.current_page = 0
        self.items_per_page = self.calculate_items_per_page(font_size)
        self.total_pages = max(1, -(-len(self.items) // self.items_per_page))  # Ceiling division
        self.create_item_buttons(font_path, font_size)

        self.needs_update = True
        self.up_active = False
        self.down_active = False

    def update_data(self):
        # No data to update
        pass

    def calculate_items_per_page(self, font_size):
        # Use font size for height calculation
        return max(1, self.height // font_size)

    def create_item_buttons(self, font_path, font_size):
        # Create a TextButton for each item
        item_height = font_size
        for i, item in enumerate(self.items):
            y_position = self.y + (i % self.items_per_page) * item_height
            button = TextButton(
                text=item,
                x=self.x,
                y=y_position,
                font_size=font_size,
                callback=lambda item=item: self.callback(item),
                font_path=font_path
            )
            while button.bounding_box[2] > self.width and button.font_size > MIN_FONT_SIZE:
                button.update(new_font_size=button.font_size - 1)
            while button.bounding_box[2] > self.width:
                button.update(new_text=button.text[:-1])
            if i % self.items_per_page == self.items_per_page - 1:
                y_position += button.font_size + 2
            self.item_buttons.append(button)

    def draw(self, draw_context):
        print("ListBrowser draw")
        # Draw the visible items for the current page
        draw_context.rectangle((self.x, self.y, 266, 128), fill=0)
        start_index = self.current_page * self.items_per_page
        end_index = min(start_index + self.items_per_page, len(self.items))

        for button in self.item_buttons[start_index:end_index]:
            button.draw(draw_context)


    def page_up(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.needs_update = True

    def page_down(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.needs_update = True

    def handle_touch(self, eventType, touch_event):
        # Check if touch is on an arrow or an item
        start_index = self.current_page * self.items_per_page
        end_index = min(start_index + self.items_per_page, len(self.items))
        if eventType == "end":
            for button in self.item_buttons[start_index:end_index]:
                if button.is_pressed(touch_event.start_x, touch_event.start_y):
                    button.handle_touch(eventType, touch_event)
                    return
