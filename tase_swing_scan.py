#!/usr/bin/env python3
"""
tase_swing_scan.py
==================

Screens the TA-35 universe against the "Swing Trading Framework — TASE (v2)"
rulebook and reports, per ticker, whether a mechanical entry trigger exists.

Data source
-----------
Yahoo Finance daily bars via ``yfinance``. TASE symbols carry the ``.TA``
suffix and most are quoted in agorot (currency code ``ILA``); the scanner
converts to ILS only where the rulebook needs ILS (the turnover screen).
All price levels in the output stay in the quote unit so they match your
broker screen.

Usage
-----
    pip install yfinance pandas numpy
    python tase_swing_scan.py                  # live scan, writes ./out/
    python tase_swing_scan.py --demo           # synthetic data, no network
    python tase_swing_scan.py --out results    # custom output folder
    python tase_swing_scan.py --min-turnover 2000000

Outputs
-------
    <out>/tase_swing_scan_<YYYY-MM-DD>.csv    machine-readable
    <out>/tase_swing_scan_<YYYY-MM-DD>.md     the table with the Trigger column

What is and is not automated
----------------------------
Automated: MA trend stack, RSI pullback zone, breakout with volume
confirmation, ATR-buffered structural stop, 1R-vs-ATR test, 2R-to-resistance
test, relative strength vs the index, group (sector) confirmation, liquidity
screen, market regime and breadth.

NOT automated — check by hand before any order: calendar events (BoI decision,
earnings, ex-dividend, index update, holidays), execution timing (continuous
trading after 10:30, never on a Friday), broker mechanics (stop-order type,
minimum order value, commissions).

Exit codes
----------
    0  scan completed (even if some symbols failed to download)
    1  fatal: no data at all / yfinance missing in live mode
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd

# yfinance is only required for live runs; demo mode must work without it so
# the pipeline can be verified in an offline environment.
try:
    import yfinance as yf  # type: ignore
except ImportError:  # pragma: no cover - exercised only where yfinance is absent
    yf = None


# ---------------------------------------------------------------------------
# Universe
# ---------------------------------------------------------------------------
# Why a static list: TASE index composition changes only at the semi-annual
# updates (May / November) plus rare fast-track additions, so a hand-maintained
# list is more reliable than scraping a script-rendered TASE page.
# "group" is the proxy used for sector confirmation (an equal-weight composite
# of the group's members); TASE's official sector indices are not on Yahoo.
# Listing marks names whose primary price discovery is in New York.
UNIVERSE: list[tuple[str, str, str, str, str]] = [
    # ticker, company, industry, group, listing
    ("POLI", "Bank Hapoalim", "Banking", "Banks", "Domestic"),
    ("LUMI", "Bank Leumi", "Banking", "Banks", "Domestic"),
    ("MZTF", "Mizrahi-Tefahot", "Banking", "Banks", "Domestic"),
    ("DSCT", "Israel Discount Bank", "Banking", "Banks", "Domestic"),
    ("FIBI", "First International Bank", "Banking", "Banks", "Domestic"),
    ("PHOE", "Phoenix Holdings", "Insurance", "Insurance", "Domestic"),
    ("HARL", "Harel", "Insurance", "Insurance", "Domestic"),
    ("CLIS", "Clal Insurance", "Insurance", "Insurance", "Domestic"),
    ("MGDL", "Migdal", "Insurance", "Insurance", "Domestic"),
    ("MMHD", "Menora Mivtachim", "Insurance", "Insurance", "Domestic"),
    ("AZRG", "Azrieli Group", "Real estate - malls & offices", "RealEstate", "Domestic"),
    ("MLSR", "Melisron", "Real estate - malls", "RealEstate", "Domestic"),
    ("BIG", "BIG Shopping Centers", "Real estate - retail centers", "RealEstate", "Domestic"),
    ("MGOR", "Mega Or", "Real estate - logistics & data centers", "RealEstate", "Domestic"),
    ("DIMRI", "Dimri", "Residential construction", "RealEstate", "Domestic"),
    ("SPEN", "Shapir Engineering", "Construction & infrastructure", "RealEstate", "Domestic"),
    ("OPCE", "OPC Energy", "Power generation", "Energy", "Domestic"),
    ("DLEKG", "Delek Group", "Oil & gas", "Energy", "Domestic"),
    ("NWMD", "NewMed Energy", "Natural gas (Leviathan)", "Energy", "Domestic"),
    ("NVPT", "Navitas Petroleum", "Oil & gas E&P", "Energy", "Domestic"),
    ("BEZQ", "Bezeq", "Telecom", "Other", "Domestic"),
    ("SAE", "Shufersal", "Food retail", "Other", "Domestic"),
    ("STRS", "Strauss Group", "Food & beverages", "Other", "Domestic"),
    ("NXSN", "NextVision", "Defense - drone cameras", "Defense", "Domestic"),
    ("TASE", "Tel Aviv Stock Exchange", "Financial services", "Other", "Domestic"),
    ("TEVA", "Teva", "Pharmaceuticals", "Other", "Dual (NYSE)"),
    ("NICE", "NICE", "Software", "Tech", "Dual (Nasdaq)"),
    ("CYBR", "Palo Alto Networks", "Cybersecurity", "Tech", "Dual (Nasdaq)"),
    ("ICL", "ICL Group", "Chemicals & fertilizers", "Other", "Dual (NYSE)"),
    ("ESLT", "Elbit Systems", "Defense", "Defense", "Dual (Nasdaq)"),
    ("TSEM", "Tower Semiconductor", "Semiconductors - foundry", "Tech", "Dual (Nasdaq)"),
    ("NVMI", "Nova", "Semiconductor equipment", "Tech", "Dual (Nasdaq)"),
    ("CAMT", "Camtek", "Semiconductor equipment", "Tech", "Dual (Nasdaq)"),
    ("ORA", "Ormat Technologies", "Geothermal / renewable energy", "Energy", "Dual (NYSE)"),
    ("ENLT", "Enlight Renewable Energy", "Renewable energy", "Energy", "Dual (Nasdaq)"),
    ("KEN", "Kenon Holdings", "Holding company (energy, shipping)", "Energy", "Dual (NYSE)"),
]

# Yahoo symbols for the benchmark. TA-125 is the framework's regime benchmark;
# TA-35 is the fallback; if neither downloads, an equal-weight composite of the
# universe is used and flagged in the output.
INDEX_SYMBOLS = ["^TA125.TA", "^TA35.TA"]


# ---------------------------------------------------------------------------
# Parameters (every number here comes from the v2 rulebook)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Params:
    """Framework parameters. Frozen so a run is reproducible and auditable."""

    lookback_days: int = 400        # calendar days requested from Yahoo (>= 252 bars)
    ema_short: int = 20             # short-term trend / trailing stop
    ema_mid: int = 50               # macro trend
    sma_long: int = 200             # macro trend
    rsi_len: int = 14
    atr_len: int = 14
    vol_avg_len: int = 20
    vol_mult: float = 1.5           # breakout-day volume >= 1.5x 20-day average
    min_turnover_ils: float = 1_000_000.0  # 20-day average daily turnover floor
    rsi_pullback_low: float = 40.0
    rsi_pullback_high: float = 50.0
    stop_buffer_atr: float = 0.5    # stop = structure low - 0.5 x ATR
    max_r_atr: float = 2.0          # 1R must be <= 2 x ATR
    min_rr_to_resistance: float = 2.0  # nearest resistance >= 2R away
    breakout_len: int = 20          # breakout = close above prior 20-day high
    rs_len: int = 20                # RS line at a 20-day high or rising over 20 days
    pullback_window: int = 3        # RSI must have been in-zone within the last N bars
    stale_days: int = 5             # warn if the last bar is older than this


# ---------------------------------------------------------------------------
# Indicators
# ---------------------------------------------------------------------------
def ema(series: pd.Series, length: int) -> pd.Series:
    """Exponential moving average (standard span-based smoothing).

    :param series: price series
    :param length: EMA span
    :returns: EMA series aligned to ``series``
    """
    return series.ewm(span=length, adjust=False).mean()


def sma(series: pd.Series, length: int) -> pd.Series:
    """Simple moving average.

    :param series: input series
    :param length: window length
    :returns: SMA series (NaN for the first ``length - 1`` bars)
    """
    return series.rolling(length).mean()


def rsi(close: pd.Series, length: int = 14) -> pd.Series:
    """Wilder RSI, the definition used by TradingView and most broker charts.

    :param close: close series
    :param length: RSI period
    :returns: RSI in the 0-100 range
    """
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / length, adjust=False).mean()
    # Edge case: a flat window gives avg_loss == 0 -> RSI 100 by convention.
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    out = 100.0 - 100.0 / (1.0 + rs)
    return out.fillna(100.0)


def atr(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """Wilder ATR using the full true-range definition (gaps included).

    :param df: OHLC frame with ``High``, ``Low``, ``Close`` columns
    :param length: ATR period
    :returns: ATR series in the quote unit
    """
    prev_close = df["Close"].shift(1)
    tr = pd.concat(
        [
            df["High"] - df["Low"],
            (df["High"] - prev_close).abs(),
            (df["Low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1.0 / length, adjust=False).mean()


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def _normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce a Yahoo/synthetic frame to tz-naive OHLCV with title-case columns.

    :param df: raw frame
    :returns: frame with exactly Open/High/Low/Close/Volume, NaN rows dropped
    """
    df = df.rename(columns=lambda c: str(c).title())
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    if getattr(df.index, "tz", None) is not None:
        df.index = df.index.tz_localize(None)
    return df.sort_index()


