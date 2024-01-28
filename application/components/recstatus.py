from . import LiveIcon, LiveComponent

class RecStatusBar(LiveComponent):
    def __init__(self, x, y, size, redis_client, device_id=1, margin=2):
        """
        Initialize the RecStatusBar with starting coordinates and size for icons.

        :param x: The x-coordinate for the starting position of the first icon.
        :param y: The y-coordinate for the position of the icons.
        :param size: The size of each icon.
        :param redis_client: An instance of a Redis client.
        """
        self.redis_client = redis_client
        self.device_id = device_id
        self.x = x
        self.y = y
        self.size = size
        self.margin = margin
        self.icons = [
            LiveIcon(x, y, size, self.get_icon_path(f'rec:{self.device_id}:time'), self.update_status, (f'rec:{self.device_id}:time',)),
            LiveIcon(x + size + margin, y, size, self.get_icon_path(f'rec:{self.device_id}:db'), self.update_status, (f'rec:{self.device_id}:db',)),
        ]
        self.needs_update = False


    def get_icon_path(self, key):
        """
        Get the initial icon path based on the current value of the given Redis key.

        :param key: The Redis key.
        :return: The file path of the icon image.
        """
        status = self.redis_client.get(key)
        return f"gui/images/icons/inv/{status}.png" if status else "gui/images/icons/inv/default.png"

    def update_status(self, key):
        """
        Fetch the latest status from Redis and return the corresponding icon path.

        :param key: The Redis key.
        :return: The file path of the new icon image.
        """
        status = self.redis_client.get(key)
        return f"gui/images/icons/inv/{status}.png" if status else "gui/images/icons/inv/default.png"

    def update_data(self):
        """
        Update data for each icon.
        """
        for icon in self.icons:
            icon.update_data()
            if icon.needs_update:
                self.needs_update = True

    def draw(self, drawContext):
        """
        Draw each icon in the status bar.

        :param drawContext: The ImageDraw object to use for drawing the icons.
        """
        drawContext.rectangle((self.x, self.y,self.x+ 2*self.size + self.margin, self.y+self.size), fill=0)
        for icon in self.icons:
            icon.draw(drawContext)
            icon.needs_update = False
