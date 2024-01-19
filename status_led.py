import math
import board
import adafruit_dotstar as dotstar
import time
import redis
import json

NUM_LEDS = 64

idx_map = {
    'sesh1': 3,
    'sesh2': 4,
    'run': 2,
    'active': 3,
    'play': 4,
    'conn': 5,
    'rec1': 8,
    'db1': 16,
    'rec2': 15,
    'db2': 23,
    'prog_start': 32,
    'drive': 56,
    'clip1': 59,
    'clip2': 60
}

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

color_key = 'statuscolors'


class StatusLed:
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, db=0)

    def _set_all(self, color):
        color_list = [color] * NUM_LEDS
        self.r.delete(color_key)

        # Serialize and store each tuple
        for tup in color_list:
            self.r.rpush(color_key, json.dumps(tup))

    def set_disabled(self, disabled: bool = False):
        self.r.set(f'{color_key}:disabled', 'true' if disabled else 'false')
        self.r.publish('led', 'update')

    def get_disabled(self):
        return 'true' in self.r.get(f'{color_key}:disabled').decode()

    def toggle_disabled(self):
        is_disabled = self.get_disabled()
        self.set_disabled(not is_disabled)

    def _set_idx(self, index, color):
        serialized_value = json.dumps(color)
        # Update the tuple at the specified index
        self.r.lset(color_key, index, serialized_value)

    def get_curr_val(self, name):
        return json.loads(self.r.lindex(color_key, idx_map.get(name)))

    def _get(self):
        """
        Retrieve the entire list of tuples from Redis.
        """
        # Deserialize each tuple in the list
        return [json.loads(tup) for tup in self.r.lrange(color_key, 0, -1)]

    def show(self, leds):
        colors = self._get()
        for idx, color in enumerate(colors):
            leds[idx] = color
        # leds.show()

    def update(self):
        pass
        # self.r.publish('led', 'update')

    def turn_off(self, update=True):
        self._set_all((0, 0, 0))
        if update:
            self.update()

    def turn_off_rec(self, device, update=True):
        if device == 1:
            rec_idx = idx_map.get('rec1')
            db_idx = idx_map.get('db1')
        else:
            rec_idx = idx_map.get('rec2')
            db_idx = idx_map.get('db2')

        self._set_idx(rec_idx, (0, 0, 0))
        self._set_idx(db_idx, (0, 0, 0))
        if update:
            self.update()

    def set_rec_status(self, device, status, update=False):
        idx = idx_map.get('rec1') if device == 1 else idx_map.get('rec2')
        self._set_idx(idx, color_map.get(status, (0, 0, 0)))
        if update:
            self.update()

    def set_drive_status(self, status, update=False):
        self._set_idx(idx_map.get('drive'), color_map.get(status, (0, 0, 0)))
        if update:
            self.update()

    def set_db_status(self, device, status, update=False):
        idx = idx_map.get('db1') if device == 1 else idx_map.get('db2')
        self._set_idx(idx, db_color_map.get(status, (0, 0, 0)))
        if update:
            self.update()

    def set_sesh_status(self, status, update=False):
        self._set_idx(idx_map.get('sesh1'), color_map.get(status, (0, 0, 0)))
        self._set_idx(idx_map.get('sesh2'), color_map.get(status, (0, 0, 0)))
        if update:
            self.update()

    def set_clip_status(self, status, update=False):
        self._set_idx(idx_map.get('clip1'), color_map.get(status, (0, 0, 0)))
        self._set_idx(idx_map.get('clip2'), color_map.get(status, (0, 0, 0)))
        if update:
            self.update()

    def set_session_status(self, run, conn, active, play, update=False):
        self._set_idx(idx_map.get('run'),
                      color_map['Done'] if run else color_map['Stop'])
        self._set_idx(idx_map.get('conn'), color_map['Done']
                      if conn else color_map['Stop'])
        self._set_idx(
            idx_map.get('active'), color_map['Good'] if active else color_map['Stop'])
        self._set_idx(idx_map.get('play'), color_map['Good']
                      if play else color_map['Stop'])
        if update:
            self.update()

    def set_progress(self, progress, update=False):
        print(f'prog == {progress}')
        start = idx_map.get('prog_start')
        if progress < 0:
            for idx in range(start, start+9):
                self._set_idx(idx, (0, 0, 0))
        else:
            prog = (min(1, progress))
            num_full = math.floor(8*prog)
            partial = (8*prog) - num_full
            idx = start
            for _ in range(num_full):
                self._set_idx(idx, color_map.get('Elapsed'))
                idx += 1
            if progress < 1:
                self._set_idx(idx, (0, max(int(40*partial), 10), 10))
                idx += 1
                while idx < start+8:
                    self._set_idx(idx, color_map.get('Remaining'))
                    idx += 1
        if update:
            self.update()


if __name__ == '__main__':
    leds = dotstar.DotStar(board.SCK, board.MOSI, NUM_LEDS,
                           brightness=0.1, auto_write=False)
    status_led = StatusLed()

    try:
        status_led._set_all((0, 0, 0))
        status_led.set_disabled(False)
        is_blank = True
        status_led.show(leds)
        r = redis.Redis(host='localhost', port=6379, db=0)
        pubsub = r.pubsub()
        pubsub.subscribe('led')
        for message in pubsub.listen():
            if message['type'] == 'message':
                line = message['data'].decode()
                if 'update' in line:
                    if status_led.get_disabled():
                        if not is_blank:
                            # print('disabling')
                            leds.fill((0, 0, 0))
                            leds.show()
                            is_blank = True
                        # else:
                        #     print('already disabled')
                    else:
                        # print('enabled')
                        status_led.show(leds)
                        is_blank = False

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        leds.fill((0, 0, 0))
