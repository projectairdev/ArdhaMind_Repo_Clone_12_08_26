# Part 15: Architectural Appendix & Glossary

This section contains reference directories, dependency graphs, data-flow diagrams, and definitions for domain-specific terminology.

---

## 📂 Complete Workstation Folder Structure

```text
/
├── .env.example               # Template documenting required API secrets
├── .gitignore                 # Enforces untracked paths (logs, cache, node_modules)
├── CHANGELOG.md               # Version-by-version release history
├── README.md                  # High-level overview and quick-start instructions
├── tsconfig.json              # TypeScript compilation rules
├── vite.config.ts             # React dev-server and asset bundler settings
├── package.json               # Node workspace requirements
├── requirements.txt           # Python application dependencies
├── metadata.json              # Platform capability declarations
├── cache/                     # Temporary cache files (sessions, ledgers, DBs)
├── logs/                      # Operations journals and post-market reports
├── tests/                     # 180+ automated unittest suites
│   ├── options/               # Option chain calculation verification
│   └── test_*.py              # Modular system tests
└── src/                       # Main source directory
    ├── App.tsx                # React entry point
    ├── main.tsx               # Client bootstrap
    ├── index.css              # Custom Tailwind CSS rules
    ├── models/                # Immutable frozen dataclass models
    ├── pipeline/              # Orchestration workflows and data pipelines
    ├── indicator_engine/      # Mathematical metrics, trend filters, ATR
    ├── scoring_engine/        # Dynamic weighted score calculator
    ├── opportunity_engine/    # Directional trade window filters
    ├── strategy_engine/       # Tactical options suitability rules
    ├── planner_engine/        # Trade entry, target, and stop calculators
    ├── confidence_engine/     # Statistical trade weightings
    ├── risk_engine_v2/        # Exposure and capital drawdown controls
    ├── decision_engine/       # Actionable trade buy/sell status resolving
    ├── execution_engine/      # Multi-stage transaction state machines
    ├── paper_trading/         # Double-entry simulation accounting ledger
    ├── analytics_engine/      # Performance metrics calculators (Sharpe, Drawdowns)
    ├── news_engine/           # News scraper, deduplicator, sentiment weightings
    ├── broker_engine/         # Manual broker integration credentials validators
    ├── operations_engine/     # Diagnostic checks and system readiness monitors
    ├── configuration_engine/  # Profile overlays, validators, schema migrations
    ├── explanation_engine/    # Gemini AI explanation prompts and parsers
    └── utils/                 # Stateless IO, mathematical and time libraries
```

---

## 🔁 Real-Time Data Flow Diagram

```text
                     [ RAW TICK PRICE ]
                             │
                             ▼
 ┌───────────────────────────────────────────────────────┐
 │ 1. Market & Option Ingestion                          │
 │  - Reads Index Tick                                   │
 │  - Identifies ATM Strike                              │
 │  - Calculates Put-Call Ratio and Max Pain Strike      │
 └───────────────────────────┬───────────────────────────┘
                             │
                             ▼
 ┌───────────────────────────────────────────────────────┐
 │ 2. Ingesting News Sentiment                           │
 │  - Parses Bloomberg Headlines                         │
 │  - Deduplicates and decays over time                  │
 └───────────────────────────┬───────────────────────────┘
                             │
                             ▼
 ┌───────────────────────────────────────────────────────┐
 │ 3. Synthesizing Directional Score                     │
 │  - Applies weights to technical indicators            │
 │  - Blends in News Sentiment                           │
 │  - Evaluates Overall Score (0-100) & Grade (A+ to F)   │
 └───────────────────────────┬───────────────────────────┘
                             │
                             ▼
 ┌───────────────────────────────────────────────────────┐
 │ 4. Sizing Risk and Settle Decisions                   │
 │  - Scores Strategy Suitability (e.g. Scalping)        │
 │  - Brackets entry, exit, and stop boundaries          │
 │  - Filters through capital drawdown rules             │
 │  - Outputs Action Status (BUY, SELL, WATCH)           │
 └───────────────────────────┬───────────────────────────┘
                             │
                             ▼
 ┌───────────────────────────────────────────────────────┐
 │ 5. Executing Trades                                   │
 │  - Simulated Paper Ledger (Double-Entry)              │
 │  - Displays on terminal for Manual Broker Entry       │
 └───────────────────────────────────────────────────────┘
```

---

## 📖 Glossary of Terms

- **ATM (At-The-Money)**: The options contract whose strike price is closest to the current spot price of the underlying index.
- **PCR (Put-Call Ratio)**: The ratio of total outstanding put options open interest to total call options open interest. Serves as a measure of derivatives sentiment.
- **Max Pain**: The strike price at which option buyers would suffer the maximum financial loss if all contracts expired at that level.
- **ATR (Average True Range)**: A technical indicator measuring market volatility over a rolling timeframe.
- **Frozen Dataclass**: A standard Python data structure decorated with `frozen=True` that prevents any property mutations after instantiation.
- **Double-Entry Ledger**: An accounting method where every transaction is recorded as a balanced debit/credit pair.
- **Slippage**: The difference between the expected price of an option trade and the actual price at which the order is filled.
- **Sharpe Ratio**: A metric used to evaluate the risk-adjusted returns of a trading strategy relative to a risk-free rate (6.0%).
- **Drawdown**: The peak-to-valley decline in a portfolio's equity curve, expressed as a percentage.
- **Gemini AI Explanation**: Natural language justifications generated by the Google Gemini model detailing why a strategy was selected and what risks are present.
