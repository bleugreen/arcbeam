import redis
from threading import Thread
import json


def listen_to_redis():
    r = redis.Redis(host='localhost', port=6379, db=0)
    pubsub = r.pubsub()
    pubsub.subscribe('crec')
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'].decode())
            print('-----'*10)
            for key in data.keys():
                print(f'{key:>10.10} = {data[key]}')


# Run the listener in a separate thread
listener_thread = Thread(target=listen_to_redis)
listener_thread.start()