def load_history(symbol: str, params: Params) -> tuple[pd.DataFrame, str]:
    """Download daily bars for one symbol.

    :param symbol: Yahoo symbol, e.g. ``POLI.TA``
    :param params: scan parameters (lookback)
    :returns: (OHLCV frame, currency code such as ``ILA`` or ``ILS``)
    :raises RuntimeError: if the download is empty
    """
    ticker = yf.Ticker(symbol)
    # auto_adjust=False keeps raw closes so stop/target levels match the
    # chart; dividends are small relative to swing levels on these names.
    raw = ticker.history(period=f"{params.lookback_days}d", auto_adjust=False)
    if raw is None or raw.empty:
        raise RuntimeError(f"no data returned for {symbol}")
    currency = "ILA"  # sensible default for TASE equities
    try:
        currency = str(ticker.fast_info["currency"])
    except Exception:  # fast_info can be missing/partial; fall back silently
        try:
            currency = str(ticker.info.get("currency", currency))
        except Exception:
            pass
    return _normalize_frame(raw), currency


def synthetic_history(seed: int, bars: int = 320, start_price: float = 5000.0) -> pd.DataFrame:
    """Deterministic random-walk OHLCV for offline testing of the pipeline.

    :param seed: RNG seed (one per symbol so series differ)
    :param bars: number of daily bars
    :param start_price: starting close in the quote unit
    :returns: OHLCV frame on a business-day index ending today
    """
    rng = np.random.default_rng(seed)
    # Mild positive drift so some names trend; volatility ~1.5%/day like TASE large caps.
    rets = rng.normal(loc=0.0004, scale=0.015, size=bars)
    close = start_price * np.exp(np.cumsum(rets))
    open_ = close * (1 + rng.normal(0, 0.004, size=bars))
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.01, size=bars))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.01, size=bars))
    volume = rng.lognormal(mean=14.5, sigma=0.5, size=bars)
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=bars)
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}, index=idx
    )


