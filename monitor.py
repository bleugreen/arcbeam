import os
import time
import subprocess
import redis

# Publish a message
channel = 'crec'


def monitor_metadata_pipe(pipe_path, redis_client):
    while True:
        if os.path.exists(pipe_path):
            with subprocess.Popen(['/home/dev/shairport-sync-metadata-reader/shairport-sync-metadata-reader'],
                                  stdin=open(pipe_path, 'r'), stdout=subprocess.PIPE) as proc:
                for line in proc.stdout:
                    # Process each line of output and update Redis
                    process_metadata_line(line.decode(), redis_client)
        else:
            # Wait for some time before checking again if the pipe exists
            time.sleep(5)


def process_metadata_line(line, redis_client):
    # Implement the logic to process each line and update Redis
    # Example: redis_client.set('key', 'value')
    if 'Enter Active' in line:
        redis_client.set('active', 'true')
    elif 'Exit Active' in line:
        redis_client.set('active', 'false')
    redis_client.publish(channel, line)


def main():
    # Configure the Redis client
    redis_client = redis.Redis(host='localhost', port=6379, db=0)

    # Path to the metadata pipe
    metadata_pipe_path = '/tmp/shairport-sync-metadata'

    # Start monitoring the metadata pipe
    monitor_metadata_pipe(metadata_pipe_path, redis_client)


if __name__ == "__main__":
    main()
