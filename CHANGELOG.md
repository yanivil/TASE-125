# Changelog

All notable changes to this project are documented here.
Format follows Keep a Changelog; versions follow SemVer.

## [Unreleased]

### Added
- `tase_swing_scan.py`: first version of the TA-35 swing scanner implementing
  the Swing Trading Framework — TASE (v2) rules: MA trend stack, RSI 40–50
  pullback trigger, 20-day breakout trigger with 1.5× volume, ATR-buffered
  structural stop, 1R ≤ 2×ATR test, 2R-to-52-week-high test, relative
  strength vs TA-125, group composite confirmation, liquidity screen, regime
  and breadth summary.
- `--demo` mode with deterministic synthetic data for offline pipeline tests.
- CSV and Markdown outputs with a `Trigger` column and blocking-reason notes.
- `README.md` documenting data source, encoded rules, output columns and the
  checks that remain manual.
