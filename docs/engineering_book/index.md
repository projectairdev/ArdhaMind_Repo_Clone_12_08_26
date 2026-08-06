# Engineering Design & Development Book
## NIFTY Option Finder & Market Intelligence Workstation

Welcome to the official, permanent **Engineering Design & Development Book** for the **NIFTY Option Finder & Market Intelligence Workstation (Version 1.0.0-beta)**. 

This document serves as the master specification, technical reference manual, and architectural blueprint for the entire trading workstation. It preserves implementation rationales, mathematical and structural boundaries, and technical decisions spanning from Sprint 1 through Sprint 26.

---

## 📖 Table of Contents

### [Part 1: Project Vision](./part1_vision.md)
- Why the workstation was built, problems it solves, human-in-the-loop philosophy, and core architectural mandates (stateless, immutable, modular).

### [Part 2: Project Evolution](./part2_evolution.md)
- Detailed, sprint-by-sprint chronicle from Sprint 1 to Sprint 26, detailing objectives, architectural additions, modules created, and integration paths.

### [Part 3: Complete System Architecture](./part3_architecture.md)
- Layered architecture view, dependency flow, engine coupling boundaries, execution models, and physical directory mappings.

### [Part 4: Engine-by-Engine Reference Manual](./part4_engines.md)
- Comprehensive technical documentation for all twenty-three core calculation and operational engines.

### [Part 5: Pipeline Orchestration & Execution](./part5_pipelines.md)
- Ingestion sequences, context transitions, pipeline hierarchies, and structural transaction boundaries.

### [Part 6: Immutable Data Models Spec](./part6_data_models.md)
- Reference schema catalog of all immutable dataclasses and how they serve as transactional contracts.

### [Part 7: Configuration & Workspace Management](./part7_config_workspace.md)
- Loader, validator, workspace preference parsers, schema migration engines, and export managers.

### [Part 8: Presentation & Dashboard Systems](./part8_presentation.md)
- CLI terminal rendering (ASCII layouts), React web dashboard integration, serialization formats, and panel layouts.

### [Part 9: Paper Trading & Margin Modeling](./part9_paper_trading.md)
- Double-entry ledger systems, initial/maintenance margin validation, slippage modeling, and performance analytics.

### [Part 10: Broker Gateways & Order Lifecycles](./part10_broker_integration.md)
- Secure token caching, multi-stage transaction state machines, manual action validation, and safety blocks.

### [Part 11: News Intelligence & Sentiment Analysis](./part11_news_intelligence.md)
- Multi-provider ingestion, deduplication, threat level evaluation, and sentiment multipliers.

### [Part 12: Verification & Testing Strategy](./part12_testing_strategy.md)
- Unit-testing design, regression verification, stateless mocking, and mock file loader setups.

### [Part 13: Architectural Decision Records (ADRs) & Lessons Learned](./part13_decisions_lessons.md)
- Why specific designs were finalized, engineering debts eliminated, design mistakes avoided, and performance optimizations.

### [Part 14: Project Statistics & Version Roadmap](./part14_roadmap_stats.md)
- Engineering metrics, coverage ratings, Version 1.0-beta specifications, and future expansion paths.

### [Part 15: Architectural Appendix & Glossary](./part15_appendix.md)
- Complete physical file structure, process diagrams, execution flows, and dictionary of domain-specific terms.

---

## 👩‍💻 Intended Audience

This book is compiled for:
- **Core Developers**: Who need to extend indicators, strategies, or build integration adapters without introducing regression bugs or breaking stateless guarantees.
- **System Operators**: Who oversee trading activities, monitor workstation performance metrics, and configure workspace preferences or active profiles.
- **Architectural Auditors**: Reviewing the structural integrity, security standards, and mathematical reliability of the trading workstation.
