"""Helpers for communicating with the Polymarket Gamma and Data APIs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import httpx
from dateutil import parser

from .config import TIMEZONE, AnalysisConfig

ISO8601 = "%Y-%m-%dT%H:%M:%S.%fZ"


@dataclass(slots=True)
class MarketSnapshot:
    """Container for price/volume snapshots used in downstream processing."""

    market_id: str
    timestamp: datetime
    price: float
    volume: float


class PolymarketClient:
    """Thin wrapper around the Polymarket APIs with caching."""

    gamma_base: str = "https://gamma-api.polymarket.com"
    data_base: str = "https://data-api.polymarket.com"

    def __init__(self, *, timeout: float = 10.0) -> None:
        self._client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def _cache_path(self, directory: Path, key: str) -> Path:
        return directory / f"{key}.json"

    def fetch_market_metadata(
        self, market_ids: Iterable[str], *, cache_dir: Path
    ) -> list[dict[str, Any]]:
        """Fetch market metadata from the Gamma API.

        Parameters
        ----------
        market_ids:
            Iterable of market identifiers.
        cache_dir:
            Directory used to cache the raw payloads.
        """

        cache_dir.mkdir(parents=True, exist_ok=True)
        payload: list[dict[str, Any]] = []
        for market_id in market_ids:
            cache_path = self._cache_path(cache_dir, f"metadata_{market_id}")
            if cache_path.exists():
                payload.append(json.loads(cache_path.read_text()))
                continue

            response = self._client.get(
                f"{self.gamma_base}/markets/{market_id}",
                params={"includeEvents": "true"},
            )
            response.raise_for_status()
            data = response.json()
            cache_path.write_text(json.dumps(data))
            payload.append(data)
        return payload

    def fetch_market_timeseries(
        self,
        market_id: str,
        *,
        start: datetime,
        end: datetime,
        cache_dir: Path,
    ) -> list[MarketSnapshot]:
        """Fetch hourly price/volume timeseries for the specified market.

        The Polymarket Data API exposes price history via the `market-price-history` endpoint.
        This method paginates between ``start`` and ``end`` timestamps (UTC) while caching
        individual responses to avoid redundant network calls.
        """

        cache_dir.mkdir(parents=True, exist_ok=True)
        cursor = start.replace(tzinfo=timezone.utc)
        end_utc = end.replace(tzinfo=timezone.utc)
        snapshots: list[MarketSnapshot] = []

        while cursor <= end_utc:
            page_end = min(cursor + timedelta(hours=500), end_utc)
            cache_key = (
                f"history_{market_id}_{cursor.isoformat().replace(':', '-')}_{page_end.isoformat().replace(':', '-')}"
            )
            cache_path = self._cache_path(cache_dir, cache_key)
            if cache_path.exists():
                raw = json.loads(cache_path.read_text())
            else:
                response = self._client.get(
                    f"{self.data_base}/market-price-history/{market_id}",
                    params={
                        "interval": "hour",
                        "startTime": int(cursor.timestamp()),
                        "endTime": int(page_end.timestamp()),
                    },
                )
                response.raise_for_status()
                raw = response.json()
                cache_path.write_text(json.dumps(raw))

            for entry in raw:
                ts = parser.isoparse(entry["timestamp"]).astimezone(timezone.utc)
                snapshots.append(
                    MarketSnapshot(
                        market_id=market_id,
                        timestamp=ts,
                        price=float(entry.get("price", 0.0)),
                        volume=float(entry.get("volume", 0.0)),
                    )
                )
            cursor = page_end + timedelta(hours=1)

        return snapshots


def collect_market_history(config: AnalysisConfig) -> dict[str, list[MarketSnapshot]]:
    """Fetch market history for all configured markets using cache directories."""

    config.ensure_directories()
    client = PolymarketClient(timeout=config.session_timeout)
    try:
        end = datetime.now(tz=timezone.utc)
        start = end - config.lookback_delta
        history: dict[str, list[MarketSnapshot]] = {}
        for market_id in config.market_ids:
            history[market_id] = client.fetch_market_timeseries(
                market_id,
                start=start,
                end=end,
                cache_dir=config.raw_data_dir,
            )
        return history
    finally:
        client.close()
