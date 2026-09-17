# 05. Security & Integrity

Security and reproducibility are core architectural tenets of the **TASE-125** project.

---

## 🔒 Security Architecture

### 1. Zero-Secret Architecture
- The scanner requires **zero credentials**, API keys, broker tokens, or private secrets.
- All price series and market metrics are pulled strictly from public market data feeds.
- The `.gitignore` is preconfigured to reject and ignore all `.env`, `credentials.json`, private keys (`*.pem`, `*.key`), and security certificates.

### 2. Secret Scanning & Push Protection
- Enabled on GitHub repository `yanivil/TASE-125`.
- Any accidental commit containing API keys or private tokens is automatically blocked at `git push` time by GitHub's push protection engine.

### 3. Automated Vulnerability Audits (Dependabot)
- Dependabot is configured via `.github/dependabot.yml`.
- Monitors Python dependencies (`pip`) and CI actions (`github-actions`) weekly for Common Vulnerabilities and Exposures (CVEs).
- Issues automated security pull requests whenever a patched version becomes available.

---

## 🛡️ Continuous Integration & Quality Assurance

### Automated Testing (`.github/workflows/tests.yml`)
Every push and pull request to `main` triggers automated CI testing on GitHub Actions:
- **Matrix**: Tested across Python 3.11 and Python 3.12.
- **Unit Tests**: Verifies indicator mathematical bounds (RSI in $[0, 100]$, positive ATR), EMA/SMA rolling logic, and composite weighting.
- **Integration Test**: Runs a full pipeline simulation using deterministic synthetic price history (`--demo`) to ensure zero-regression reporting.

---

## 🚨 Vulnerability Reporting

If you identify a security issue, please follow our [Security Policy](../../SECURITY.md):
- **Do not post in public issues.**
- Privately disclose vulnerabilities through [GitHub Security Advisories](https://github.com/yanivil/TASE-125/security).
