from datetime import datetime
from threading import Lock


class WorkerStatus:
    FIELD_ORDER = {
        "LLM": [
            "Pending",
            "Loop",
            "Last processed",
            "Last error",
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

    _statuses: dict[str, dict[str, str]] = {}
    _lock = Lock()
    _llm_error: str = "no error"
    _llm_error_screen: bytes = b""

    @classmethod
    def init(cls) -> None:
        cls._statuses = {group: {field: "-" for field in fields} for group, fields in cls.FIELD_ORDER.items()}

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime("%H:%M:%S")

    @classmethod
    def update(cls, group: str, field: str, status: str | None = None) -> None:
        if status is None:
            status = cls._now()

        with cls._lock:
            cls._statuses.setdefault(group, {})[field] = status

    @classmethod
    def update_llm_error_status(cls, error_msg: str, screenshot: bytes) -> None:
        cls._llm_error = error_msg
        cls._llm_error_screen = screenshot

    @classmethod
    def snapshot(cls) -> dict[str, dict[str, str]]:
        with cls._lock:
            return {group: fields.copy() for group, fields in cls._statuses.items()}

    @classmethod
    def format_message(cls, last_update: str) -> str:
        statuses = cls.snapshot()
        sections = [f"Stock Scanner\nLast update: {last_update}"]

        for group, field_order in cls.FIELD_ORDER.items():
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
