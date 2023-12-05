from dataclasses import dataclass
import time


@dataclass(frozen=True)
class TimeStamp:
    latency_offset = 0.2
    sample_rate = 44100
    rtp: int
    py_ms: int

    @staticmethod
    def create(rtp: int, ms=None):
        # Progress message is sent when frame hits buffer, not when played, so the actual frame 'now' is rtp - buffer len
        if ms is None:
            return TimeStamp(rtp, time.clock_gettime(time.CLOCK_MONOTONIC_RAW)*1000)
        else:
            return TimeStamp(rtp, ms)
