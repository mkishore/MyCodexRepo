# Polymarket Lead-Lag Analysis

This repository contains the scaffolding for an analysis that compares price and volume movements on Polymarket to public attention captured via Google Trends. The goal is to identify whether on-chain market signals lead or lag search interest for a curated list of high-liquidity markets over the past 30 days.

## Project Structure

```
.
├── data
│   ├── curated/   # cleaned, structured datasets used for analysis
│   └── raw/       # raw API pulls cached locally to avoid repeat calls
├── scripts
│   └── run_analysis.py  # main entry point for the end-to-end workflow
├── src
│   └── polymarket_leadlag
│       ├── __init__.py
│       ├── config.py
│       ├── data_api.py
│       ├── google_trends.py
│       ├── processing.py
│       ├── analysis.py
│       └── visualization.py
├── pyproject.toml
└── README.md
```

## Workflow Overview

1. **Data Acquisition**
   - `polymarket_leadlag.data_api` handles communication with the Polymarket Gamma and Data APIs.
   - `polymarket_leadlag.google_trends` fetches Google Trends series via `pytrends`.
   - Results are cached in `data/raw/`.

2. **Processing**
   - `polymarket_leadlag.processing` converts API responses into hourly bars in the Asia/Kolkata timezone.
   - Missing hours are forward-filled for prices and reindexed for Trends data.
   - Processed datasets are written to `data/curated/`.

3. **Analysis**
   - `polymarket_leadlag.analysis` computes cross-correlations for lags between −48 and +48 hours.
   - Peak correlation values and associated lead/lag offsets are exported to CSV.
   - Significant price shocks (>2σ) are identified, and surrounding Trends changes are evaluated.

4. **Visualization**
   - `polymarket_leadlag.visualization` creates the required charts: lead–lag heatmap, peak-lead bars, case-study overlays, and scatter plots.

5. **Execution**
   - The `scripts/run_analysis.py` script orchestrates the end-to-end flow. It accepts configuration parameters and optional overrides for market selection.

## Next Steps

1. Provide the list of 20 high-liquidity market IDs (unless the script is extended to auto-select them).
2. Implement the API clients, processing routines, analysis logic, and visualization code following the provided docstrings and TODOs.
3. Run `python scripts/run_analysis.py` after populating the required environment variables or configuration files.

## Environment Setup

```bash
pip install -e .
```

This will install the project in editable mode along with the required dependencies.

## Notes

- Respect Polymarket API rate limits. Reuse cached data where possible.
- Ensure all timestamps are normalized to Asia/Kolkata.
- The repository currently only contains scaffolding; core logic must be implemented.
