import redis
import json

def sesh_message(type: str, value):
    message_dict = {
        'type': type,
        'value': value
    }
    return json.dumps(message_dict)

def bundle_message(bundle: dict):
    message_dict = {
        'type': 'bundle',
        **bundle
    }
    return json.dumps(message_dict)

def frame_message(rtp: int, ms):
    message_dict = {
        'type': 'frame',
        'rtp': rtp,
        'ms': ms
    }
    return json.dumps(message_dict)

def prog_message(start: int, curr: int, end: int):
    message_dict = {
        'type': 'progress',
        'start': start,
        'curr': curr,
        'end': end
    }
    return json.dumps(message_dict)

def ctl_message(cmd):
    message_dict = {
        'type': 'control',
        'cmd': cmd,
    }
    return json.dumps(message_dict)

class RedisClient:
    """
    Client wrapper for managing Shairplay-sync device states using Redis.

    Schema:
    - Device Status (`device:status`): Hash with 'connected', 'active', 'playing' (boolean as 1/0).
    - Device Details (`device:details`): Hash with 'addr', 'name', 'id', 'model', 'mac_addr', expires in 12 hours.
    - Current Song (`song:[page]`): Hash with 'title', 'artist', 'album', 'elapsed', 'length', 'rec_status', 'db_status'.

    Offers methods for setting/getting these fields individually or in bulk, handling boolean and string data types.
    """

    def __init__(self, host='localhost', port=6379, db=0):
        self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def publish(self, line, channel='crec'):
        self.redis.publish(channel, line)

    def set_device_status(self, status_data):
        """ Set multiple device status fields, converting boolean to integer. """
        status_data = {k: 1 if v else 0 for k, v in status_data.items()}
        self.redis.hset("device:status", mapping=status_data)
        self.redis.expire("device:status", 43200)

    def set_device_status_field(self, field, value):
        """ Set a single device status field, converting boolean to integer. """
        self.redis.hset("device:status", field, 1 if value else 0)
        self.redis.expire("device:status", 43200)

    def get_device_status(self):
        return {k: v == '1' for k, v in self.redis.hgetall("device:status").items()}

    def get_device_status_field(self, field):
        return self.redis.hget("device:status", field) == '1'

    def set_device_details(self, details_data):
        """ Set multiple device detail fields with a 12hr expiry. """
        self.redis.hset("device:details", mapping=details_data)
        self.redis.expire("device:details", 43200)

    def set_device_detail_field(self, field, value):
        """ Set a single device detail field with a 12hr expiry. """
        self.redis.hset("device:details", field, value)
        self.redis.expire("device:details", 43200)

    def get_device_details(self):
        return self.redis.hgetall("device:details")

    def get_device_detail_field(self, field):
        return self.redis.hget("device:details", field)

    def set_current_song(self, song_data, page='rec'):
        """ Set multiple current song fields. """
        song_data = {k: "None" if v is None else v for k, v in song_data.items()}
        self.redis.hset(f"song:{page}", mapping=song_data)

    def set_current_song_field(self, field, value, page='rec'):
        """ Set a single current song field. """
        self.redis.hset(f"song:{page}", field, value)

    def get_current_song(self, page='rec'):
        return self.redis.hgetall(f"song:{page}")

    def get_current_song_field(self, field, page='rec'):
        return self.redis.hget(f"song:{page}", field)

    def set_browse(self, field, value):
        """ Set a single current song field. """
        self.redis.hset(f"browser", field, value)
    def get_browse(self, field):
        """ Set a single current song field. """
        return self.redis.hget(f"browser", field)
    def reset_browse(self):
        """ Set a single current song field. """
        self.redis.delete(f"browser")


    def set_rec_time_status(self, device, status):
        self.redis.set(f"rec:{device}:time", status)
    def set_rec_db_status(self, device, state):
        print(f"rec:{device}:db", state)
        status = 'default'
        if state == 'UNKNOWN' or state == 'NEW':
            status = 'new'
        elif state == 'KNOWN':
            status = 'seen'
        elif state == 'SAVED' or state == 'EXPORTED':
            status = 'complete'
        self.redis.set(f"rec:{device}:db", status)

    def reset_song(self):
        """ Clears all stored data related to the current song. """
        self.redis.delete("song:rec", "song:player")
        self.redis.delete("rec:1:time", "rec:1:db", "rec:3:time", "rec:3:db")

    def reset(self):
        """ Clears all stored data related to the device and current song. """
        self.redis.delete("device:status", "device:details", "song:rec", "song:play")
        self.redis.delete("rec:1:time", "rec:1:db", "rec:3:time", "rec:3:db")
