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
        if ms is None:
            return TimeStamp(rtp, time.clock_gettime(time.CLOCK_MONOTONIC_RAW)*1000)
        else:
            return TimeStamp(rtp, ms)
