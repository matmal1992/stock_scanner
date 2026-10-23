from datetime import datetime
from threading import Lock


class WorkerStatus:
    FIELD_ORDER = {
        "LLM": [
            "Pending",
            "Loop",
            "Last processed",
        ],
        "GPW": [
            "Loop",
            "Last scrape",
        ],
        "GPW entry scraper": [
            "Loop",
            "Last scrape",
        ],
    }

    def __init__(self) -> None:
        self._statuses: dict[str, dict[str, str]] = {}
        self._lock = Lock()

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime("%H:%M:%S")

    def update(self, group: str, field: str, status: str | None = None) -> None:
        if status is None:
            status = self._now()

        with self._lock:
            self._statuses.setdefault(group, {})[field] = status

    def snapshot(self) -> dict[str, dict[str, str]]:
        with self._lock:
            return {group: fields.copy() for group, fields in self._statuses.items()}

    def format_message(self, last_update: str) -> str:
        statuses = self.snapshot()
        sections = [f"Stock Scanner\nLast update: {last_update}"]

        for group, field_order in self.FIELD_ORDER.items():
            fields = statuses.get(group, {})

            if not fields:
                continue

            lines = [group]

            for field in field_order:
                if field in fields:
                    lines.append(f"{field}: {fields[field]}")

            for field, value in fields.items():
                if field not in field_order:
                    lines.append(f"{field}: {value}")

            sections.append("\n".join(lines))

        return "\n\n".join(sections)
