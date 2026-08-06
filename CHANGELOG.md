# Changelog

All notable changes to the NIFTY Option Finder & Market Intelligence Workstation will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0-RC1] - 2026-07-11

### Added
- **Centralized System Readiness Checklist (Task 10)**: Designed and implemented a comprehensive real-time visual system verification matrix reporting overall workstation health (READY, WARNING, NOT READY) inside the Operations dashboard.
- **Order Lifecycle Management (Sprint 34)**: Integrated a complete manual order lifecycle state machine with multi-stage transitions (INITIATED, PLACED, EXECUTED, CLOSED, REJECTED) and high-fidelity timeline visuals.

### Changed
- **Comprehensive Release Candidate Audit (Sprint 35)**: Performed full engineering audits of architecture, performance profiles, security scopes, reliability retries, and environmental configurations.
- **Unit Test Regression Validation**: Confirmed 100% pass rate over all 231 pipeline unit tests.

---

## [1.0.0-beta] - 2026-07-10

### Added
- **Configuration & Workspace Manager**: Added support for profile settings, mock loaders, multi-level validations, schema migration evaluations, YAML/JSON exporters, and a corresponding ASCII CLI dashboard panel.
- **Operations & Workstation Health Manager**: Implemented deep system checks, startup diagnostics, directory validation, Python and Node module checking, memory utilization logging, and dynamic readiness scoring.
- **Execution & Position Lifecycle Manager**: Added live tracking for active paper-trading transactions, multi-stage state machines (INITIATED, PLACED, EXECUTED, CLOSED, REJECTED), ledger logging, and slippage modelling.
- **Manual Broker Integration**: Created a secure local gateway to authenticate, test reconnects, and track paper portfolio margins and credentials.
- **News Intelligence Engine**: Integrated sentiment analysis, scheduled macro events trackers, high-severity alert keywords flags, and automated directional score multipliers based on sentiment confidence.
- **Performance Analytics Engine**: Developed deep analytical processors tracking Sharpe ratio, win rate, P&L profiles, duration distributions, and regime-specific strategy performances.
- **Paper Trading Engine**: Implemented simulated ledger systems, margin calculations, auto-drawdown stops, and transaction validation.

### Changed
- Refactored all engine builders to follow the builder-pattern, outputting clean, immutable, frozen dataclasses from `src.models`.
- Updated CLI presentation layers to feature high-contrast, beautiful double-line borders, uniform timestamping, and consistent metrics units (e.g. `ms`, `%`, `INR`).
- Replaced direct standard file-system reads with stateless loader managers to prevent file locking and improve concurrent pipeline executions.

### Fixed
- Fixed critical dataclass positional argument issues during operations readiness scoring checks.
- Resolved circular import loops between the planning pipelines and confidence weighting processors.
- Corrected fractional slippage calculation discrepancies in option trade execution logs.

---

## [0.9.0] - 2026-06-15
### Added
- Integrated **AI Explanation Layer** generating natural language justifications and tactical summaries via the Google Gemini API.
- Implemented **Evening Planner** and **Intraday Assistant** to compare actual market actions against prior forecasts.
- Added support for Option Chain builders and ATM strike selection under volatile conditions.

---

## [0.8.0] - 2026-04-10
### Added
- Initial modular pipeline release featuring:
  - Market Intelligence & Scoring
  - Opportunity identification and directional bias categorization
  - Risk controls and allocation management
  - Core unittests covering fundamental directional math.
