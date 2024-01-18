from PIL import ImageFont
import time
from eink import EInkDisplay
import logging

class EInkDisplayApp:
    def __init__(self):
        self.display = EInkDisplay(handle_touch=self.handle_touch_event)  # Your E-Ink display class
        # self.display.epd.sleep()
        self.touch_count = 0

    def handle_touch_event(self, touch_x, touch_y):
        logging.info(f"APP TOUCH event detected at ({touch_x}, {touch_y})")
        self.touch_count += 1

    def update_display(self, text):
        def draw_on_image(draw):
            draw.rectangle((0, 0, self.display.width, self.display.height), fill=255)  # Clear the screen
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
            # Draw centered text
            draw.text((20, 20), text, font=font, fill=0)

        self.display.draw(draw_on_image)

    def run(self):
        while True:
            # Example: Update display with current time every minute
            current_time = time.strftime("%H:%M:%S", time.localtime())
            # self.display.epd.init()
            self.update_display(f"Current Time: {current_time}\nTouch count: {self.touch_count}")
            # self.display.epd.sleep()
            time.sleep(3)

app = EInkDisplayApp()
try:
    app.run()
finally:
    app.display.stop()