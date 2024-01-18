from dataclasses import dataclass
import time

@dataclass
class TouchEvent:
    start_x: int
    start_y: int
    end_x: int = None
    end_y: int = None
    start_time: float = None
    update_time: float = None
    end_time: float = None
    duration: float = None

    @staticmethod
    def create(start_x, start_y):
        return TouchEvent(
            start_x=start_x,
            start_y=start_y,
            start_time=time.time(),
        )

    def update(self, end_x, end_y):
        self.end_x = end_x
        self.end_y = end_y
        self.update_time = time.time()

    def end(self):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        # In case end coordinates were not updated, use start coordinates
        if self.end_x is None or self.end_y is None:
            self.end_x = self.start_x
            self.end_y = self.start_y

    def last_time(self):
        return self.end_time if self.end_time is not None else self.update_time if self.update_time is not None else self.start_time

    def __str__(self):
        return f"TouchEvent(start=({self.start_x}, {self.start_y}), end=({self.end_x}, {self.end_y}), duration={(self.duration or -1):.3f})"
