# AIR ArdhaMind — NIFTY 50 Intelligence Workstation

AIR ArdhaMind is an enterprise-grade, **READ-ONLY** NIFTY 50 market intelligence workstation and decision-support terminal.

The workstation combines deterministic market-data engines, real-time Kite Connect WebSocket streaming, evidence-based structural level analysis, multi-session intelligence, and an AI-powered Live Assistant into a unified high-performance React/Node/Python workstation.

---

## 🛡️ Absolute Safety & Product Invariants

- **Read-Only Invariant**: Production workstation is strictly read-only. No automated order placement, broker mutation, or autonomous execution.
- **Data Integrity**: Zero data fabrication; zero synthetic price replacement. Missing numeric data is explicitly handled as `UNAVAILABLE` or `None`.
- **Single Upstream Ticker**: Exactly one active upstream WebSocket streaming instance (`StreamingOrchestrator`).
- **Canonical State Truth**: Single authoritative frontend source of truth via `CanonicalWorkstationState` over local WebSocket `/api/ws`.

---

## 🚀 Workspaces & Capabilities

1. **NIFTY Live**: Real-time tick stream, live spot chart, candle buffer, VWAP, intraday range, and multi-timeframe trend telemetry.
2. **Live Assistant**: Context-aware market intelligence, grounded explanations, and live query interface.
3. **Today's Analysis**: Intraday performance evaluation, regime classification, session high/low tracking, and completed session review.
4. **Forward Outlook**: Multi-session predictive intelligence, structural level confluences, and scenario planning.
5. **Pre-Market Planner**: Pre-open market briefing, global cues, GIFT NIFTY gap analysis, and opening setup strategies.
6. **Market Pulse**: Cross-asset sentiment, India VIX, sector performance, and market breadth.
7. **NEWS & UPDATES**: Real-time filtered financial news, source attribution, category filtering, and impact scoring.
8. **Settings**: Broker connectivity health, session diagnostics, performance metrics, and workstation configuration.

---

## 📂 Project Architecture & Codebase Layout

```text
/
├── src/
│   ├── application/           # Workstation state coordinator, DataQualityService
│   ├── broker/
│   │   ├── adapters/          # KiteBrokerGateway (Zerodha KiteConnect REST/WS)
│   │   └── services/          # BrokerService, StreamingOrchestrator, MarketStatusService
│   │       └── portfolio/     # Read-only position, portfolio, order, and MTM telemetry
│   ├── controlled_execution/  # Preserved future human-controlled execution architecture
│   ├── frontend/              # React 18 / TypeScript workspaces, components, viewmodels
│   ├── intelligence_engine/   # Pre-Market, Today's Analysis, Forward Outlook, Live Assistant
│   ├── operations_engine/     # Service monitoring, readiness diagnostics, health scoring
│   ├── proposal_engine/       # Trade proposal models and audit storage
│   └── server_bridge.py       # Python daemon bridge interface
├── dist/                      # Production build bundle (server.cjs and client assets)
├── data/                      # Session stores, performance records, post-market briefings
├── docs/                      # Technical specifications, architecture docs, historical audits
├── tests/                     # 194 active regression tests covering all workstation engines
│   ├── archived_sprints/      # Archived historical test suites and legacy adapters
│   └── integration/           # End-to-end integration and runtime acceptance tests
├── server.ts                  # Production Express / WebSocket / HTTP bridge server
├── package.json               # Node workspace definition & build scripts
├── pytest.ini                 # Pytest testpath configuration & exclusions
└── requirements.txt           # Python application dependencies
```

---

## 🛠️ Quick Start & Local Development

### 1. Prerequisites
- **Node.js**: `v20.x` or `v24.x`
- **Python**: `3.11` or `3.12`

### 2. Dependency Installation
```bash
# Install Node dependencies
npm ci

# Create virtual environment and install Python dependencies
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt  # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # Linux/macOS
```

### 3. Verification & Testing
```bash
# TypeScript compilation check
npx tsc --noEmit

# Production bundle build
npm run build

# Run active Python regression test suite
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

### 4. Running the Local Workstation
```bash
# Start production server (Node Express + Python daemon bridge)
node dist/server.cjs

# Or run in development mode with Vite hot-reload
npm run dev
```

---

## 📘 Documentation
- [**Production Runbook**](PRODUCTION.md) — VPS operations, systemd service management, and monitoring.
- [**Product Specifications**](PRODUCT_SPEC.md) — Architectural principles and workspace capabilities.
- [**Historical Audits**](docs/historical_audits/) — Archive of sprint audits and engineering reviews.
