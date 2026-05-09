import io
import traceback
from contextlib import redirect_stderr, redirect_stdout

from PySide6.QtCore import QObject, Signal

from stock_scanner.scanners.three_tier_scanner import run_3t_strategy


class ThreeTierWorker(QObject):
    finished = Signal()
    logUpdated = Signal(str)
    errorOccurred = Signal(str)

    def run(self) -> None:
        buffer = io.StringIO()

        try:
            with redirect_stdout(buffer), redirect_stderr(buffer):
                run_3t_strategy()

            output = buffer.getvalue()
            self.logUpdated.emit(output)

        except Exception:
            self.errorOccurred.emit(traceback.format_exc())

        finally:
            self.finished.emit()
