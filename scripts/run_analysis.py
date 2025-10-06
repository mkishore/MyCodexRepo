"""Entrypoint for the Polymarket lead/lag analysis workflow."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd

from polymarket_leadlag.analysis import summarize_lead_lag
from polymarket_leadlag.config import AnalysisConfig
from polymarket_leadlag.data_api import collect_market_history
from polymarket_leadlag.google_trends import hourly_trends
from polymarket_leadlag.processing import assemble_market_timeseries
from polymarket_leadlag.visualization import (
    plot_case_study_overlay,
    plot_lead_lag_heatmap,
    plot_peak_leads,
    plot_shock_scatter,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("market_ids", nargs="*", help="Polymarket market IDs to analyze")
    parser.add_argument("--lookback-hours", type=int, default=30 * 24)
    parser.add_argument("--max-lag", type=int, default=48)
    parser.add_argument("--price-jump-sigma", type=float, default=2.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.market_ids:
        raise SystemExit("Provide market IDs or configure auto-selection logic.")

    config = AnalysisConfig(
        market_ids=args.market_ids,
        lookback_hours=args.lookback_hours,
        max_lag_hours=args.max_lag,
        price_jump_sigma=args.price_jump_sigma,
    )

    config.ensure_directories()

    history = collect_market_history(config)
    trends_data = {
        market_id: hourly_trends(
            config,
            keywords=[market_id],
            lookback_hours=config.lookback_hours,
            cache_slug=f"{market_id}_trends",
        )
        for market_id in config.market_ids
    }

    series = assemble_market_timeseries(
        config,
        history=history,
        trends=trends_data,
    )

    results = summarize_lead_lag(config, series.values())

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results_path = output_dir / "lead_lag_summary.csv"
    results.to_csv(results_path, index=False)

    plot_lead_lag_heatmap(results, output_dir=output_dir)
    plot_peak_leads(results, output_dir=output_dir)

    # Case study placeholder: choose first two markets for overlay charts.
    for market_id in list(series.keys())[:2]:
        plot_case_study_overlay(series[market_id], output_dir=output_dir)

    # Shock scatter placeholder: create empty dataframe until implemented.
    shocks = pd.DataFrame(columns=["market_id", "shock_size", "trends_delta_24h"])
    plot_shock_scatter(shocks, output_dir=output_dir)

    print(f"Summary written to {results_path}")


if __name__ == "__main__":
    main()
