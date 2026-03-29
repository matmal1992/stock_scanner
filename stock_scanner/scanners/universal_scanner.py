import pandas as pd

from stock_scanner.core.io_utils import load_tickers, read_parquet, save_tickers
from stock_scanner.report.report_updater import update_filter_section


def run_scan(profile: dict) -> None:

    CONFIG = profile["config"]
    filters = profile["filters"]

    candidates: list[tuple[str, dict[str, float]]] = []
    fail_stats: dict[str, int] = {}
    total_scanned: int = 0

    tickers = load_tickers(CONFIG.tickers_path)

    for ticker in tickers:
        path = CONFIG.data_dir / f"{ticker}.parquet"
        total_scanned += 1

        if not path.exists():
            continue

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

    stats = {"total": total_scanned, "passed": len(candidates), "fails": fail_stats}

    update_filter_section(candidates, profile["report_slot"], profile["columns"], stats)

    save_tickers([t for t, _ in candidates], CONFIG.to_download)


#  W przyszłości implementacja rankingu
# def calculate_score(m):

#     score = (
#         0.25 * (1 - m["compression_ratio"]) +   # im mniejsza kompresja tym lepiej
#         0.25 * min(m["vol_ratio"] / 3, 1) +     # normalizacja volume expansion
#         0.25 * m["trend_r2"] +                  # siła trendu
#         0.25 * (1 + m["dist_from_high"])        # bliskość high
#     )

#     return score
