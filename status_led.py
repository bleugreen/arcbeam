import math
import board
import adafruit_dotstar as dotstar
import time

# while True:
#     for i in range(64):
#         dots[i] = (0, 255, 0)
#         time.sleep(0.02)
#     for i in range(64):
#         dots[i] = (0, 0, 0)
#         time.sleep(0.02)


SESH_IDX1 = 3
SESH_IDX2 = 4

RUN_IDX = 2
CONN_IDX = 3
ACTIVE_IDX = 4
PLAY_IDX = 5

REC1_IDX = 8
REC2_IDX = 15
DB1_IDX = 16
DB2_IDX = 23
PROG_START = 32
DRIVE_START = 56
NUM_LEDS = 64

DRIVE_IDX = 56

color_map = {
    'Start': (0, 0, 20),
    'Good': (0, 10, 0),
    'Active': (0, 20, 10),
    'Done': (0, 10, 20),
    'Stop': (10, 0, 0),
    'Error': (120, 0, 0),
    'Save': (20, 0, 40),
    'Elapsed': (0, 50, 10),
    'Remaining':  (0, 0, 10)
}

db_color_map = {
    'NEW': (0, 0, 15),
    'KNOWN': (15, 10, 0),
    'SAVED': (0, 20, 0),
    'EXPORTED': (10, 0, 20),
    'UNKNOWN': (10, 0, 0)
}


class StatusLed:
    def __init__(self):
        self.leds = dotstar.DotStar(board.SCK, board.MOSI, NUM_LEDS,
                                    brightness=0.1, auto_write=False, )
        self.colors = [(0, 0, 0) for _ in range(NUM_LEDS)]

    def update(self):
        for idx, color in enumerate(self.colors):
            self.leds[idx] = color
        self.leds.show()

    def turn_off(self, update=True):
        self.colors = [(0, 0, 0) for _ in range(NUM_LEDS)]
        if update:
            self.update()

    def turn_off_rec(self, device, update=True):
        rec_idx = REC1_IDX if device == 1 else REC2_IDX
        db_idx = DB1_IDX if device == 1 else DB2_IDX
        self.colors[rec_idx] = (0, 0, 0)
        self.colors[db_idx] = (0, 0, 0)
        if update:
            self.update()

    def set_rec_status(self, device, status, update=False):
        idx = REC1_IDX if device == 1 else REC2_IDX
        self.colors[idx] = color_map.get(status, (0, 0, 0))
        if update:
            self.update()

    def set_drive_status(self, status, update=False):
        self.colors[DRIVE_IDX] = color_map.get(status, (0, 0, 0))
        if update:
            self.update()

    def set_db_status(self, device, status, update=False):
        idx = DB1_IDX if device == 1 else DB2_IDX
        self.colors[idx] = db_color_map.get(status, (0, 0, 0))
        if update:
            self.update()

    def set_sesh_status(self, status, update=False):
        self.colors[SESH_IDX1] = color_map.get(status, (0, 0, 0))
        self.colors[SESH_IDX2] = color_map.get(status, (0, 0, 0))
        if update:
            self.update()

    def set_progress(self, progress, update=False):
        print(f'prog == {progress}')
        if progress < 0:
            for idx in range(PROG_START, PROG_START+9):
                self.colors[idx] = (0, 0, 0)
        else:
            prog = (min(1, progress))
            num_full = math.floor(8*prog)
            partial = (8*prog) - num_full
            start = PROG_START
            idx = start
            for _ in range(num_full):
                self.colors[idx] = color_map.get('Elapsed')
                idx += 1
            if progress < 1:
                self.colors[idx] = (0, max(int(40*partial), 10), 10)
                idx += 1
                while idx < start+8:
                    self.colors[idx] = color_map.get('Remaining')
                    idx += 1
        if update:
            self.update()
