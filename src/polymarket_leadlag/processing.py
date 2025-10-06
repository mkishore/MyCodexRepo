"""Transform raw API payloads into aligned hourly datasets."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import pandas as pd

from .config import TIMEZONE, AnalysisConfig
from .data_api import MarketSnapshot


@dataclass(slots=True)
class MarketTimeSeries:
    """Holds aligned price and attention series for a market."""

    market_id: str
    prices: pd.DataFrame
    trends: pd.DataFrame

    @property
    def combined(self) -> pd.DataFrame:
        """Return merged dataframe containing price and trends information."""

        df = self.prices.join(self.trends, how="outer").sort_index()
        df = df.ffill()
        return df


def snapshots_to_frame(
    snapshots: Iterable[MarketSnapshot],
    *,
    column_name: str = "price",
) -> pd.DataFrame:
    """Convert a list of MarketSnapshot objects into an hourly dataframe."""

    if not snapshots:
        return pd.DataFrame(columns=[column_name])

    records = [
        {
            "timestamp": s.timestamp.tz_convert(TIMEZONE),
            column_name: getattr(s, column_name),
            "volume": s.volume,
        }
        for s in snapshots
    ]
    df = pd.DataFrame.from_records(records).set_index("timestamp").sort_index()
    df = df[~df.index.duplicated(keep="last")]
    df = df.resample("1H").ffill()
    return df[[column_name, "volume"]]


def assemble_market_timeseries(
    config: AnalysisConfig,
    *,
    history: dict[str, list[MarketSnapshot]],
    trends: dict[str, pd.DataFrame],
) -> dict[str, MarketTimeSeries]:
    """Create aligned time series objects for downstream analysis.

    Parameters
    ----------
    history:
        Mapping of market ID to raw price snapshots.
    trends:
        Mapping of market ID to hourly Google Trends dataframes.
    """

    series: dict[str, MarketTimeSeries] = {}
    for market_id, snapshots in history.items():
        price_df = snapshots_to_frame(snapshots)
        trend_df = trends.get(market_id, pd.DataFrame()).copy()
        if not trend_df.empty:
            trend_df = trend_df.tz_convert(TIMEZONE).resample("1H").ffill()
        series[market_id] = MarketTimeSeries(
            market_id=market_id,
            prices=price_df,
            trends=trend_df,
        )
    return series
