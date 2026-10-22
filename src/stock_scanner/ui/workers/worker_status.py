from threading import Lock


class WorkerStatus:
    def __init__(self) -> None:
        self._statuses: dict[str, str] = {}
        self._lock = Lock()

    def update(self, worker: str, status: str) -> None:
        with self._lock:
            self._statuses[worker] = status

    def snapshot(self) -> dict[str, str]:
        with self._lock:
            return self._statuses.copy()
