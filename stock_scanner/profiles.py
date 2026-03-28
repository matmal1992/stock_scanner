# profiles.py
from stock_scanner.config import CONFIG_1D, CONFIG_5M, CONFIG_15M
from config_filters import T1_FILTER, T2_FILTER, T3_FILTER
from stock_scanner.strategy_profiles import (
    T1_COLUMNS,
    T2_COLUMNS,
    T3_COLUMNS,
    metrics_t1,
    metrics_t2,
    metrics_t3,
)

# -------- RULES --------
RULES_T1 = [
    ("min_ret_20d", lambda m, f: m["ret_20d"] >= f.min_ret_20d),
    ("min_trend_r2", lambda m, f: m["trend_r2"] >= f.min_trend_r2),
    ("min_atr_pct", lambda m, f: m["atr_pct"] >= f.min_atr_pct),
    ("min_turnover", lambda m, f: m["avg_turnover"] >= f.min_turnover),
    ("max_compression", lambda m, f: m["compression_ratio"] <= f.max_compression),
]

RULES_T2 = [
    ("min_ret_1d", lambda m, f: m["ret_1d"] >= f.min_ret_1d),
    ("min_trend_r2", lambda m, f: m["trend_r2"] >= f.min_trend_r2),
    ("min_vol_ratio", lambda m, f: m["vol_ratio"] >= f.min_vol_ratio),
    ("max_compression", lambda m, f: m["compression_ratio"] <= f.max_compression),
    ("min_dist_from_high", lambda m, f: m["dist_from_high"] >= f.min_dist_from_high),
]

RULES_T3 = [
    ("max_compression", lambda m, f: m["compression_ratio"] <= f.max_compression),
    ("min_dist_from_high", lambda m, f: m["dist_from_high"] >= f.min_dist_from_high),
    ("min_vol_ratio", lambda m, f: m["vol_ratio"] >= f.min_vol_ratio),
    ("min_trend_r2", lambda m, f: m["trend_r2"] >= f.min_trend_r2),
    (
        "atr_sanity_required",
        lambda m, f: m["atr_sanity"] if f.atr_sanity_required else True,
    ),
    ("alert", lambda m, f: m["alert"]),
]

# -------- PROFILES --------
PROFILE_T1 = {
    "config": CONFIG_1D,
    "filters": T1_FILTER,
    "metrics": metrics_t1,
    "rules": RULES_T1,
    "columns": T1_COLUMNS,
    "report_slot": "<!-- T1_FILTER -->",
    "score": None,
    "rank": False,
}

PROFILE_T2 = {
    "config": CONFIG_15M,
    "filters": T2_FILTER,
    "metrics": metrics_t2,
    "rules": RULES_T2,
    "columns": T2_COLUMNS,
    "report_slot": "<!-- T2_FILTER -->",
    "score": None,
    "rank": False,
}

PROFILE_T3 = {
    "config": CONFIG_5M,
    "filters": T3_FILTER,
    "metrics": metrics_t3,
    "rules": RULES_T3,
    "columns": T3_COLUMNS,
    "report_slot": "<!-- T3_FILTER -->",
    "score": lambda m: m["vol_ratio"] + m["trend_r2"],  # przykładowa funkcja scoringowa
    "rank": True,
}
