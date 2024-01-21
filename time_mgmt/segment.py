import time
from typing import List, Optional
from .stamp import TimeStamp

SR = 44100
THRESH_SEC = 2


class TimeSegment:
    def __init__(self, stream_type='Realtime', buffer_len=0.2):
        self.start: Optional[TimeStamp] = None
        self._end: Optional[TimeStamp] = None
        self.timestamps: List[TimeStamp] = []
        self.threshold = SR * THRESH_SEC
        self.stream_type = stream_type
        self.buffer_len = buffer_len
        print(f'Creating {stream_type} segment')

    def add_stamp(self, rtp: int, ms=None) -> bool:
        """
        Adds a timestamp to the segment.
        If the rtp difference exceeds the threshold, end the segment and return False.
        """
        frame_ms = ms
        new_stamp = TimeStamp.create(rtp, frame_ms)

        if self.timestamps:
            last_stamp = self.timestamps[-1]
            if new_stamp.rtp == last_stamp.rtp and new_stamp.py_ms != last_stamp.py_ms:
                # Replace last timestamp with new one if rtp is same but py_ns is different
                print('replace')
                self.timestamps[-1] = new_stamp
            elif abs(new_stamp.rtp-last_stamp.rtp) > self.threshold:
                self._end = last_stamp
                return False
            elif new_stamp.rtp > last_stamp.rtp:
                # Append new timestamp if it's greater than the last
                self.timestamps.append(new_stamp)
            else:
                # RTP reset or discontinuity detected
                self._end = last_stamp
                return False
        else:
            # For the first timestamp in the segment
            self.start = new_stamp
            self.timestamps.append(new_stamp)

        return True

    def __repr__(self):
        now = time.clock_gettime(time.CLOCK_MONOTONIC_RAW)*1000
        ret = ''
        if self.start:
            ret += f'Elapsed: {int((now - self.start.py_ms)/1000.0)}s '
        if self.timestamps:
            ret += f'Stamps: {len(self.timestamps)} '
            msgaps = [self.timestamps[i+1].py_ms -
                      self.timestamps[i].py_ms for i in range(len(self.timestamps)-1)]
            avg_msgap = sum(msgaps) / len(msgaps) if msgaps else 0
            rtpgaps = [self.timestamps[i+1].rtp -
                       self.timestamps[i].rtp for i in range(len(self.timestamps)-1)]
            avg_rtpgap = sum(rtpgaps) / len(rtpgaps) if rtpgaps else 0
            ret += f'Avg Gap: {int(avg_msgap)}ms - {int(avg_rtpgap)} frames'
        return ret

    def get_last(self):
        if self.timestamps:
            return self.timestamps[-1]
        return None
