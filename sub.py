import redis
from threading import Thread


def listen_to_redis():
    r = redis.Redis(host='localhost', port=6379, db=0)
    pubsub = r.pubsub()
    pubsub.subscribe('crec')
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    for message in pubsub.listen():
        if message['type'] == 'message':
            print(f"Received: {message['data'].decode()}")
            print(redis_client.get('active'))


# Run the listener in a separate thread
listener_thread = Thread(target=listen_to_redis)
listener_thread.start()
