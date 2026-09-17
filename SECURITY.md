# Security Policy

## Overview
**TASE-125** is an open-source, automated quantitative scanner for the Tel Aviv Stock Exchange (TASE). 

The application operates on a **zero-credential architecture**:
- It requires no API keys, private tokens, passwords, or personal financial data.
- All market prices are retrieved from public endpoints via Yahoo Finance (`yfinance`).
- All outputs are written locally to disk as Markdown and CSV reports.

## Reporting a Vulnerability
We take the security of this project and its users seriously. If you discover a security vulnerability or security-sensitive issue:

1. **Do not open a public GitHub issue.**
2. Use GitHub's private vulnerability reporting feature:
   - Navigate to the repository's [Security Tab](https://github.com/yanivil/TASE-125/security).
   - Click **Report a vulnerability** to privately submit details.
3. Provide as much detail as possible, including:
   - A description of the vulnerability.
   - Steps to reproduce or proof-of-concept.
   - Potential impact.

You will receive an initial response within 48 hours. Validated fixes will be patched and documented under `CHANGELOG.md`.

## Scope & Security Boundary

### In Scope
- Core scanner code (`tase_swing_scan.py`).
- Automation wrapper (`run_daily.sh`).
- Test suites and continuous integration workflows (`.github/workflows/`).
- Supply chain security and pinned dependencies (`requirements.txt`).

### Out of Scope
- Heuristic trading outcomes, strategy profitability, and market execution decisions (the scanner is an educational analytical tool, not financial advice).
- External infrastructure and service availability of third-party public data providers (such as Yahoo Finance / TASE).

## Dependency Security & Automated Updates
- Dependencies are pinned in `requirements.txt`.
- Automated security scanning and dependency update pull requests are monitored weekly via Dependabot (`.github/dependabot.yml`).
- Secret scanning and push protection are enabled on the repository to prevent accidental credential leakage.
