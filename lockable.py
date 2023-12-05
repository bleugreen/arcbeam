import time


class LockableValue:
    def __init__(self, initial_value=None, verbose=False, timeout=15, repeat_lock=True):
        self.value = initial_value
        self.repeat_lock = repeat_lock
        self.verbose = verbose
        self.locked = False
        self.timeout = timeout
        self.updated_at = time.time()

    def update(self, new_value):
        current_time = time.time()
        if new_value is not None:
            # Check if the timeout has been exceeded
            if current_time - self.updated_at > self.timeout and self.value is not None:
                if not self.locked:
                    self.locked = True
                    if self.verbose:
                        print(
                            f"Timeout exceeded. Value locked at: {self.value}")
                return

            if self.locked:
                if self.verbose:
                    print(
                        f"Value ({self.value}) is locked. Update to {new_value} not allowed.")
                return

            if self.value == new_value:
                if self.verbose:
                    print(f"No change in value ({self.value}). Locking.")
                if self.repeat_lock:
                    self.locked = True
            else:
                if self.verbose:
                    print(f"Value updated to: {new_value} from: {self.value}")
                self.value = new_value
                self.updated_at = current_time  # Update the time of the last update

    def __contains__(self, item):
        return str(self.value) in item

    def __str__(self):
        return str(self.value)
