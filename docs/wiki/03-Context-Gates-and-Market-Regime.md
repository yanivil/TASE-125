# 03. Context Gates & Market Regime

The core principle of the framework is: **context precedes setup**. Even a picture-perfect chart pattern will fail if the broader market or sector is under heavy distribution.

---

## 🚪 The 5 Context Gates

A stock must clear all five gates to fire a live buy trigger. If a setup forms but fails one or more gates, the scanner demotes the trigger to `NONE` and logs the failure in the `Notes` column (e.g. `gate fail: RS,group`).

```
[Market Regime] ──➔ [Sector Group] ──➔ [Macro Trend] ──➔ [Relative Strength] ──➔ [Liquidity]
      │                   │                 │                   │                 │
      ▼                   ▼                 ▼                   ▼                 ▼
^TA125 > 50EMA      Group > 50EMA    50EMA > 200SMA       RS at 20d High     Turnover >= 1M
```

---

### Gate 1: Market Regime
- **Rule**: Benchmark close > rising 50 EMA ($\text{EMA}_{50\text{ today}} > \text{EMA}_{50\text{ 5 bars ago}}$).
- **Benchmark**: `^TA125.TA` (falling back to `^TA35.TA` or equal-weight composite).
- **Purpose**: Prevents initiating long swing positions during market corrections or bear markets.

### Gate 2: Sector / Group Confirmation
- **Rule**: The stock's sector composite must close above a rising 50 EMA.
- **Sectors Tracked**:
  - `Banks`: Hapoalim, Leumi, Mizrahi, Discount, FIBI.
  - `Insurance`: Phoenix, Harel, Clal, Migdal, Menora Mivtachim.
  - `RealEstate`: Azrieli, Melisron, BIG, Mega Or, Dimri, Shapir.
  - `Energy`: OPC, Delek, NewMed, Navitas, Ormat, Enlight, Kenon.
  - `Tech`: NICE, CYBR, Tower, Nova, Camtek.
  - `Defense`: NextVision, Elbit Systems.
  - `Other`: Bezeq, Shufersal, Strauss, TASE, Teva, ICL.
- **Purpose**: Institutional capital moves in sectors. A stock rarely runs sustainably without its peer group.

### Gate 3: Macro Trend Stack
- **Rule**: $\text{Close} > \text{EMA}_{50} > \text{SMA}_{200}$, with $\text{EMA}_{50}$ rising.
- **Minimum Data**: Requires $\ge 205$ bars of daily trading history.
- **Purpose**: Enforces buying only in Stage 2 accumulation phases.

### Gate 4: Relative Strength (RS)
- **Rule**: Stock's RS line ($\frac{\text{Stock Close}}{\text{Index Close}}$) is within 0.5% of its 20-day high or higher than it was 20 sessions ago.
- **Purpose**: Eliminates underperforming stocks. Focuses capital solely on market leaders.

### Gate 5: Minimum Turnover (Liquidity)
- **Rule**: 20-day average daily turnover $\ge 1,000,000 \text{ ILS}$.
- **Purpose**: Ensures adequate liquidity on the Tel Aviv Stock Exchange to prevent slippage and wide bid-ask spreads.

---

## 🏷️ Non-Trigger State Classifications

Stocks without triggers are categorized into informative states:
- **`Below MA stack`**: Price is below its 50 EMA or 200 SMA (avoid).
- **`At 52w high`**: Trading right at 52-week highs (watch for base formation).
- **`Base under high`**: Consolidating within 5% of its 52-week high (prime watchlist for breakouts).
- **`Extended`**: RSI(14) > 60 in an uptrend (too late to chase).
- **`Pullback zone`**: RSI(14) between 40 and 50 (watch for bounce confirmation).
- **`Trend, no trigger`**: Healthy uptrend, waiting for either a pullback or breakout setup.
- **`Insufficient history`**: Fewer than 205 trading sessions since IPO/listing.
