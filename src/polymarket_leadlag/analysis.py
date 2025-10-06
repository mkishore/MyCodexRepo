"""Statistical routines for lead/lag analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from .config import AnalysisConfig
from .processing import MarketTimeSeries


@dataclass(slots=True)
class LeadLagResult:
    """Stores per-market correlation statistics."""

    market_id: str
    peak_correlation: float
    peak_lag_hours: int


def compute_cross_correlation(
    prices: pd.Series,
    trends: pd.Series,
    *,
    lag_range: range,
) -> LeadLagResult:
    """Compute maximum cross-correlation across the provided lag range."""

    if prices.empty or trends.empty:
        return LeadLagResult(market_id="", peak_correlation=np.nan, peak_lag_hours=0)

    prices = prices.sort_index().pct_change().dropna()
    trends = trends.sort_index().diff().dropna()
    aligned = prices.to_frame("returns").join(trends.to_frame("trend_delta"), how="inner").dropna()
    if aligned.empty:
        return LeadLagResult(market_id="", peak_correlation=np.nan, peak_lag_hours=0)

    returns = aligned["returns"].to_numpy()
    trend_delta = aligned["trend_delta"].to_numpy()

    corrs: list[tuple[int, float]] = []
    for lag in lag_range:
        shifted = np.roll(trend_delta, lag)
        if lag > 0:
            shifted[:lag] = np.nan
        elif lag < 0:
            shifted[lag:] = np.nan
        valid_mask = ~np.isnan(shifted)
        if valid_mask.sum() < 3:
            corrs.append((lag, np.nan))
            continue
        corr = np.corrcoef(returns[valid_mask], shifted[valid_mask])[0, 1]
        corrs.append((lag, corr))

    corrs = [(lag, corr) for lag, corr in corrs if not np.isnan(corr)]
    if not corrs:
        return LeadLagResult(market_id="", peak_correlation=np.nan, peak_lag_hours=0)

    peak_lag, peak_corr = max(corrs, key=lambda item: abs(item[1]))
    return LeadLagResult(market_id="", peak_correlation=float(peak_corr), peak_lag_hours=int(peak_lag))


def summarize_lead_lag(
    config: AnalysisConfig,
    series: Iterable[MarketTimeSeries],
) -> pd.DataFrame:
    """Compute cross-correlation stats for each market and return dataframe."""

    results: list[LeadLagResult] = []
    for ts in series:
        result = compute_cross_correlation(
            ts.prices["price"],
            ts.trends.iloc[:, 0] if not ts.trends.empty else pd.Series(dtype=float),
            lag_range=config.lag_range,
        )
        results.append(
            LeadLagResult(
                market_id=ts.market_id,
                peak_correlation=result.peak_correlation,
                peak_lag_hours=result.peak_lag_hours,
            )
        )

    return pd.DataFrame([r.__dict__ for r in results])
