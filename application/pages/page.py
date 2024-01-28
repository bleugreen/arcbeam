class Page:
    def __init__(self):
        """
        Initialize a Page with a collection of UI elements.
        """
        self.elements = []

    def add_elements(self, *elements):
        """
        Add one or more UI elements (like Buttons) to the page.

        :param elements: A list of UI elements to add.
        """
        self.elements.extend(elements)

    def draw(self, drawContext, force_refresh=False):
        """
        Draw the page and all its elements.

        :param drawContext: The drawing context to use for drawing the page and its elements.
        """
        for element in self.elements:
            element.draw(drawContext)

    def handle_touch(self, eventType, touch_event):
        """
        Handle a touch event by delegating it to the appropriate UI element.

        :param eventType: The type of touch event ('start', 'end', etc.).
        :param touch_event: The TouchEvent object.
        """
        for element in self.elements:
            if hasattr(element, 'handle_touch'):
                element.handle_touch(eventType, touch_event)

    def handle_button(self, button_event):
        """
        Handle a button event by delegating it to the appropriate UI element.

        :param button_event: The ButtonEvent object.
        """
        print(f"Page received button event: {button_event.button_name}-{button_event.event_type}")

    def activate(self):
        print("Page activated - Default implementation does nothing")
