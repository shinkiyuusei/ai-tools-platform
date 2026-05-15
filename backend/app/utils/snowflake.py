import time
import threading


_EPOCH = 1700000000000
_WORKER_ID_BITS = 5
_SEQUENCE_BITS = 12
_MAX_WORKER_ID = (1 << _WORKER_ID_BITS) - 1
_MAX_SEQUENCE = (1 << _SEQUENCE_BITS) - 1
_WORKER_ID_SHIFT = _SEQUENCE_BITS
_TIMESTAMP_SHIFT = _SEQUENCE_BITS + _WORKER_ID_BITS


class Snowflake:
    def __init__(self, worker_id: int = 1):
        if worker_id < 0 or worker_id > _MAX_WORKER_ID:
            raise ValueError(f"worker_id must be 0-{_MAX_WORKER_ID}")
        self._worker_id = worker_id
        self._sequence = 0
        self._last_timestamp = -1
        self._lock = threading.Lock()

    def next_id(self) -> int:
        with self._lock:
            timestamp = int(time.time() * 1000)
            if timestamp < self._last_timestamp:
                raise RuntimeError("Clock moved backwards")

            if timestamp == self._last_timestamp:
                self._sequence = (self._sequence + 1) & _MAX_SEQUENCE
                if self._sequence == 0:
                    while timestamp <= self._last_timestamp:
                        timestamp = int(time.time() * 1000)
            else:
                self._sequence = 0

            self._last_timestamp = timestamp
            return (
                (timestamp - _EPOCH) << _TIMESTAMP_SHIFT
            ) | (self._worker_id << _WORKER_ID_SHIFT) | self._sequence


_snowflake = Snowflake()


def generate_id() -> int:
    return _snowflake.next_id()
