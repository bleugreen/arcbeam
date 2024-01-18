import os
import time
import subprocess
import redis
from redis_client import RedisClient
import json
from time_mgmt import amt_ns_to_ms

# Publish a message
channel = 'crec'
bundle = {}
in_bundle = False


def monitor_metadata_pipe(pipe_path, redis_client):
    global bundle, in_bundle
    while True:
        if os.path.exists(pipe_path):

            with subprocess.Popen(['/home/dev/shairport-sync-metadata-reader/shairport-sync-metadata-reader'],
                                  stdin=open(pipe_path, 'r'), stdout=subprocess.PIPE) as proc:
                for line in proc.stdout:
                    # Process each line of output and update Redis
                    print(line.decode().strip())
                    process_metadata_line(
                        line.decode().strip(), redis_client)
        else:
            # Wait for some time before checking again if the pipe exists
            time.sleep(5)


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


def process_metadata_line(line, redis_client: RedisClient):
    global bundle, in_bundle
    if line.startswith('XXX'):
        print(f'ERROR: {line}')
        return bundle, in_bundle

    if 'Metadata bundle' in line:
        rtp_id = line.split('"')[1]
        if 'start' in line:
            bundle = {'rtp': rtp_id}
            in_bundle = True
        elif 'end' in line:
            redis_client.publish(bundle_message(bundle))
            bundle = {}
            in_bundle = False
    elif in_bundle:
        key = line.split(':')[0]
        print('IN BUNDLE', line)
        if '"' in line:
            bundle[key] = line.split('"')[1]
        elif ":" in line:
            bundle[key] = line.split(':')[1].strip('. \n')
    elif 'Active State' in line:
        if 'Enter' in line:
            redis_client.set_active(True)
            redis_client.publish(sesh_message('active', True))
        elif 'Exit' in line:
            redis_client.set_active(False)
            redis_client.publish(sesh_message('active', False))
    elif 'Play Session' in line:
        if 'Begin' in line:
            redis_client.set_playing(True)
            redis_client.publish(sesh_message('playing', True))
        elif 'End' in line:
            redis_client.set_playing(False)
            redis_client.publish(sesh_message('playing', False))
    elif 'The AirPlay client at' in line:
        addr = line.split('"')[1]
        if 'has connected' in line:
            redis_client.set_device_addr(addr)
            redis_client.publish(sesh_message('conn', True))
        elif 'has disconnected' in line:
            redis_client.set_device_addr(None)
            redis_client.publish(sesh_message('conn', False))
    elif 'Stream type' in line:
        st = line.split('"')[1]
        redis_client.publish(sesh_message('streamtype', st))
    elif 'frame/time:' in line:
        rtp = int(line.split('"')[1].split('/')[0])
        ss_ns = int(line.split('"')[1].split('/')[1])
        ss_ms = amt_ns_to_ms(ss_ns)
        redis_client.publish(frame_message(rtp, ss_ms))
    elif 'Progress String' in line:
        start, curr, end = map(
            int, line.split('"')[1].split('/'))
        redis_client.publish(prog_message(start, curr, end))
    elif line.startswith('Pause'):
        redis_client.publish(ctl_message('Pause'))
    elif line.startswith('Resume'):
        redis_client.publish(ctl_message('Resume'))
    elif line.startswith('Play'):
        redis_client.publish(ctl_message('Play'))

    else:
        print(line)


if __name__ == "__main__":
    # Configure the Redis client
    redis_client = RedisClient()

    # Path to the metadata pipe
    metadata_pipe_path = '/tmp/shairport-sync-metadata'

    # Start monitoring the metadata pipe
    monitor_metadata_pipe(metadata_pipe_path, redis_client)
