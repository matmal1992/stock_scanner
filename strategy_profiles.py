from dataclasses import dataclass


@dataclass
class Tier1Filters:
    min_ret_20d: float
    min_trend_r2: float
    min_atr_pct: float
    min_turnover: int
    max_compression: float


@dataclass
class Tier2Filters:
    min_ret_1d: float
    min_trend_r2: float
    min_vol_ratio: float
    max_compression: float
    min_dist_from_high: float


@dataclass
class Tier3Filters:
    max_compression: float
    min_dist_from_high: float
    min_vol_ratio: float
    min_trend_r2: float
    atr_sanity_required: bool

@dataclass
class StrategyProfile:
    tier1: Tier1Filters
    tier2: Tier2Filters
    tier3: Tier3Filters



STRATEGY_PROFILES = {

"conservative": StrategyProfile(

    tier1=Tier1Filters(
        min_ret_20d=0.08,
        min_trend_r2=0.65,
        min_atr_pct=0.025,
        min_turnover=2_000_000,
        max_compression=0.6
    ),

    tier2=Tier2Filters(
        min_ret_1d=0.03,
        min_trend_r2=0.5,
        min_vol_ratio=1.8,
        max_compression=0.6,
        min_dist_from_high=-0.02
    ),

    tier3=Tier3Filters(
        max_compression=0.6,
        min_dist_from_high=-0.005,
        min_vol_ratio=1.7,
        min_trend_r2=0.4,
        atr_sanity_required=True
    )
),

"balanced": StrategyProfile(

    tier1=Tier1Filters(
        min_ret_20d=0.05,
        min_trend_r2=0.5,
        min_atr_pct=0.02,
        min_turnover=1_000_000,
        max_compression=0.7
    ),

    tier2=Tier2Filters(
        min_ret_1d=0.02,
        min_trend_r2=0.4,
        min_vol_ratio=1.5,
        max_compression=0.7,
        min_dist_from_high=-0.03
    ),

    tier3=Tier3Filters(
        max_compression=0.7,
        min_dist_from_high=-0.01,
        min_vol_ratio=1.4,
        min_trend_r2=0.3,
        atr_sanity_required=True
    )
),

"aggressive": StrategyProfile(

    tier1=Tier1Filters(
        min_ret_20d=0.03,
        min_trend_r2=0.35,
        min_atr_pct=0.015,
        min_turnover=500_000,
        max_compression=0.8
    ),

    tier2=Tier2Filters(
        min_ret_1d=0.01,
        min_trend_r2=0.25,
        min_vol_ratio=1.2,
        max_compression=0.8,
        min_dist_from_high=-0.05
    ),

    tier3=Tier3Filters(
        max_compression=0.8,
        min_dist_from_high=-0.02,
        min_vol_ratio=1.2,
        min_trend_r2=0.2,
        atr_sanity_required=True
    )
)

}

ACTIVE_STRATEGY = "aggressive"
FILTERS = STRATEGY_PROFILES[ACTIVE_STRATEGY]