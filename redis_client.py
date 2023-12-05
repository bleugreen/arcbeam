import redis


class RedisClient:
    def __init__(self):
        # Initialize Redis connection
        self.redis = redis.Redis(host='localhost', port=6379, db=0)
        self.current_device_addr = self.redis.get('device').decode()

    def set_active(self, active):
        # Set the 'active' key to true or false
        self.redis.set('active', 'true' if active else 'false')

    def is_active(self):
        # Get the 'active' key
        return self.redis.get('active') == b'true'

    def set_playing(self, playing):
        # Set the 'playing' key to true or false
        self.redis.set('playing', 'true' if playing else 'false')

    def is_playing(self):
        # Get the 'playing' key
        return self.redis.get('playing') == b'true'

    def get_device_addr(self):
        # Get the 'playing' key
        return self.redis.get('device').decode()

    def set_device_addr(self, device_addr):
        # Set the 'device' key to the device address or 'none'
        self.redis.set('device', device_addr if device_addr else 'none')

    def set_device_field(self, field, value):
        # Set a field for the current device
        addr = self.get_device_addr()
        if addr is not 'none':
            self.redis.hset(f'device:{addr}', field, value)
        else:
            raise ValueError("No current device address set")

    def get_device(self):
        # Get all fields for the current device
        addr = self.get_device_addr()
        if addr is not 'none':
            return self.redis.hgetall(f'device:{addr}')
        else:
            return None
