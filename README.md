# tase-swing-scanner

Screens the TA-35 universe (36 names as of September 2026) against the
**Swing Trading Framework — TASE (v2)** rulebook and writes a table with a
`Trigger` column per ticker: `PULLBACK`, `BREAKOUT`, or `NONE` with the reason.

The rulebook itself lives in `swing-trading-framework.md`. This tool automates
the parts that are arithmetic. It does **not** replace the calendar, execution
and broker checks, which stay manual.

## Install and run

```bash
pip install yfinance pandas numpy
python tase_swing_scan.py            # live scan -> ./out/
python tase_swing_scan.py --demo     # offline pipeline test on synthetic data
python tase_swing_scan.py --out results --min-turnover 2000000
```

Run it after the closing auction (after ~17:30 Israel time Mon–Thu) so the
last bar is a full session. Do not act on a scan run mid-session: the trigger
rules are defined on daily closes.

## Data

- Source: Yahoo Finance via `yfinance`. TASE symbols use the `.TA` suffix
  (`POLI.TA`, `LUMI.TA`, …). Most are quoted in **agorot** (`ILA`); price
  levels in the output are left in the quote unit so they match your broker.
  The turnover screen converts to ILS internally.
- Benchmark for regime and relative strength: `^TA125.TA`, then `^TA35.TA`,
  then an equal-weight composite of the universe if neither downloads. The
  Markdown header states which one was used.
- Sector confirmation uses an equal-weight composite of the group members
  (Banks, Insurance, RealEstate, Energy, Tech, Defense, Other) because TASE's
  official sector indices are not on Yahoo. It is a proxy, not TA-Banks5.
- Universe is a hand-maintained list in `UNIVERSE`. Update it after each
  semi-annual index update (May / November) and any fast-track addition.

## Rules encoded (all thresholds in `Params`)

| Rule | Implementation |
|---|---|
| Market regime | benchmark close > 50 EMA and 50 EMA higher than 5 bars ago |
| Group confirmation | group composite close > rising 50 EMA |
| Trend stack | close > 50 EMA > 200 SMA, 50 EMA rising |
| Relative strength | RS line (stock ÷ benchmark) at its 20-day high (±0.5%) or above its value 20 bars ago |
| Liquidity | 20-day average turnover ≥ 1,000,000 ILS (`--min-turnover`) |
| Pullback trigger | RSI(14) touched 40–50 within the last 3 bars, a low in the last 5 bars came within 1 ATR of the 20 EMA, and today closed above the 20 EMA and above yesterday's close |
| Breakout trigger | close above the prior 20-day high on volume ≥ 1.5× the 20-day average |
| Stop | pullback: 5-day low − 0.5 ATR; breakout: 10-day low − 0.5 ATR |
| 1R test | 1R (close − stop) must be ≤ 2 × ATR(14) |
| 2R test | 52-week high must be ≥ 2R above the close (skipped if already at the high) |
| Target 1 | close + 2R (sell 50%; move stop to entry + costs) |

Context gates are applied last so the `Notes` column says exactly which gate
blocked an otherwise valid setup (`gate fail: RS,group`).

## Output columns

`Ticker, Company, Industry, Listing, Close, RSI14, Trend, RS, Liq, Group,
State, Trigger, Stop, 1R, T1 (+2R), Turnover20 (ILS), LastBar, Notes`

`State` classifies non-triggered names: `Below MA stack`, `At 52w high`,
`Base under high` (within 5%), `Extended` (RSI > 60), `Pullback zone`,
`Trend, no trigger`, `Insufficient history`, `NO DATA`.

## What stays manual before any order

- Calendar: BoI decision, earnings, ex-dividend, index update, holiday eves.
- Execution: continuous trading after 10:30, never a Friday session.
- Dual-listed names: half size and wider stop, or exclude — the scan flags
  the listing but applies the same rules to both buckets.
- Broker mechanics: stop-order type, minimum order value, commissions.

## Known limitations

- Yahoo's TASE feed occasionally drops sessions or lags a day; the `Notes`
  column flags a last bar older than 5 days as `stale data`.
- Yahoo symbols for recent listings can differ from the TASE ticker. For
  example, Palo Alto Networks trades on TASE as `CYBR.TA` (inherited from
  CyberArk). A wrong symbol shows up under "Download failures" and as `NO DATA`.
- ATR and RSI use Wilder smoothing (TradingView default). A simple-average ATR
  differs by a few percent.
- Dividends are not back-adjusted (`auto_adjust=False`) so levels match the
  chart; a large ex-dividend gap inside the ATR window inflates ATR slightly.
