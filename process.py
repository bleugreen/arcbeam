import os
import subprocess
import redis
from config import PYTHON_PATH
process = None

def main():
    global process
    redis_client = redis.Redis()
    pubsub = redis_client.pubsub()
    pubsub.subscribe('process')

    def stop_process():
        global process
        if process:
            process.terminate()
            process = None

    for message in pubsub.listen():
        if message['type'] == 'message':
            command = message['data'].decode('utf-8')
            print(f"Received command: {command}")

            if command == 'stop:all':
                stop_process()
                break
            elif 'stop' in command:
                stop_process()
            elif command.startswith('start:'):
                stop_process()
                project_root = os.path.dirname(os.path.abspath(__file__))

                if command == 'start:recorder':
                    process_command = [PYTHON_PATH, '-m', 'recording.recorder']
                elif command == 'start:player':
                    process_command = [PYTHON_PATH, '-m', 'player']
                print(f"Starting process: {process_command}")
                process = subprocess.Popen(process_command, cwd=project_root)

if __name__ == "__main__":
    main()
