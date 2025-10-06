"""Google Trends client utilities."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

import pandas as pd
from pytrends.request import TrendReq

from .config import AnalysisConfig, TIMEZONE


def _cache_path(cache_dir: Path, slug: str) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"trends_{slug}.json"


def build_trends_client(config: AnalysisConfig) -> TrendReq:
    """Instantiate a configured TrendReq session."""

    return TrendReq(hl="en-US", tz=330, timeout=(config.session_timeout, config.session_timeout))


def fetch_trends_series(
    config: AnalysisConfig,
    *,
    keywords: Iterable[str],
    timeframe: str,
    cache_slug: str,
) -> pd.DataFrame:
    """Fetch Google Trends interest over time for the supplied keywords.

    Results are cached to avoid repeated requests during development.
    """

    cache_file = _cache_path(config.raw_data_dir, cache_slug)
    if cache_file.exists():
        raw = json.loads(cache_file.read_text())
        return pd.read_json(raw, orient="split")

    client = build_trends_client(config)
    client.build_payload(
        list(keywords),
        timeframe=timeframe,
        geo=config.trends_geo,
    )
    df = client.interest_over_time().drop(columns=["isPartial"], errors="ignore")
    cache_file.write_text(df.to_json(orient="split"))
    return df


def hourly_trends(
    config: AnalysisConfig,
    *,
    keywords: Iterable[str],
    lookback_hours: int,
    cache_slug: str,
) -> pd.DataFrame:
    """Return Trends series at hourly frequency over the configured window."""

    # Google Trends only allows limited intraday lookback windows. The pipeline will
    # fall back to multiple batched requests if the window exceeds 7 days.
    window_days = lookback_hours / 24
    if window_days <= 7:
        timeframe = f"now {int(window_days)}-d"
    else:
        timeframe = "now 7-d"

    df = fetch_trends_series(
        config,
        keywords=keywords,
        timeframe=timeframe,
        cache_slug=cache_slug,
    )

    df = df.tz_localize("UTC").tz_convert(TIMEZONE).resample("1H").mean().ffill()
    return df.tail(lookback_hours)
