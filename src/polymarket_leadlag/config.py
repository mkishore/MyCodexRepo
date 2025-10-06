"""Configuration models and defaults for the Polymarket lead/lag analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Iterable, Optional

TIMEZONE = "Asia/Kolkata"


def _default_raw_dir() -> Path:
    return Path("data/raw")


def _default_curated_dir() -> Path:
    return Path("data/curated")


@dataclass(slots=True)
class AnalysisConfig:
    """Container for end-to-end workflow settings.

    Attributes
    ----------
    market_ids:
        Iterable of Polymarket market identifiers to evaluate. Required.
    lookback_hours:
        Number of hours to include in the analysis window. Defaults to 30 days.
    max_lag_hours:
        The positive/negative lag range used for cross-correlation.
    price_jump_sigma:
        Threshold (in standard deviations) for identifying price shock events.
    raw_data_dir:
        Directory to cache raw API payloads.
    curated_data_dir:
        Directory to store processed datasets.
    trends_geo:
        Google Trends geography string. Defaults to worldwide.
    """

    market_ids: Iterable[str]
    lookback_hours: int = 30 * 24
    max_lag_hours: int = 48
    price_jump_sigma: float = 2.0
    raw_data_dir: Path = field(default_factory=_default_raw_dir)
    curated_data_dir: Path = field(default_factory=_default_curated_dir)
    trends_geo: str = ""
    trends_resolution: str = "now 7-d"
    trends_kw_batch_size: int = 5
    session_timeout: float = 10.0

    def ensure_directories(self) -> None:
        """Create cache directories if they do not exist."""

        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.curated_data_dir.mkdir(parents=True, exist_ok=True)

    @property
    def lag_range(self) -> range:
        """Return symmetric lag range for cross-correlation."""

        return range(-self.max_lag_hours, self.max_lag_hours + 1)

    @property
    def lookback_delta(self) -> timedelta:
        """Return timedelta representing total lookback window."""

        return timedelta(hours=self.lookback_hours)

    @classmethod
    def from_market_ids(
        cls,
        market_ids: Iterable[str],
        *,
        lookback_hours: Optional[int] = None,
        max_lag_hours: Optional[int] = None,
    ) -> "AnalysisConfig":
        """Create configuration from required market list with optional overrides."""

        kwargs: dict[str, object] = {"market_ids": market_ids}
        if lookback_hours is not None:
            kwargs["lookback_hours"] = lookback_hours
        if max_lag_hours is not None:
            kwargs["max_lag_hours"] = max_lag_hours
        return cls(**kwargs)
