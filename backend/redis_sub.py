import threading
import redis
import time
import logging

logging.basicConfig(level=logging.INFO)

class RedisSubscriber:
    def __init__(self, channel, callback, sleep_interval=0.2, start_now=True, host='localhost', port=6379, db=0):
        self.channel = channel
        self.callback = callback
        self.sleep_interval = sleep_interval
        self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self.pubsub.subscribe(self.channel)
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.listen)
        if start_now:
            self.thread.start()

    def start(self):
        if not self.thread.is_alive():
            self.thread.start()

    def listen(self):
        while not self.stop_event.is_set():
            message = self.pubsub.get_message()
            if message and message['type'] == 'message':
                self.callback(message['data'])
            else:
                time.sleep(self.sleep_interval)  # Adjust sleep time as needed

    def stop(self):
        logging.info(f"Stopping {self.channel} thread...")
        self.stop_event.set()
        self.thread.join(timeout=10)
        if self.thread.is_alive():
            logging.warn(f"Warning: {self.channel} thread did not terminate.")

    # Optional: Destructor to ensure cleanup
    def __del__(self):
        self.stop()
