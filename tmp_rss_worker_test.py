from stock_scanner.download.database import init_db
from stock_scanner.ui.workers.rss_feed_worker import RSSWorker

init_db()
worker = RSSWorker()

worker.log.connect(lambda msg: print("LOG:", msg))
worker.error.connect(lambda msg: print("ERROR:", msg))
worker.data_ready.connect(lambda data: print("DATA_READY:", data))
worker.finished.connect(lambda: print("FINISHED"))

worker.run()
