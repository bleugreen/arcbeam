from .menu import Menu
from ..components import Button, LiveTextBox
from functools import partial
from .livemenu import LiveMenu

keyboard_path = "gui/images/keyboard.png"
BTN_DATA = {
    'A': (0, 30, 33, 22), 'B': (36, 30, 32, 22), 'C': (74, 30, 32, 22),
    'D': (111, 30, 32, 22), 'E': (149, 30, 32, 22), 'F': (187, 30, 32, 22),
    'G': (225, 30, 32, 22), 'H': (0, 53, 33, 22), 'I': (36, 53, 32, 22),
    'J': (74, 53, 32, 22), 'K': (111, 53, 32, 22), 'L': (149, 53, 32, 22),
    'M': (187, 53, 32, 22), 'N': (225, 53, 32, 22), 'O': (0, 76, 33, 22),
    'P': (36, 76, 32, 22), 'Q': (74, 76, 32, 22), 'R': (111, 76, 32, 22),
    'S': (149, 76, 32, 22), 'T': (187, 76, 32, 22), 'U': (225, 76, 32, 22),
    'V': (41, 99, 32, 22), 'W': (76, 99, 32, 22), 'X': (112, 99, 32, 22),
    'Y': (147, 99, 32, 22), 'Z': (182, 99, 32, 22),
    'back': (263, 29, 32, 30), 'cancel': (263, 61, 32, 30), 'submit': (263, 95, 32, 30)
}


class KeyboardMenu(LiveMenu):
    def __init__(self, on_submit, on_cancel, img_path="gui/images/keyboard.png", button_data=BTN_DATA):
        super().__init__(img_path)
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.elements = []
        self.text_state=""
        for label, (x, y, w, h) in button_data.items():
            onPress = partial(self.onPress, label)
            button = Button(x, y, w, h, onPress)
            self.elements.append(button)
        self.text_box = LiveTextBox(6, 4, 242, 22, self.get_text_state)
        self.elements.append(self.text_box)

    def onPress(self, label):
        # Placeholder for button press logic
        print(f"Button {label} pressed")
        if label == 'back':
            self.text_state = self.text_state[:-1]
        # Handle submit or cancel, perform the necessary actions
        elif label in ['cancel', 'submit']:
            self.handle_special_keys(label)
        # Handle character input
        else:
            self.text_state += label
        print(f"Text state: {self.text_state}")
        # Update the text box to reflect changes
        self.text_box.update_data()

    def draw(self, display, drawContext, force_refresh=False):
        super().draw(display, drawContext, force_refresh)

    def get_text_state(self):
        # Return the current text state for the LiveTextBox
        return self.text_state

    def handle_special_keys(self, label):
        # Placeholder for handling special keys
        if label == 'cancel':
            self.text_state = ""
            self.on_cancel()
        elif label == 'submit':
            self.on_submit(self.text_state)
            self.text_state = ""
        self.text_box.update_data()