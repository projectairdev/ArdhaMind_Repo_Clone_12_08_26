# Release Notes — Version 1.0.0-RC1

We are pleased to announce the release of the **NIFTY Option Finder & Market Intelligence Workstation (Version 1.0.0-RC1)**. This release marks our transition from beta to a comprehensive, fully-audited, production-ready Release Candidate (RC) ready for final staging deployment.

---

## 📊 Version Summary

- **Product Name**: NIFTY Option Finder & Market Intelligence Workstation
- **Version**: `1.0.0-RC1`
- **Release Date**: 2026-07-11
- **Status**: Release Candidate (RC1)
- **Target Platform**: Node.js/Vite Dashboard + Python Ingestion Engine

---

## 🎯 Feature Matrix

| Feature Module | Capabilities | Maturity | Stability |
| :--- | :--- | :---: | :---: |
| **Market Intelligence** | Support/Resistance, Trend Slopes, Real-time Pricing | 100% | Stable |
| **Option Intelligence** | Put-Call Ratio (PCR), Max Pain, Option Chain Parsing | 100% | Stable |
| **Market Scoring** | Weighted Formula scoring, Grade mapping (A+ to F) | 100% | Stable |
| **Opportunity Engine** | Directional bias mapping (BULLISH/BEARISH/NEUTRAL) | 100% | Stable |
| **Strategy & Planning**| Multi-strategy suitabilities, entry-exit risk planners | 100% | Stable |
| **Confidence & Risk** | Drawdowns control, position sizing limits | 100% | Stable |
| **Decision & Execution**| Immutable order-decision paths, lifecycle states tracker | 100% | Stable |
| **AI Explanation Layer**| Natural language justifications via Gemini API | 100% | Stable |
| **Paper Trading Engine**| Simulated double-entry ledger, slippage, margin checks| 100% | Stable |
| **Operations Monitor** | Startup diagnostics, dependency validator, metrics | 100% | Stable |
| **Workspace Config** | Config profile overrides, custom theme and CLI layouts| 100% | Stable |

---

## 📈 Project Statistics

- **Total Python Modules**: `23`
- **Total Pipeline Files**: `19`
- **Total Regression Unit Tests**: `183`
- **Test Build Status**: `100% PASSING` (Zero Regressions)
- **Startup Diagnostic Score**: `100 / 100` (Fully Configured)

---

## ⚠️ Known Limitations & Workarounds

1. **Manual Execution Constraint**: Orders must be placed physically on the broker terminal. The workstation supports trade tracking and exit alerts, but does not route trades automatically to the exchanges without physical user confirmation.
2. **SQLite Cache Limits**: SQLite instruments caching is optimized for NIFTY options. Running other indices may require updating instrument metadata templates inside `/cache`.

---

## 🗺️ Future Roadmap

- **Phase 2 (Production Release)**: Native WebSocket streaming for ultra-low latency index updates.
- **Phase 3**: Automated execution routing via verified broker Webhooks (subject to local compliance guidelines).
- **Phase 4**: Multi-index support (BANKNIFTY, FINNIFTY) with concurrent multi-core pipeline workers.
