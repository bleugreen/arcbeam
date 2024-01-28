import logging
import os
import sys
import threading
import time
from PIL import Image, ImageDraw
from .touchevent import TouchEvent

libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)
from TP_lib import epd2in9_V2, icnt86

FULL_REFRESH_INTERVAL = 180  # seconds
TOUCH_EVENT_TIMEOUT = 0.3  # seconds

# Logger setup
logging.basicConfig(level=logging.DEBUG)
flag_t = 1

class EInkDisplay:
    def __init__(self, handle_touch=None):
        self.width = 296
        self.height = 128
        self.epd = epd2in9_V2.EPD_2IN9_V2()
        self.tp = icnt86.INCT86()
        self.ICNT_Dev = icnt86.ICNT_Development()
        self.ICNT_Old = icnt86.ICNT_Development()
        self.flag_t = 1
        if handle_touch is None:
            self.handle_touch = self.handle_touch_event
        else:
            self.handle_touch = handle_touch
        self.init_display()
        self.start_touch_thread()
        self.image = Image.new('1', (self.width, self.height), 0)  # Initialize a blank image
        self.drawImage = ImageDraw.Draw(self.image)  # Create a drawing object
        self.lastFullRefresh = time.time()
        self.active_touches = {}
        self.is_sleeping = False

    def init_display(self):
        logging.info("Initializing and clearing the display")
        self.epd.init()
        self.tp.ICNT_Init()
        self.epd.Clear(0xFF)
        self.has_drawn = False

    def start_touch_thread(self):
        self.t1 = threading.Thread(target=self.pthread_irq)
        self.t1.setDaemon(True)
        self.t1.start()

    def pthread_irq(self):
        logging.info("Touch thread running")
        self.active_touches:dict[str,TouchEvent] = {}
        while self.flag_t == 1:
            if self.tp.digital_read(self.tp.INT) == 0:
                self.ICNT_Dev.Touch = 1
                self.tp.ICNT_Scan(self.ICNT_Dev, self.ICNT_Old)
                print('read')
                for i in range(self.ICNT_Dev.TouchCount):  # Assuming 5 is the max number of touches
                    touch_id = i  # Unique identifier for each touch
                    if self.ICNT_Dev.P[i] > 0:
                        touch_x, touch_y = self.ICNT_Dev.X[i], self.ICNT_Dev.Y[i]
                        if touch_id not in self.active_touches:
                            self.active_touches[touch_id] = TouchEvent.create(touch_x, touch_y)
                            self.handle_touch('start', self.active_touches[touch_id])
                        else:
                            self.active_touches[touch_id].update(touch_x, touch_y)
                    else:
                        if touch_id in self.active_touches:
                            self.active_touches[touch_id].end()
                            touch_event = self.active_touches[touch_id]
                            self.handle_touch('end', touch_event)
                            del self.active_touches[touch_id]
                        else:
                            touch_x, touch_y = self.ICNT_Dev.X[i], self.ICNT_Dev.Y[i]
                            event = TouchEvent.create(touch_x, touch_y)
                            self.handle_touch('start', event)
                            event.end()
                            self.handle_touch('end', event)
            else:
                # Reset the touch state if no touch is detected
                self.ICNT_Dev.Touch = 0
                current_time = time.time()
                for touch_id, touch_info in list(self.active_touches.items()):
                    if current_time - touch_info.last_time() > TOUCH_EVENT_TIMEOUT:
                        touch_info.end()
                        self.handle_touch('end', touch_info)
                        del self.active_touches[touch_id]
            time.sleep(0.01)
        logging.info("Touch thread: exiting")

    def handle_touch_start(self, start_x, start_y):
        logging.info(f"Touch start event detected at ({start_x}, {start_y})")

    def handle_touch_end(self, touch_event: TouchEvent):
        logging.info(f"Touch end event detected from ({touch_event.start_x}, {touch_event.start_y}) to ({touch_event.end_x}, {touch_event.end_y}) Duration: {touch_event.duration}")

    def handle_touch_event(eventType, touch_event):
        logging.info(f"{eventType} :: {touch_event})")

    def draw(self, partial=True, static=False):
        """
        Draw the current image on the display, handling full or partial refresh.

        :param partial: Whether to do a partial refresh.
        :param static: Whether the screen is static (to put display to sleep).
        """
        if self.is_sleeping:
            self.wake()
        buffer = self.epd.getbuffer(self.image)
        if partial:
            self.epd.display_Partial(buffer)
            self.epd.ReadBusy()
        else:
            self.epd.display_Base(buffer)
            self.epd.ReadBusy()


        if static:
            self.sleep()

    def full_refresh(self):
        # Redraw the entire screen from scratch
        self.image = Image.new('1', (self.width, self.height), 0)
        self.drawImage = ImageDraw.Draw(self.image)
        self.epd.display_Base(self.epd.getbuffer(self.image))

    def partial_refresh(self, img):
        self.epd.display_Partial_Wait(self.epd.getbuffer(img))

    def sleep(self):
        self.epd.sleep()
        self.is_sleeping = True

    def wake(self):
        self.epd.init()
        self.is_sleeping = False

    def clear(self):
        self.image.paste(Image.new('1', (self.width, self.height), 0))
        self.has_drawn = False

    def stop(self):
        self.flag_t = 0
        if not self.is_sleeping:
            self.sleep()
        if self.t1.is_alive():
            self.t1.join(timeout=10)
            if self.t1.is_alive():
                logging.warning("Touch thread did not terminate.")
        self.epd.Dev_exit()
