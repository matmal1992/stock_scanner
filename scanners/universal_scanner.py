from core.io_utils import read_parquet
from report.report_updater import update_filter_section

from core.io_utils import read_parquet
from report.report_updater import update_filter_section
import pandas as pd

def run_scan(profile):

    CONFIG = profile["config"]
    filters = profile["filters"]

    candidates = []
    fail_stats = {}
    total_scanned = 0

    for path in CONFIG.data_dir.glob("*.parquet"):

        ticker = path.stem
        total_scanned += 1

        try:
            df = read_parquet(path)

            if df is None:
                fail_stats["no_data"] = fail_stats.get("no_data", 0) + 1
                continue

            required_cols = ["Close", "High", "Low", "Volume"]
            if not all(col in df.columns for col in required_cols):
                fail_stats["missing_columns"] = fail_stats.get("missing_columns", 0) + 1
                continue

            metrics = profile["metrics"](df)

            if metrics is None:
                fail_stats["too_short_data"] = fail_stats.get("too_short_data", 0) + 1
                continue

            if any(pd.isna(v) for v in metrics.values()):
                fail_stats["nan_metrics"] = fail_stats.get("nan_metrics", 0) + 1
                continue

            passed = True

            for rule in profile["rules"]:

                name, func = rule

                if not func(metrics, filters):
                    fail_stats[name] = fail_stats.get(name, 0) + 1
                    passed = False
                    break

            if not passed:
                continue

            if profile.get("score"):
                metrics["score"] = profile["score"](metrics)

            candidates.append((ticker, metrics))

        except Exception as e:
            print("Error:", ticker, e)

    if profile.get("rank"):
        candidates.sort(key=lambda x: x[1]["score"], reverse=True)

    stats = {
        "total": total_scanned,
        "passed": len(candidates),
        "fails": fail_stats
    }

    update_filter_section(
        candidates,
        profile["report_slot"],
        profile["columns"],
        stats
    )