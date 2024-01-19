class Button:
    def __init__(self, x, y, width, height, onPress, duration=0.01):
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
        self.duration = duration

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

    def handle_touch(self, eventType, touch_event):
        """
        Handle a touch event. Calls different methods based on the touch event type.

        :param eventType: The type of touch event ('start', 'end', etc.).
        :param touch_event: The TouchEvent object.
        """
        if eventType == 'start':
            self.handle_start(touch_event)
        elif eventType == 'end':
            self.handle_end(touch_event)
        # Add more conditions for other event types as needed

    def handle_start(self, touch_event):
        if self.is_pressed(touch_event.start_x, touch_event.start_y):
            print(f"Button touch start at ({touch_event.start_x}, {touch_event.start_y})")
            # Add logic for start touch here, e.g., highlighting the button

    def handle_end(self, touch_event):
        if self.is_pressed(touch_event.end_x, touch_event.end_y):
            print(f"Button touch end at ({touch_event.end_x}, {touch_event.end_y})")
            # Trigger the onPress action if touch ends within the button
            if touch_event.duration >= self.duration:
                self.onPress()
            # Add additional logic for end touch here if needed
