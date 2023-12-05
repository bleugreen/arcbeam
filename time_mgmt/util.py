import time
from config import SAMPLE_RATE

def amt_rtp_to_ms(rtp, sample_rate=SAMPLE_RATE):
    return (rtp / sample_rate) * 1000


def amt_ms_to_rtp(ms, sample_rate=SAMPLE_RATE):
    return (ms / 1000.0) * sample_rate

def amt_ns_to_ms(ns):
    return (ns / 1_000_000.0)

def current_time_ms():
    return time.clock_gettime(time.CLOCK_MONOTONIC_RAW)*1000
