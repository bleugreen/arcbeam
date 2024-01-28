from PIL import Image

class LiveIcon:
    def __init__(self, x, y, size, img_path, update_function, function_args=()):
        """
        Initialize a live icon with coordinates, size, an image path, and an update function.

        :param x: The x-coordinate of the top-left corner of the icon.
        :param y: The y-coordinate of the top-left corner of the icon.
        :param size: The size (width and height) of the icon. Icons are square.
        :param img_path: The initial file path of the icon image.
        :param update_function: A function that updates the image path.
        :param function_args: Arguments to pass to the update function.
        """
        self.x = x
        self.y = y
        self.size = size
        self.update_function = update_function
        self.function_args = function_args
        self.img_path = img_path
        self.image = self.load_and_resize_image(img_path, size)
        self.needs_update = False

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

    def update_data(self):
        """
        Update the icon's image based on the update function and its arguments.
        """
        new_img_path = self.update_function(*self.function_args)
        if new_img_path != self.img_path:
            self.img_path = new_img_path
            self.image = self.load_and_resize_image(new_img_path, self.size)
            self.needs_update = True

    def draw(self, drawContext):
        """
        Draw the icon on the screen using ImageDraw object.

        :param drawContext: The ImageDraw object to use for drawing the icon.
        """
        for x in range(self.image.width):
            for y in range(self.image.height):
                pixel = self.image.getpixel((x, y))
                color = pixel[0]
                drawContext.point((self.x + x, self.y + y), fill=color)
