class Button:
    def __init__(self, x, y, width, height, onPress):
        """
        Initialize a button with coordinates, dimensions, and an onPress callback.

        :param x: The x-coordinate of the top-left corner of the button.
        :param y: The y-coordinate of the top-left corner of the button.
        :param width: The width of the button.
        :param height: The height of the button.
        :param onPress: A callback function that is called when the button is pressed.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.onPress = onPress

    def draw(self, drawContext):
        """
        Draw the button on the screen.

        :param drawContext: The drawing context to use for drawing the button.
        """
        # Draw the button rectangle (outline or filled as needed)
        drawContext.rectangle((self.x, self.y, self.x + self.width, self.y + self.height), outline=0, fill=None)
        # Additional drawing code (like text) can be added here

    def is_pressed(self, touch_x, touch_y):
        """
        Check if the button is pressed based on touch coordinates.

        :param touch_x: The x-coordinate of the touch.
        :param touch_y: The y-coordinate of the touch.
        :return: True if the button is pressed, False otherwise.
        """
        return (self.x <= touch_x <= self.x + self.width and
                self.y <= touch_y <= self.y + self.height)

    def handle_touch(self, touch_x, touch_y):
        """
        Handle a touch event. Calls the onPress callback if the button is pressed.

        :param touch_x: The x-coordinate of the touch.
        :param touch_y: The y-coordinate of the touch.
        """
        if self.is_pressed(touch_x, touch_y):
            print(f"Button received touch at ({touch_x}, {touch_y})")
            self.onPress()
