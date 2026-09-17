# TASE 125 Project — Roadmap & Tasks

## Scheduled Expansion
- **Target Date**: 2026-10-01 (In 2 weeks)
- **Task**: Expand the scanner from the current TA-35 universe (36 stocks) to the full **TA-125** index constituents.
- **Details**:
  - Add the remaining ~90 tickers of the TA-125 index to `UNIVERSE` in `tase_swing_scan.py`.
  - Classify each constituent into its respective sector/group (Banks, RealEstate, Tech, Energy, Insurance, Defense, Other) for group confirmation composites.
  - Verify dual-listed tickers vs. domestic Yahoo Finance `.TA` symbols.
  - Ensure the 20-day turnover liquidity threshold (default 1,000,000 ILS) accounts for mid-cap liquidity dynamics across the TA-125.
