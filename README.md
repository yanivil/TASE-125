# TASE-125: Swing Trading Scanner

[![tests](https://github.com/yanivil/TASE-125/actions/workflows/tests.yml/badge.svg)](https://github.com/yanivil/TASE-125/actions/workflows/tests.yml)
[![python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](https://www.python.org/)
[![security](https://img.shields.io/badge/security-zero--credential-success)](SECURITY.md)
[![dependabot](https://img.shields.io/badge/dependabot-enabled-blue.svg?logo=dependabot)](.github/dependabot.yml)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**TASE-125** is an automated quantitative swing scanner for the Tel Aviv Stock Exchange (TASE). It screens equities daily against the rules of the **Swing Trading Framework — TASE (v2)**, reporting only confirmed setups with defined entry, structural stop-loss, and 2R profit targets.

---

## 📚 Project Documentation & Wiki

Detailed guides, mathematical definitions, and operational manuals are available in the **[Project Wiki](docs/wiki/Home.md)**:

- **[01. Architecture & Pipeline](docs/wiki/01-Architecture-and-Pipeline.md)** — Data pipeline, Agorot-to-ILS logic, and benchmark fallbacks.
- **[02. Trading Framework & Setups](docs/wiki/02-Trading-Framework-and-Setups.md)** — In-depth breakdown of `PULLBACK` and `BREAKOUT` triggers, stop calculations, and 2R targets.
- **[03. Context Gates & Market Regime](docs/wiki/03-Context-Gates-and-Market-Regime.md)** — Market regime, breadth, sector group composites, and relative strength (RS).
- **[04. Automation & Operations](docs/wiki/04-Automation-and-Operations.md)** — Daily scheduler (`run_daily.sh`), weekend filters, and trader pre-order checklist.
- **[05. Security & Integrity](docs/wiki/05-Security-and-Integrity.md)** — Zero-credential model, Dependabot configuration, and vulnerability reporting.

---

## 🚀 Quickstart

### Installation

```bash
# Clone the repository
git clone https://github.com/yanivil/TASE-125.git
cd TASE-125

# Setup virtual environment and dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest
```

### Running the Scanner

```bash
# 1. Offline demo test (synthetic random-walk data, deterministic verification)
python3 tase_swing_scan.py --demo

# 2. Live daily scan (downloads latest daily bars from Yahoo Finance)
python3 tase_swing_scan.py

# 3. Custom output directory and liquidity threshold
python3 tase_swing_scan.py --out out --min-turnover 2000000

# 4. Run full test suite
pytest -v
```

---

## ⏰ Daily Automation

The scanner includes an automated runner [`run_daily.sh`](run_daily.sh) configured to execute at **21:00 Israel Time** Monday through Friday:

```bash
./run_daily.sh
```

- **Weekend Guard**: Automatically skips execution on Saturday and Sunday.
- **Output**: Generates both a machine-readable CSV and a GitHub-Flavoured Markdown table in `./out/`.
- **Logs**: Preserves execution timestamps and console metrics in `./logs/`.

---

## 📊 Summary of Encoded Rules

| Rule | Technical Specification |
|---|---|
| **Market Regime** | Benchmark (`^TA125.TA`) close > rising 50 EMA |
| **Group Confirmation** | Sector composite close > rising 50 EMA |
| **Trend Stack** | Close > 50 EMA > 200 SMA, with 50 EMA rising |
| **Relative Strength** | RS line (stock ÷ benchmark) at/near 20-day high (±0.5%) or higher than 20 bars ago |
| **Liquidity Floor** | 20-day average daily turnover $\ge$ 1,000,000 ILS (`--min-turnover`) |
| **Pullback Trigger** | RSI(14) in 40–50 zone within last 3 bars; low within 1 ATR of 20 EMA; closes above 20 EMA & yesterday's close |
| **Breakout Trigger** | Close above prior 20-day high on volume $\ge$ 1.5× 20-day volume average |
| **Structural Stop** | Pullback: 5-day low − 0.5 ATR; Breakout: 10-day low − 0.5 ATR |
| **1R Max Risk Limit** | $1R$ ($\text{Close} - \text{Stop}$) must be $\le 2 \times \text{ATR}(14)$ |
| **2R Clearance Test** | 52-week high must be $\ge 2R$ above entry (skipped if already at 52-week high) |
| **Take Profit 1 (T1)** | $\text{Close} + 2R$ (sell 50%; move stop to breakeven + costs) |

---

## 🔒 Security

This project follows strict security best practices:
- **Zero-Secret Architecture**: Requires no API keys, tokens, or private credentials.
- **Secret Scanning & Push Protection**: Active on the GitHub repository.
- **Automated Dependency Updates**: Managed weekly via Dependabot (`.github/dependabot.yml`).
- **Security Policy**: See [SECURITY.md](SECURITY.md) for vulnerability disclosure guidelines.
