"""
Unit and integration tests for tase_swing_scan.py
"""
import os
import tempfile
import numpy as np
import pandas as pd
import pytest

from tase_swing_scan import (
    Params,
    atr,
    composite,
    ema,
    evaluate,
    parse_args,
    rsi,
    run,
    sma,
    synthetic_history,
    to_markdown,
    trend_state,
)


@pytest.fixture
def sample_ohlcv() -> pd.DataFrame:
    """Generate deterministic synthetic price history."""
    return synthetic_history(seed=42, bars=300, start_price=10000.0)


def test_indicators_shape_and_bounds(sample_ohlcv):
    """Test indicator outputs, shapes, and mathematical boundary constraints."""
    close = sample_ohlcv["Close"]
    
    # EMA & SMA lengths
    e20 = ema(close, 20)
    assert len(e20) == len(close)
    assert not e20.isna().all()
    
    s50 = sma(close, 50)
    assert len(s50) == len(close)
    assert s50.iloc[:49].isna().all()
    assert not s50.iloc[49:].isna().any()

    # RSI range: [0, 100]
    r = rsi(close, 14)
    assert len(r) == len(close)
    assert (r >= 0.0).all() and (r <= 100.0).all()

    # ATR must be strictly positive
    a = atr(sample_ohlcv, 14)
    assert len(a) == len(sample_ohlcv)
    assert (a > 0.0).all()


def test_trend_state():
    """Test regime / trend state detector (close > rising 50 EMA)."""
    p = Params()
    # Strongly upward trending series
    up_series = pd.Series(np.linspace(100, 200, 100))
    assert trend_state(up_series, p) is True

    # Strongly downward trending series
    down_series = pd.Series(np.linspace(200, 100, 100))
    assert trend_state(down_series, p) is False

    # Too short series
    short_series = pd.Series([100.0, 101.0, 102.0])
    assert trend_state(short_series, p) is False


def test_composite():
    """Test normalized equal-weight composite index generation."""
    s1 = pd.Series([100.0, 110.0, 120.0], index=pd.date_range("2026-01-01", periods=3))
    s2 = pd.Series([50.0, 55.0, 60.0], index=pd.date_range("2026-01-01", periods=3))
    comp = composite({"T1": s1, "T2": s2})
    
    # Both series gained 10% on step 1, 20% on step 2 -> normalized composite should reflect this
    assert comp.iloc[0] == pytest.approx(1.0)
    assert comp.iloc[1] == pytest.approx(1.1)
    assert comp.iloc[2] == pytest.approx(1.2)


def test_evaluate_structure(sample_ohlcv):
    """Test evaluate() generates all expected output fields and valid data types."""
    p = Params()
    index_close = sample_ohlcv["Close"] * 0.95
    row = evaluate(
        ticker="TEST",
        meta=("Test Corp", "Tech", "Tech", "Domestic"),
        df=sample_ohlcv,
        index_close=index_close,
        params=p,
        group_ok=True,
        regime_ok=True,
        currency="ILA",
    )
    
    expected_keys = [
        "Ticker", "Company", "Industry", "Listing", "Close", "RSI14",
        "Trend", "RS", "Liq", "Group", "State", "Trigger", "Stop",
        "1R", "T1 (+2R)", "Turnover20 (ILS)", "LastBar", "Notes"
    ]
    for k in expected_keys:
        assert k in row
    assert row["Ticker"] == "TEST"
    assert row["Trigger"] in ("NONE", "PULLBACK", "BREAKOUT")


def test_to_markdown():
    """Test markdown table generator formatting."""
    rows = [
        {"Ticker": "POLI", "Close": 7993.0, "Trigger": "NONE"},
        {"Ticker": "LUMI", "Close": 7811.0, "Trigger": "NONE"},
    ]
    cols = ["Ticker", "Close", "Trigger"]
    md = to_markdown(rows, cols)
    assert "| Ticker | Close | Trigger |" in md
    assert "| POLI | 7993.0 | NONE |" in md
    assert "| LUMI | 7811.0 | NONE |" in md


def test_full_demo_run():
    """End-to-end integration test running the scanner in demo mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        args = parse_args(["--demo", "--out", tmpdir])
        code = run(args)
        assert code == 0
        
        # Check output files
        files = os.listdir(tmpdir)
        csv_files = [f for f in files if f.endswith(".csv")]
        md_files = [f for f in files if f.endswith(".md")]
        
        assert len(csv_files) == 1
        assert len(md_files) == 1
        
        # Verify CSV has 36 tickers + 1 header line = 37 rows
        with open(os.path.join(tmpdir, csv_files[0])) as f:
            lines = f.readlines()
            assert len(lines) == 37
