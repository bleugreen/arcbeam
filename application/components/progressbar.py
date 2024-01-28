from . import LiveComponent


class ProgressBar(LiveComponent):
    def __init__(self, x, y, width, height, bg_color, fg_color, circle_radius, update_function, function_args=()):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.circle_radius = circle_radius
        self.update_function = update_function
        self.function_args = function_args
        self.progress = 0.0
        self.needs_update = True

    def update_data(self):
        # Fetch progress data using the provided function and arguments
        new_progress = self.update_function(*self.function_args)
        if new_progress is not None and 0 <= float(new_progress) <= 1:
            if abs(float(new_progress) - self.progress) > 0.05:
                self.progress = float(new_progress)
                self.needs_update = True
                print(f"Progress updated to {self.progress}")

    def draw(self, drawContext):
        # Draw the background rectangle
        drawContext.rectangle((self.x, self.y, self.x + self.width, self.y + self.height), fill=self.bg_color)

        # Calculate the width of the foreground rectangle based on the progress
        fg_width = self.progress * (self.width-2*self.circle_radius)
        print(f"Progress: {self.progress}, fg_width: {fg_width}")
        circle_radius = (self.height-8)//2
        # Draw the foreground rectangle
        x0 = self.x+circle_radius
        y0 = self.y + 4
        x1 = min(self.x + self.width-circle_radius, x0 + fg_width)
        y1 = self.y + self.height - 4
        drawContext.rectangle((x0, y0, x1, y1), fill=self.fg_color)

        # Draw the foreground circle centered on the right edge of the fg rectangle
        circle_x = self.x
        circle_y = self.y + self.height / 2
        drawContext.ellipse((circle_x , circle_y - circle_radius, circle_x + 2*circle_radius, circle_y + circle_radius), fill=self.fg_color)
        circle_x = x1 - circle_radius

        drawContext.ellipse((circle_x , circle_y - circle_radius, circle_x + 2*circle_radius, circle_y + circle_radius), fill=self.fg_color)
