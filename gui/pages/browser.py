from .menu import Menu
from ..components import Button, LiveTextBox, PaginatedList
from functools import partial
from .livemenu import LiveMenu
from config import LIB_PATH
import os

browser_path = "gui/images/browser.png"
BTN_DATA = {
    'back': (266, 1, 30, 30),
    'up': (266, 33, 30, 30),
    'filter': (266, 66, 30, 30),
    'down': (266, 98, 30, 30)
}


class BrowserMenu(LiveMenu):
    def __init__(self, items, rect, get_data=None, level='artist', on_select=None, on_back=None, on_filter=None, img_path=browser_path, button_data=BTN_DATA):
        super().__init__(img_path)
        self.items = items
        self.level = level
        self.making_elements = False
        self.list_rect = rect
        self.on_select = on_select
        self.on_back = on_back
        self.on_filter = on_filter
        self.get_data = get_data
        self.elements = []
        self.current_page = {
            'artist': 0,
            'album': 0,
            'track': 0
        }

    def make_elements(self, button_data=BTN_DATA):
        self.making_elements = True
        self.elements = []
        for label, (x, y, w, h) in button_data.items():
            onPress = partial(self.onPress, label)
            button = Button(x, y, w, h, onPress)
            self.elements.append(button)
        on_select = partial(self.on_select, self.level)
        self.page_list = PaginatedList(self.items, self.list_rect, on_select)
        self.page_list.current_page = self.current_page[self.level]
        self.page_list.needs_update = True
        self.page_list.update_data()
        self.elements.append(self.page_list)
        self.making_elements = False

    def navigate_to_match(self, filter_text):
        filter_text_lower = filter_text.lower()

        # Find the index of the first item that starts with or comes after the filter text
        matching_index = next((i for i, item in enumerate(self.items) if item.lower() >= filter_text_lower), None)

        if matching_index is not None:
            print(f"First matching index: {matching_index}")
            items_per_page = self.page_list.items_per_page
            new_page = matching_index // items_per_page
            print(f"Moving from page {self.page_list.current_page} to page {new_page}")
            self.current_page[self.level] = new_page
            self.page_list.current_page = new_page  # Update current page of PaginatedList
            self.make_elements()



    def activate(self):
        self.has_drawn = False
        self.items = self.get_data(self.level)
        self.make_elements()
        super().activate()

    def update_items(self, items, level='artist'):
        if level != self.level:
            self.level = level
        self.items = items
        self.make_elements()


    def onPress(self, label):
        # Placeholder for button press logic
        print(f"Button {label} pressed")
        if label == 'back':
            print("Back pressed")
            self.on_back(self.level)
            self.current_page[self.level] = 0
        elif label == 'up':
            print("Up pressed")
            self.page_list.page_up()
            self.current_page[self.level] = self.page_list.current_page
        elif label == 'filter':
            print("Filter pressed")
            self.on_filter()
        elif label == 'down':
            print("Down pressed")
            self.page_list.page_down()
            self.current_page[self.level] = self.page_list.current_page

    def draw(self, display, drawContext, force_refresh=False):
        if not self.making_elements:
            super().draw(display, drawContext, force_refresh)
