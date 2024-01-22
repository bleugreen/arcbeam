from .menu import Menu
from ..components import Button, LiveTextBox, PaginatedList
from functools import partial
from .livemenu import LiveMenu

browser_path = "gui/images/browser.png"
BTN_DATA = {
    'back': (266, 1, 30, 30),
    'up': (266, 33, 30, 30),
    'filter': (266, 66, 30, 30),
    'down': (266, 98, 30, 30)
}


class BrowserMenu(LiveMenu):
    def __init__(self, items, rect, level='artist', on_select=None, on_back=None, on_filter=None, img_path=browser_path, button_data=BTN_DATA):
        super().__init__(img_path)
        self.items = items
        self.level = level
        self.list_rect = rect
        self.on_select = on_select
        self.on_back = on_back
        self.on_filter = on_filter
        self.elements = []
        self.current_page = {
            'artist': 0,
            'album': 0,
            'track': 0
        }


    def make_elements(self, button_data=BTN_DATA):
        self.elements = []
        for label, (x, y, w, h) in button_data.items():
            onPress = partial(self.onPress, label)
            button = Button(x, y, w, h, onPress)
            self.elements.append(button)
        on_select = partial(self.on_select, self.level)
        self.page_list = PaginatedList(self.items, self.list_rect, on_select)
        self.page_list.current_page = self.current_page[self.level]
        self.elements.append(self.page_list)

    def update_items(self, items, level='artist'):
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
        super().draw(display, drawContext, force_refresh)
