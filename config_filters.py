from dataclasses import dataclass

# -------- Tier 1 (1D momentum scan) --------
@dataclass
class Tier1Filters:
    min_ret_20d: float = -0.10
    min_trend_r2: float = 0.02
    min_atr_pct: float = 0.005
    min_turnover: int = 5_000
    max_compression: float = 0.65


# -------- Tier 2 (15m confirmation) --------
@dataclass
class Tier2Filters:
    min_ret_1d: float = -0.02
    min_trend_r2: float = 0.1
    min_vol_ratio: float = 0.8
    max_compression: float = 0.7
    min_dist_from_high: float = -0.03


# -------- Tier 3 (5m breakout trigger) --------
@dataclass
class Tier3Filters:
    # max_compression: float = 0.7
    # min_dist_from_high: float = -0.01
    # min_vol_ratio: float = 1.4
    # min_trend_r2: float = 0.3
    # atr_sanity_required: bool = True
    pass


# Instances used in project

T1_FILTER = Tier1Filters()
T2_FILTER = Tier2Filters()
T3_FILTER = Tier3Filters()

# WEIGHTS = {
#     "rs": 0.4,
#     "volume": 0.2,
#     "trend": 0.2,
#     "compression": 0.2,
# }
