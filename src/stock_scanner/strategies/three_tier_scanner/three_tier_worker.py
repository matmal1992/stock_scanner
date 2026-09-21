import traceback
from contextlib import redirect_stderr, redirect_stdout
from typing import TextIO, cast

from PySide6.QtCore import QObject, Signal

from src.stock_scanner.core.utils import EmittingStream
from src.stock_scanner.strategies.three_tier_scanner.three_tier_scanner import run_3t_strategy


class ThreeTierWorker(QObject):
    finished = Signal()
    logUpdated = Signal(str)
    errorOccurred = Signal(str)
    progressUpdated = Signal(int)

    def run(self) -> None:
        try:
            stream = EmittingStream(self.logUpdated)
            safe_stream = cast(TextIO, stream)

            with redirect_stdout(safe_stream), redirect_stderr(safe_stream):
                run_3t_strategy(progress_callback=self.progressUpdated.emit)

        except Exception:
            self.errorOccurred.emit(traceback.format_exc())

        finally:
            self.finished.emit()
