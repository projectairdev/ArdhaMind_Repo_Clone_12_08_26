# NIFTY Option Finder & Market Intelligence Workstation

Welcome to the **NIFTY Option Finder & Market Intelligence Workstation** (Version 1.0.0-beta). This is an enterprise-grade, high-performance option analysis, directional scoring, risk management, and decision execution platform designed for paper trading and manual broker evaluation on NIFTY index options.

The workstation combines multiple high-speed scoring pipelines, an advanced opportunity intelligence layer, paper trading and manual brokerage bridges, an AI-powered explanation engine, and a complete system health monitor into a unified, lightweight terminal dashboard interface.

---

## 🚀 Key Capabilities

- **Market & Option Intelligence**: Analyzes live spot prices, ATM options, Put-Call Ratio (PCR), Max Pain, Open Interest confluences, and structural support/resistance zones.
- **Directional Scoring Pipeline**: Synthesizes market signals to generate real-time scoring metrics, visual grades, and directional bias (BULLISH/BEARISH/NEUTRAL).
- **Opportunity & Strategy Engines**: Matches incoming market conditions with a comprehensive strategy library (e.g., Scalping, Momentum, Swing, Mean Reversion) and evaluates candidate option contracts.
- **Confidence & Risk Controls**: Applies multi-tier statistical checks, exposure boundaries, capital allocation limits, and drawdown protections to each trade plan.
- **Decision & Execution Manager**: Implements an immutable order-decision layer and tracks live paper positions, slippage simulations, and transaction logs.
- **Workstation Health & Operations Manager**: Runs deep startup diagnostics, manages active dependency validation, resource utilization tracking, and generates real-time readiness ratings.
- **AI Explanation Layer**: Generates human-readable, context-aware justifications and risk analyses for every tactical trading decision using the Google Gemini model.
- **Workspace & Profile Manager**: Supports dynamic loading, saving, and verifying workstation preferences (CLI/React layouts, logging thresholds, active profiles).

---

## 📂 Project Architecture & Codebase Layout

```text
/
├── src/
│   ├── models/                # Immutable type-safe data schemas (dataclasses)
│   ├── pipeline/              # Coordinate executing mathematical & trading runs
│   ├── config_engine/         # Legacy scoring parameters
│   ├── configuration_engine/  # Profile presets, file loaders, validators, and exporters
│   ├── indicator_engine/      # Mathematical metrics, trend filters, support/resistance
│   ├── opportunity_engine/    # Filter spot data, classify regime, find candidate strikes
│   ├── strategy_engine/       # Tactical strategy evaluations (e.g. Scalping, Swing, Expiry)
│   ├── planner_engine/        # Formulates comprehensive TradePlans for option contracts
│   ├── confidence_engine/     # Statistical confirmation, historical confluences, weighting
│   ├── risk_engine/           # Portfolio drawdown limits, capital sizing rules
│   ├── decision_engine/       # Actionable buy/sell decisions, margin buffers
│   ├── execution_engine/      # Lifecycle states, transaction trails, slippage model
│   ├── paper_trading/         # Margin calculations, ledger tracking, paper accounts
│   ├── analytics_engine/      # Sharpe ratio, win rate, duration distribution analytics
│   ├── news_engine/           # Real-time event scraping, sentiment processing, alerts
│   ├── broker_engine/         # Manual broker accounts, API keys validation, API gateway
│   ├── operations_engine/     # Readiness, dependency verification, hardware usage metrics
│   ├── explanation_engine/    # Generates Gemini prompt payloads and parses responses
│   ├── dashboard/             # Visual dashboard panel rendering (CLI text-blocks & schemas)
│   └── utils/                 # Clean, stateless file IO, math, time, and loggers
├── docs/                      # Complete operational and development guides
├── tests/                     # 180+ comprehensive Python regression unittests
├── package.json               # Frontend Node workspace definition
├── requirements.txt           # Python application dependencies
└── metadata.json              # Platform capability declarations
```

---

## 🛠️ Quick Start

### 1. Prerequisites
- **Python**: Version `3.11` or higher.
- **NodeJS**: Version `18` or higher (for front-end dashboard viewing).

### 2. Dependency Installation
```bash
# Install Python backend dependencies
pip install -r requirements.txt

# Install Node dependencies
npm install
```

### 3. Running the Test Suite
The codebase includes 183+ high-coverage unittests. To run the full regression verification suite:
```bash
python3 -m unittest discover tests
```

---

## 📘 Comprehensive Documentation

Detailed documentation and operator books are organized in the `/docs` folder:

1. [**Architecture Guide**](docs/architecture_guide.md) — Dive deep into data flows, pipeline orchestration, and model relationships.
2. [**Installation Guide**](docs/installation_guide.md) — Complete setup instructions from a bare system to running workstation instances.
3. [**Configuration Guide**](docs/configuration_guide.md) — Learn how to customize scoring weights, profiles (Default, Aggressive, Conservative), and workstation preferences.
4. [**Operator Guide**](docs/operator_guide.md) — Walk through standard operating procedures, CLI monitoring layouts, and report outputs.
5. [**Paper Trading Guide**](docs/paper_trading_guide.md) — How the paper portfolio behaves, margin thresholds, and performance metrics tracking.
6. [**Live Trading Guide**](docs/live_trading_guide.md) — Steps for manual broker integration, risk control overrides, and safety margins.
7. [**Troubleshooting Guide**](docs/troubleshooting_guide.md) — Resolving common errors, missing API keys, or memory utilization bottlenecks.
8. [**Developer Guide**](docs/developer_guide.md) — Standard guidelines, adding new custom pipelines, and extending test coverage.
9. [**Release Notes**](docs/release_notes.md) — Details on the Version 1.0.0-beta Release Candidate.

For complete release history, refer to [**CHANGELOG.md**](CHANGELOG.md).

---

## ⚖️ License
Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) or source file headers for details.
