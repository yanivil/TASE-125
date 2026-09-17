# 02. Trading Framework & Setups

The scanner implements the **Swing Trading Framework — TASE (v2)**. This rulebook focuses strictly on high-probability setups in established institutional uptrends, with predefined risk.

---

## 🎯 The Two Setups

### 1. The Pullback Setup (`PULLBACK`)
The pullback strategy seeks to join an established Stage 2 uptrend when price temporarily digests gains and tests short-term support.

| Parameter | Rule | Rationale |
|---|---|---|
| **Trend Stack** | $\text{Close} > \text{EMA}_{50} > \text{SMA}_{200}$ and $\text{EMA}_{50}$ rising | Confirms long-term and intermediate institutional uptrend. |
| **RSI Cooling Zone** | $\text{RSI}(14) \in [40, 50]$ within last 3 bars | Confirms orderly momentum consolidation without breaking structure. |
| **Support Test** | Lowest low of last 5 bars $\le \text{EMA}_{20} + 1\times\text{ATR}$ | Price came down to test the 20-day EMA support band. |
| **Turn-Up Confirmation** | $\text{Close} > \text{EMA}_{20}$ and $\text{Close} > \text{Close}_{\text{yesterday}}$ | Buyers stepped in; confirmation that the bounce is underway. |

---

### 2. The 20-Day Range Breakout (`BREAKOUT`)
The breakout strategy catches fast-moving leadership stocks breaking out of a multi-week consolidation base.

| Parameter | Rule | Rationale |
|---|---|---|
| **Trend Stack** | $\text{Close} > \text{EMA}_{50} > \text{SMA}_{200}$ and $\text{EMA}_{50}$ rising | Must occur within an active bull market trend. |
| **Price Breakout** | $\text{Close} > \max(\text{High}_{20})$ of prior 20 sessions | Clean close above all overhead supply of the past month. |
| **Volume Expansion** | $\text{Volume} \ge 1.5 \times \text{Volume SMA}_{20}$ | Confirms institutional accumulation driving the breakout. |

---

## 🛡️ Structural Risk & Sizing Rules

Every confirmed trigger automatically generates structural stop-loss and profit target levels:

### 1. Structural Stop-Loss
- **Pullback Stop**: $\text{Low}_{5\text{-day}} - 0.5 \times \text{ATR}(14)$
- **Breakout Stop**: $\text{Low}_{10\text{-day}} - 0.5 \times \text{ATR}(14)$

The $0.5 \times \text{ATR}$ buffer prevents getting stopped out by intraday market noise.

### 2. The 1R Limit ($1R \le 2\times\text{ATR}$)
The risk per share is defined as:
$$1R = \text{Close} - \text{Stop}$$
If $1R > 2 \times \text{ATR}$, the setup is **disqualified** with note `1R > 2xATR`. This prevents taking trades where the stop is excessively wide.

### 3. The 2R Clearance Test
The nearest major structural resistance (the 52-week high) must be at least $2R$ away from the entry price:
$$\text{Resistance Room} = \text{High}_{52\text{w}} - \text{Close} \ge 2 \times 1R$$
*Exception*: If the stock is already at or breaking to new 52-week highs ($\text{Close} \ge \text{High}_{52\text{w}} \times 0.999$), this test is skipped because there is no overhead resistance ("blue sky").

### 4. Target 1 (T1)
- **Take Profit 1**: $\text{Close} + 2R$
- **Standard Execution**: Sell 50% of position at T1; advance the stop on the remainder to breakeven + trading costs.