# ---------------------------------------------------------------------------
# Context: regime, breadth, groups
# ---------------------------------------------------------------------------
def trend_state(close: pd.Series, params: Params) -> bool:
    """Rulebook regime test: close above a rising 50 EMA.

    :param close: close series
    :param params: parameters (EMA length)
    :returns: True if above a rising 50 EMA
    """
    e50 = ema(close, params.ema_mid)
    if len(e50) < params.ema_mid + 6:
        return False
    return bool(close.iloc[-1] > e50.iloc[-1] and e50.iloc[-1] > e50.iloc[-6])


def composite(closes: dict[str, pd.Series]) -> pd.Series:
    """Equal-weight, normalized composite of several close series.

    Each member is scaled to 1.0 at its first available bar so a high-priced
    name does not dominate. Used for group confirmation and as the index
    fallback.

    :param closes: mapping ticker -> close series
    :returns: composite series
    """
    frame = pd.concat(closes, axis=1).sort_index().ffill()
    normalized = frame.apply(lambda s: s / s.dropna().iloc[0])
    return normalized.mean(axis=1)


# ---------------------------------------------------------------------------
# Per-ticker evaluation
# ---------------------------------------------------------------------------
def evaluate(
    ticker: str,
    meta: tuple[str, str, str, str],
    df: pd.DataFrame,
    index_close: pd.Series,
    params: Params,
    group_ok: bool,
    regime_ok: bool,
    currency: str,
) -> dict:
    """Apply the full rulebook to one ticker and return a result row.

    Order of checks mirrors the rulebook: context gates (trend, RS, liquidity,
    group, regime) must all pass, then a setup must produce a trigger, then the
    trade must survive the 1R-vs-ATR test and the 2R-to-resistance test.

    :param ticker: TASE ticker
    :param meta: (company, industry, group, listing)
    :param df: OHLCV frame (>= 210 bars recommended)
    :param index_close: benchmark close series for the RS line
    :param params: parameters
    :param group_ok: group composite above a rising 50 EMA
    :param regime_ok: benchmark above a rising 50 EMA
    :param currency: quote currency code (``ILA`` = agorot)
    :returns: dict with one row of the output table
    """
    company, industry, group, listing = meta
    c, h, l, v = df["Close"], df["High"], df["Low"], df["Volume"]

    e20, e50, s200 = ema(c, params.ema_short), ema(c, params.ema_mid), sma(c, params.sma_long)
    rsi14 = rsi(c, params.rsi_len)
    atr14 = atr(df, params.atr_len)
    vol20 = sma(v, params.vol_avg_len)

    # Turnover screen needs ILS; Yahoo quotes most TASE equities in agorot.
    unit = 0.01 if currency.upper() == "ILA" else 1.0
    turnover20 = (c * unit * v).rolling(params.vol_avg_len).mean()

    # RS line = stock / index, aligned on the stock's calendar.
    idx = index_close.reindex(c.index).ffill()
    rs_line = c / idx

    close = float(c.iloc[-1])
    a = float(atr14.iloc[-1])
    hi52 = float(h.iloc[-252:].max())
    prior_high = float(h.iloc[-(params.breakout_len + 1):-1].max())  # excludes today
    low5 = float(l.iloc[-5:].min())
    low10 = float(l.iloc[-10:].min())

    # --- context gates -----------------------------------------------------
    enough_history = len(c) >= params.sma_long + 5
    trend_ok = bool(
        enough_history
        and close > e50.iloc[-1] > s200.iloc[-1]
        and e50.iloc[-1] > e50.iloc[-6]
    )
    # RS passes if the line is at (within 0.5% of) its 20-day high, or simply
    # higher than 20 bars ago - "rising or breaking out".
    rs_window = rs_line.iloc[-params.rs_len:]
    rs_ok = bool(
        rs_line.iloc[-1] >= rs_window.max() * 0.995
        or rs_line.iloc[-1] > rs_line.iloc[-params.rs_len - 1]
    )
    liq_ok = bool(turnover20.iloc[-1] >= params.min_turnover_ils)
    vol_ok = bool(v.iloc[-1] >= params.vol_mult * vol20.iloc[-1])

    # --- setups --------------------------------------------------------------
    recent_rsi = rsi14.iloc[-params.pullback_window:]
    rsi_in_zone = bool(
        ((recent_rsi >= params.rsi_pullback_low) & (recent_rsi <= params.rsi_pullback_high)).any()
    )
    # A pullback "touched" the 20 EMA zone if a low in the last 5 bars came
    # within one ATR of it; the entry day must close back above the 20 EMA
    # and above the prior close (turn-up), not just sit in the zone.
    touched_e20 = bool(low5 <= float(e20.iloc[-1]) + a)
    turning_up = bool(close > e20.iloc[-1] and close > c.iloc[-2])
    pullback_candidate = trend_ok and rsi_in_zone and touched_e20 and turning_up

    # Breakout = close above the prior 20-day high on >= 1.5x average volume.
    breakout_candidate = trend_ok and close > prior_high and vol_ok

    trigger, stop, notes = "NONE", None, []
    if breakout_candidate:
        trigger, stop = "BREAKOUT", low10 - params.stop_buffer_atr * a
    elif pullback_candidate:
        trigger, stop = "PULLBACK", low5 - params.stop_buffer_atr * a

    # --- risk tests ------------------------------------------------------------
    r1 = (close - stop) if stop is not None else None
    if trigger != "NONE":
        if r1 <= 0:
            # Defensive: a stop above the close means the structure is broken.
            trigger, notes = "NONE", notes + ["stop above close"]
        elif r1 > params.max_r_atr * a:
            trigger, notes = "NONE", notes + ["1R > 2xATR"]
        else:
            at_high = close >= hi52 * 0.999
            room = hi52 - close
            if not at_high and room < params.min_rr_to_resistance * r1:
                trigger, notes = "NONE", notes + ["52w high < 2R away"]

    # --- context gates applied last so the note explains what blocked -----------
    if trigger != "NONE":
        gates = {"trend": trend_ok, "RS": rs_ok, "liquidity": liq_ok, "group": group_ok, "regime": regime_ok}
        failed = [name for name, ok in gates.items() if not ok]
        if failed:
            trigger, notes = "NONE", notes + [f"gate fail: {','.join(failed)}"]

    # --- state label for names without a trigger --------------------------------
    if not enough_history:
        state = "Insufficient history"
    elif not trend_ok:
        state = "Below MA stack"
    elif close >= hi52 * 0.999:
        state = "At 52w high"
    elif (hi52 - close) / close <= 0.05:
        state = "Base under high"
    elif rsi14.iloc[-1] > 60:
        state = "Extended"
    elif rsi_in_zone:
        state = "Pullback zone"
    else:
        state = "Trend, no trigger"

    last_bar = df.index[-1].date()
    if (dt.date.today() - last_bar).days > params.stale_days:
        notes.append(f"stale data ({last_bar})")

    yes = lambda b: "Y" if b else "N"  # noqa: E731 - tiny formatter
    return {
        "Ticker": ticker,
        "Company": company,
        "Industry": industry,
        "Listing": listing,
        "Close": round(close, 1),
        "RSI14": round(float(rsi14.iloc[-1]), 1),
        "Trend": yes(trend_ok),
        "RS": yes(rs_ok),
        "Liq": yes(liq_ok),
        "Group": yes(group_ok),
        "State": state,
        "Trigger": trigger,
        "Stop": round(stop, 1) if stop is not None and trigger != "NONE" else "",
        "1R": round(r1, 1) if r1 is not None and trigger != "NONE" else "",
        "T1 (+2R)": round(close + 2 * r1, 1) if r1 is not None and trigger != "NONE" else "",
        "Turnover20 (ILS)": int(turnover20.iloc[-1]) if not np.isnan(turnover20.iloc[-1]) else "",
        "LastBar": str(last_bar),
        "Notes": "; ".join(notes),
    }


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def to_markdown(rows: list[dict], columns: list[str]) -> str:
    """Render rows as a GitHub-flavoured Markdown table without extra deps.

    :param rows: result dicts
    :param columns: column order
    :returns: Markdown string
    """
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join("---" for _ in columns) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run(args: argparse.Namespace) -> int:
    """Execute the scan end to end.

    :param args: parsed CLI arguments
    :returns: process exit code
    """
    params = Params(min_turnover_ils=args.min_turnover)
    if not args.demo and yf is None:
        print("yfinance is not installed. Run: pip install yfinance", file=sys.stderr)
        return 1

    # 1) Load every symbol; keep going on individual failures so one bad
    #    symbol (e.g. a wrong Yahoo code) does not kill the whole scan.
    data: dict[str, tuple[pd.DataFrame, str]] = {}
    failures: list[str] = []
    for i, (ticker, *_rest) in enumerate(UNIVERSE):
        try:
            if args.demo:
                data[ticker] = (synthetic_history(seed=100 + i), "ILA")
            else:
                data[ticker] = load_history(f"{ticker}.TA", params)
        except Exception as exc:  # noqa: BLE001 - report and continue
            failures.append(f"{ticker}: {exc}")
    if not data:
        print("No data loaded for any symbol.", file=sys.stderr)
        return 1

    # 2) Benchmark: TA-125, then TA-35, then equal-weight composite fallback.
    index_close: pd.Series | None = None
    index_used = "equal-weight universe composite (fallback)"
    if args.demo:
        index_close = synthetic_history(seed=7, start_price=2000.0)["Close"]
        index_used = "synthetic index (demo)"
    else:
        for sym in INDEX_SYMBOLS:
            try:
                index_close = load_history(sym, params)[0]["Close"]
                index_used = sym
                break
            except Exception:
                continue
    if index_close is None:
        index_close = composite({t: d[0]["Close"] for t, d in data.items()})
    regime_ok = trend_state(index_close, params)

    # 3) Breadth and group composites.
    above50 = sum(trend_state(d[0]["Close"], params) for d in data.values())
    breadth = 100.0 * above50 / len(data)
    groups: dict[str, dict[str, pd.Series]] = {}
    for ticker, company, industry, group, listing in UNIVERSE:
        if ticker in data:
            groups.setdefault(group, {})[ticker] = data[ticker][0]["Close"]
    group_ok = {g: trend_state(composite(members), params) for g, members in groups.items()}

    # 4) Evaluate.
    rows = []
    for ticker, company, industry, group, listing in UNIVERSE:
        if ticker not in data:
            rows.append({"Ticker": ticker, "Company": company, "Industry": industry,
                         "Listing": listing, "State": "NO DATA", "Trigger": "N/A"})
            continue
        df, currency = data[ticker]
        rows.append(evaluate(ticker, (company, industry, group, listing), df,
                             index_close, params, group_ok[group], regime_ok, currency))

    # 5) Write outputs.
    columns = ["Ticker", "Company", "Industry", "Listing", "Close", "RSI14", "Trend", "RS",
               "Liq", "Group", "State", "Trigger", "Stop", "1R", "T1 (+2R)",
               "Turnover20 (ILS)", "LastBar", "Notes"]
    stamp = dt.date.today().isoformat()
    out_dir = args.out
    import os
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, f"tase_swing_scan_{stamp}.csv")
    md_path = os.path.join(out_dir, f"tase_swing_scan_{stamp}.md")
    pd.DataFrame(rows, columns=columns).to_csv(csv_path, index=False)

    header = [
        f"# TASE swing scan - {stamp}",
        "",
        f"- Benchmark: {index_used} - regime {'PASS' if regime_ok else 'FAIL'} (close above rising 50 EMA)",
        f"- Breadth: {breadth:.0f}% of universe above a rising 50 EMA",
        "- Groups above rising 50 EMA: " + ", ".join(f"{g}={'Y' if ok else 'N'}" for g, ok in sorted(group_ok.items())),
        f"- Turnover floor: {params.min_turnover_ils:,.0f} ILS (20-day average)",
        "- Calendar, execution timing and broker checks are NOT automated - see README.",
        "",
    ]
    if failures:
        header.append("- Download failures: " + "; ".join(failures))
        header.append("")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(header) + "\n" + to_markdown(rows, columns) + "\n")

    triggered = [r["Ticker"] for r in rows if str(r.get("Trigger", "")).startswith(("PULLBACK", "BREAKOUT"))]
    print(f"Benchmark {index_used}: regime {'PASS' if regime_ok else 'FAIL'}; breadth {breadth:.0f}%")
    print(f"Triggers: {', '.join(triggered) if triggered else 'none'}")
    if failures:
        print("Failures: " + "; ".join(failures))
    print(f"Wrote {csv_path} and {md_path}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI definition.

    :param argv: argument list (None = sys.argv)
    :returns: parsed namespace
    """
    parser = argparse.ArgumentParser(description="TASE swing-trading framework scanner (v2 rules)")
    parser.add_argument("--out", default="out", help="output folder (default: ./out)")
    parser.add_argument("--min-turnover", type=float, default=Params.min_turnover_ils,
                        help="20-day average turnover floor in ILS (default 1,000,000)")
    parser.add_argument("--demo", action="store_true",
                        help="use synthetic data instead of Yahoo Finance (offline pipeline test)")
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
