from typing import Protocol
import pandas as pd


class MarketDataProvider(Protocol):
    def download(
        self,
        tickers: list[str],
        interval: str,
        period: str,
    ) -> dict[str, pd.DataFrame]:
        ...
