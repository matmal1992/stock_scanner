import traceback
from contextlib import redirect_stderr, redirect_stdout
from typing import TextIO, cast

from PySide6.QtCore import QObject, Signal

from stock_scanner.core.io_utils import EmittingStream
from stock_scanner.scanners.three_tier_scanner import run_3t_strategy


class ThreeTierWorker(QObject):
    finished = Signal()
    logUpdated = Signal(str)
    errorOccurred = Signal(str)

    def run(self) -> None:
        try:
            stream = EmittingStream(self.logUpdated)
            safe_stream = cast(TextIO, stream)

            with redirect_stdout(safe_stream), redirect_stderr(safe_stream):
                run_3t_strategy()

        except Exception:
            self.errorOccurred.emit(traceback.format_exc())

        finally:
            self.finished.emit()
