from abc import ABC, abstractmethod

class LiveComponent(ABC):
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @abstractmethod
    def update_data(self):
        """
        Update the component's data. Subclasses should implement this method.
        """
        pass

    @abstractmethod
    def draw(self, drawContext):
        """
        Draw the component on the screen. Subclasses should implement this method.

        :param drawContext: The drawing context to use for drawing the component.
        """
        pass
