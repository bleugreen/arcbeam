from PIL import Image

class Icon:
    def __init__(self, x, y, size, img_path):
        """
        Initialize an icon with coordinates, size, and an image path.

        :param x: The x-coordinate of the top-left corner of the icon.
        :param y: The y-coordinate of the top-left corner of the icon.
        :param size: The size (width and height) of the icon. Icons are square.
        :param img_path: The file path of the icon image.
        """
        self.x = x
        self.y = y
        self.size = size
        self.img_path = img_path
        self.image = self.load_and_resize_image(img_path, size)
        self.has_drawn = False

    def load_and_resize_image(self, img_path, size):
        """
        Load an image from a path and resize it to the specified size.

        :param img_path: The file path of the image.
        :param size: The size to which the image should be resized.
        :return: The resized image.
        """
        with Image.open(img_path) as img:
            resized_img = img.resize((size, size))
            return resized_img

    def draw(self, drawContext):
        """
        Draw the icon on the screen using ImageDraw object.

        :param drawContext: The ImageDraw object to use for drawing the icon.
        """
        if not self.has_drawn:
            for x in range(self.image.width):
                for y in range(self.image.height):
                    pixel = self.image.getpixel((x, y))
                    color = pixel[0]
                    drawContext.point((self.x + x, self.y + y), fill=color)
            self.has_drawn = True
