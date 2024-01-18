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

    def draw(self, drawContext):
        """
        Draw the page and all its elements.

        :param drawContext: The drawing context to use for drawing the page and its elements.
        """
        for element in self.elements:
            element.draw(drawContext)

    def handle_touch(self, touch_x, touch_y):
        print(f"Page received touch at ({touch_x}, {touch_y})")
        """
        Handle a touch event by delegating it to the appropriate UI element.

        :param touch_x: The x-coordinate of the touch.
        :param touch_y: The y-coordinate of the touch.
        """
        for element in self.elements:
            if hasattr(element, 'handle_touch'):
                element.handle_touch(touch_x, touch_y)

    def activate(self):
        print("Page activated - Default implementation does nothing")
