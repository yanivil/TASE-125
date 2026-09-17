# 04. Automation & Operations

This guide covers daily operation, crontab automation, weekend scheduling rules, output reports, and manual pre-trade execution checks.

---

## 🤖 Automated Daily Runner (`run_daily.sh`)

The script [`run_daily.sh`](../../run_daily.sh) automates the scanning process:

### 1. Weekend & Holiday Guard
- TASE trading takes place **Sunday through Thursday**.
- The scanner runs **Monday through Friday at 21:00 Israel Time**.
- The runner automatically inspects `date +%u`:
  ```bash
  DOW=$(date +%u)
  if [ "$DOW" -eq 6 ] || [ "$DOW" -eq 7 ]; then
    echo "Skipping scan: Saturday and Sunday are excluded."
    exit 0
  fi
  ```

### 2. Crontab Configuration
Configured on the host machine using macOS/Linux crontab:
```cron
# Runs Monday through Friday at 21:00 Israel Time
0 21 * * 1-5 "/Volumes/eDisk_2TB/Gemeni/TASE 125/run_daily.sh" >> "/Volumes/eDisk_2TB/Gemeni/TASE 125/logs/cron.log" 2>&1
```

---

## 📁 Output Artifacts

Every scan generates two files in the `./out/` directory:
1. **`tase_swing_scan_<YYYY-MM-DD>.csv`**: Machine-readable spreadsheet format.
2. **`tase_swing_scan_<YYYY-MM-DD>.md`**: Visual table containing header diagnostics and per-ticker statuses.

### Output Columns
| Column | Description |
|---|---|
| **Ticker** | TASE Symbol (e.g. `POLI`, `LUMI`, `CYBR`) |
| **Company** | Full company name |
| **Industry** | Primary business domain |
| **Listing** | `Domestic` vs `Dual (Nasdaq/NYSE)` |
| **Close** | Official closing price (in Agorot or native unit) |
| **RSI14** | Wilder RSI value |
| **Trend** | `Y` if Close > 50 EMA > 200 SMA and 50 EMA rising |
| **RS** | `Y` if Relative Strength is at 20-day high or rising |
| **Liq** | `Y` if 20-day turnover $\ge 1,000,000 \text{ ILS}$ |
| **Group** | `Y` if sector composite is above rising 50 EMA |
| **State** | Non-triggered category (e.g. `Base under high`, `Extended`) |
| **Trigger** | `PULLBACK`, `BREAKOUT`, or `NONE` |
| **Stop** | Structural stop-loss level (with 0.5 ATR buffer) |
| **1R** | Distance from Close to Stop |
| **T1 (+2R)** | First take-profit target |
| **Turnover20 (ILS)** | 20-day average turnover in Shekels |
| **LastBar** | Date of the latest complete daily bar |
| **Notes** | Blocking gates or risk warnings (`gate fail: RS`, `1R > 2xATR`) |

---

## 📋 Trader Manual Pre-Order Checklist

Before submitting an order based on a confirmed scan trigger:

1. **Calendar Filter**:
   - Check for Bank of Israel (BoI) interest rate decisions.
   - Verify that company earnings are not due within the next 10 trading days.
   - Confirm no pending ex-dividend date during the planned swing horizon.
2. **Dual-Listed Stocks**:
   - For names like `TEVA`, `CYBR`, `NICE`, `ESLT`, primary price discovery happens in New York.
   - Consider reducing position size to half or widening the stop buffer.
3. **Execution Timing**:
   - Enter orders during continuous trading after 10:30 Israel Time to avoid opening auction volatility.
   - Never execute new swing entries during a Friday session.
