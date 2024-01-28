import os
import subprocess
import logging
from backend import RedisSubscriber, publish
from config import PYTHON_PATH
import time
import json

logging.basicConfig(level=logging.INFO)

class ProcessManager:
    def __init__(self):
        self.process = None
        self.subscriber = RedisSubscriber('process', self.handle_message, start_now=False)
        self.curr_process = None
    def start(self):
        self.subscriber.start()
        logging.info(f"Process manager started. {self.subscriber.thread.is_alive()}")

    def stop_process(self):
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
                logging.info("Process terminated gracefully.")
            except subprocess.TimeoutExpired:
                self.process.kill()
                logging.warning("Process had to be killed.")
            self.process = None

    def handle_message(self, command):
        logging.info(f"Received command: {command}")
        if command == 'stop:all':
            self.stop()
        elif 'stop' in command:
            if self.curr_process == 'player':
                publish('player', json.dumps({'command': 'stop'}))
                time.sleep(0.2)
            self.stop_process()
        elif command.startswith('start:'):
            self.stop_process()
            project_root = os.path.dirname(os.path.abspath(__file__))
            process_command = []
            if command == 'start:recorder':
                self.curr_process = 'recorder'
                process_command = [PYTHON_PATH, 'recording/recorder.py']
            elif command == 'start:player':
                self.curr_process = 'player'
                process_command = [PYTHON_PATH, '-m', 'player']
            if process_command:
                logging.info(f"Starting process: {process_command}")
                self.process = subprocess.Popen(process_command, cwd=project_root)

    def stop(self):
        self.stop_process()
        self.subscriber.stop()

if __name__ == "__main__":
    manager = ProcessManager()
    try:
        print("Starting process manager...")
        manager.start()
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        manager.stop()
