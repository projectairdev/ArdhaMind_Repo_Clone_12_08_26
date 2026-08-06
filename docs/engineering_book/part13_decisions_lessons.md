# Part 13: Architectural Decision Records (ADRs) & Lessons Learned

This section documents the formal Architectural Decision Records (ADRs) that shaped the system's design, alongside lessons learned and technical debt eliminated throughout development.

---

## 🏛️ Architectural Decision Records (ADRs)

### ADR 001: Selection of Stateless Engine Design
- **Context**: Early iterations of calculation engines maintained internal state lists (e.g., storing historical prices or tracking active signals inside class-level properties).
- **Decision**: All engines must be strictly stateless, with calculation functions declared as static methods.
- **Rationale**: Storing state inside calculation modules led to memory leaks, race conditions, and corrupted subsequent runs. Stateless engines guarantee that given identical input data, calculations return identical results.
- **Impact**: Code became 100% thread-safe, making multi-threaded backtesting simple to implement.

### ADR 002: Immutability of Data Models (Frozen Dataclasses)
- **Context**: Engines communicate across a multi-stage pipeline. Modifying context variables mid-flight led to silent errors.
- **Decision**: All data models in `src/models/` must be decorated with `@dataclass(frozen=True)`.
- **Rationale**: Enforcing immutability prevents downstream risk or planning engines from altering core parameters (such as entry premiums or strike prices).
- **Impact**: Eliminated common mutation bugs, making the system highly reliable and audit-safe.

### ADR 003: Restriction on Autonomous Trading (Human-in-the-Loop)
- **Context**: The workstation is designed to assist option traders. Auto-routing trades directly to live accounts presents regulatory and financial risks.
- **Decision**: The system acts strictly as a decision support system and manual execution bridge.
- **Rationale**: Requiring manual validation of recommended trade plans prevents catastrophic failures due to unexpected market events, internet disconnects, or broker API errors.
- **Impact**: Complete compliance with local regulatory guidelines, ensuring absolute safety of operator capital.

### ADR 004: Decoupling of Presentation and Calculation Layers
- **Context**: Early implementations blended terminal styling and ASCII box drawing with core mathematical functions.
- **Decision**: Isolate presentation systems inside specialized dashboard modules. Communication occurs strictly through serialized JSON schemas.
- **Rationale**: Blending presentation and business logic made testing difficult and prevented porting the UI to the web. Decoupling allows developers to swap or extend views (CLI or React) without touching calculation models.
- **Impact**: The UI can be updated from CLI to React with zero risk of regression bugs.

### ADR 005: Paper Trading Integration Prior to Live Routing
- **Context**: Operators need a way to prove strategy edge and test system behavior.
- **Decision**: Build a local paper trading simulator with double-entry ledgers and margin accounting.
- **Rationale**: Running simulations locally with realistic slippage and fee calculations allows operators to validate their trading edge before committing real capital.
- **Impact**: Provides a safe testing sandbox for training and optimization.

---

## 💡 Lessons Learned & Technical Debt Eliminated

- **Elimination of Circular Imports**: In early development stages, the Trade Planner required direct access to Confidence weighting coefficients, which in turn queried planning parameters. This was resolved by introducing a flat dependency flow where pipelines orchestrate the sequence, removing circular dependencies.
- **Unified Logging Conventions**: Legacy print statements and inconsistent logging prefixes were replaced with a centralized, thread-safe logger in `src/utils/logger.py`. Log levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`) are strictly enforced, ensuring readable tracebacks under high volatility.
- **Schema Validation Gateways**: Direct filesystem reads were replaced with a centralized `ProfileManager` that validates data ranges and overlays preset values dynamically. This prevents malformed config files from crashing the workstation.
- **Strict Linting Enforcement**: Transitioning from JavaScript to strict TypeScript compilation (`npm run lint`) caught numerous type-mismatch bugs and unhandled null values, resulting in an exceptionally stable release candidate.
