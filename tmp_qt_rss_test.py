import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from stock_scanner.ui.windows.news_tracker_window import NewsTrackerWindow

app = QApplication(sys.argv)
win = NewsTrackerWindow()
win.show()
print("Window shown")

QTimer.singleShot(100, win.start_rss)
QTimer.singleShot(10000, app.quit)

exit_code = app.exec()
print("Event loop exit", exit_code)
