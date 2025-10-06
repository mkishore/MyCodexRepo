"""Visualization utilities for the Polymarket lead/lag project."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .processing import MarketTimeSeries


def ensure_output_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def plot_lead_lag_heatmap(results: pd.DataFrame, *, output_dir: Path) -> Path:
    """Create a heatmap showing peak lag for each market."""

    ensure_output_dir(output_dir)
    fig, ax = plt.subplots(figsize=(10, 6))
    pivot = results.pivot_table(
        index="market_id",
        values="peak_lag_hours",
    )
    sns.heatmap(pivot, cmap="coolwarm", center=0, ax=ax, cbar_kws={"label": "Lag (hours)"})
    ax.set_title("Lead/Lag of Trends vs Polymarket Prices")
    fig.tight_layout()
    path = output_dir / "lead_lag_heatmap.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def plot_peak_leads(results: pd.DataFrame, *, output_dir: Path) -> Path:
    """Create a bar plot of peak lead/lag per market."""

    ensure_output_dir(output_dir)
    fig, ax = plt.subplots(figsize=(10, 6))
    ordered = results.sort_values("peak_lag_hours")
    sns.barplot(data=ordered, x="peak_lag_hours", y="market_id", palette="vlag", ax=ax)
    ax.axvline(0, color="black", linewidth=1)
    ax.set_xlabel("Lag (hours)")
    ax.set_ylabel("Market")
    ax.set_title("Peak Lead/Lag per Market")
    fig.tight_layout()
    path = output_dir / "peak_leads_bar.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def plot_case_study_overlay(
    series: MarketTimeSeries,
    *,
    output_dir: Path,
    price_label: str = "Price",
    trends_label: str = "Trends",
) -> Path:
    """Overlay price and trends series for a given market."""

    ensure_output_dir(output_dir)
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()
    series.prices["price"].plot(ax=ax1, color="tab:blue", label=price_label)
    if not series.trends.empty:
        series.trends.iloc[:, 0].plot(ax=ax2, color="tab:orange", label=trends_label)
    ax1.set_title(f"Price vs Trends: {series.market_id}")
    ax1.set_ylabel(price_label)
    ax2.set_ylabel(trends_label)
    fig.tight_layout()
    path = output_dir / f"overlay_{series.market_id}.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def plot_shock_scatter(
    shocks: pd.DataFrame,
    *,
    output_dir: Path,
) -> Path:
    """Scatter plot relating shock size to 24h trends change."""

    ensure_output_dir(output_dir)
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.scatterplot(data=shocks, x="shock_size", y="trends_delta_24h", hue="market_id", ax=ax)
    ax.set_xlabel("Price Shock (σ)")
    ax.set_ylabel("Δ Trends (24h)")
    ax.set_title("Shock Size vs 24h Trends Change")
    fig.tight_layout()
    path = output_dir / "shock_scatter.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path
