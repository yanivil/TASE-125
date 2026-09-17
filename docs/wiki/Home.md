# Welcome to the TASE-125 Wiki

**TASE-125** is an automated quantitative screening engine designed for equities listed on the **Tel Aviv Stock Exchange (TASE)**. It scans daily price bars against the disciplined rules of the **Swing Trading Framework — TASE (v2)** to identify high-probability, risk-defined swing setups.

---

## 🧭 Navigation Guide

Explore the detailed documentation pages below:

| Page | Description |
|---|---|
| **[01. Architecture & Pipeline](01-Architecture-and-Pipeline)** | End-to-end data pipeline, Yahoo Finance integration, Agorot-to-ILS conversions, and benchmark fallbacks. |
| **[02. Trading Framework & Setups](02-Trading-Framework-and-Setups)** | Complete breakdown of `PULLBACK` and `BREAKOUT` triggers, structural stop sizing, and 2R profit targets. |
| **[03. Context Gates & Market Regime](03-Context-Gates-and-Market-Regime)** | How market regime, market breadth, sector group composites, and Relative Strength (RS) protect your capital. |
| **[04. Automation & Operations](04-Automation-and-Operations)** | Scheduled daily runner (`run_daily.sh`), weekend handling, report structures, and the manual pre-trade checklist. |
| **[05. Security & Integrity](05-Security-and-Integrity)** | Zero-secret architecture, automated Dependabot security updates, GitHub secret scanning, and vulnerability disclosure. |

---

## ⚡ Quickstart

### 1. Requirements
- Python 3.11 or 3.12
- Libraries: `yfinance`, `pandas`, `numpy`, `pytest`

```bash
# Clone the repository
git clone https://github.com/yanivil/TASE-125.git
cd TASE-125

# Create a virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest
```

### 2. Run Modes

- **Offline Demo Test** (synthetic deterministic data, no network required):
  ```bash
  python3 tase_swing_scan.py --demo
  ```

- **Live Daily Scan** (runs against live Yahoo Finance closing bars):
  ```bash
  python3 tase_swing_scan.py
  ```

- **Run Automated Daily Script**:
  ```bash
  ./run_daily.sh
  ```

- **Run Test Suite**:
  ```bash
  pytest -v
  ```

---

## 🕒 Timing & Trading Hours

- **TASE Trading Days**: Sunday through Thursday (Continuous trading runs from 09:59 to ~17:25 Israel Time).
- **Scan Schedule**: The scanner is automated to run **Monday through Friday at 21:00 Israel Time** (skipping Saturday and Sunday).
- **Rule of Thumb**: Never act on scan results mid-session. All triggers are calculated exclusively on official daily closing prices.
