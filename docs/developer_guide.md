# Developer Guide

Welcome to the development team of the **NIFTY Option Finder & Market Intelligence Workstation**! This guide details contributing standards, coding conventions, testing protocols, and pipeline extensions.

---

## 🗂️ Code Conventions and Guidelines

### 1. Zero Mutable Shared State
All engines and pipelines must be strictly stateless. Do not declare global, class-level, or static variables that change during runtime execution:
- **Incorrect**:
  ```python
  class StrategyEngine:
      active_signals = [] # Mutable shared state!
  ```
- **Correct**:
  ```python
  class StrategyEngine:
      @staticmethod
      def evaluate(context: MarketContext) -> List[StrategyScore]:
          # Stateless calculation returning an immutable list
          return ...
  ```

### 2. Type-Safe Data Models
Every engine must receive and return standard Python `@dataclass(frozen=True)` types from `src/models/` to enforce compiler integrity:
```python
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class CustomMetric:
    metric_id: str
    value: float
```

### 3. Named Imports at Top Level
Always place imports at the top of the file, and utilize named imports rather than wildcards:
- **Incorrect**: `from src.models import *`
- **Correct**: `from src.models import MarketScore, OptionContext`

### 4. Prohibited Plausible Market Data Fallbacks (Frontend Rule & Code-Review Checklist)
**Rule Intent**:
> *"fallback values must never be plausible market data — always null/undefined so the UI can render an explicit awaiting-data state."*

In the frontend codebase (React, TypeScript, view models, and adapters), never use `??` or `||` fallback expressions where the right-hand side is a numeric, date, percentage, or currency literal that mimics plausible market data. Fabricating fallback values risks misleading traders by presenting stale or synthetic quotes as real market context.

#### ❌ Prohibited Patterns:
```typescript
// NEVER use plausible market data as fallback:
const spotPrice = data.spot ?? 24080.40;          // ❌ Synthetic spot price
const activeDate = data.date ?? "2026-09-01";     // ❌ Fabricated trading date
const vixValue = data.vix ?? "10.68";             // ❌ Plausible VIX level
const supportLevel = immediateSupport || "24,180";// ❌ Fabricated support strike
const changePercent = data.changePct ?? 0.28;     // ❌ Fabricated percentage
```

#### ✅ Allowed / Compliant Patterns:
```typescript
// ALWAYS fall back to null/undefined or explicit UI empty state:
const spotPrice = data.spot ?? null;              // ✅ Explicit null -> renders awaiting-data state
const activeDate = data.date ?? null;             // ✅ Renders "--" or loading skeleton
const vixValue = data.vix ?? null;                // ✅ Clean awaiting state

// UI layout / array length fallbacks are acceptable when non-market constants:
const itemCount = items.length || 0;              // ✅ Structural/UI constant
const pageSize = config.limit ?? 10;              // ✅ Configuration default
```

#### 🔍 Fallback Review Linter:
Run the AST-based fallback scanner before submitting code:
```bash
npm run lint:fallbacks
```
Flagged expressions are highlighted for peer review to ensure all market data attributes retain truthful temporal and awaiting-data provenance.

---

## 🧪 Testing Protocol & Regression Safety

To maintain our 100% bug-free status, every change must be accompanied by unittests. We do not accept PRs that decrease overall code coverage.

### Running Existing Tests
The project features 180+ tests. Run them before staging code changes:
```bash
# Run all unittests
python3 -m unittest discover tests

# Run specific suite
python3 -m unittest tests/test_configuration_manager.py
```

### Writing a New Test Case
Store test cases in `/tests/` with the prefix `test_`. Inherit from `unittest.TestCase`:
```python
import unittest

class TestNewFeature(unittest.TestCase):
    def test_calculation(self) -> None:
        self.assertEqual(2 + 2, 4)
```

---

## ⚙️ CI/CD & Formatting Standards

Before creating a pull request, run the linters to ensure codebase compliance:
```bash
# Verify TypeScript compile (Frontend UI)
npm run lint
```
There should be NO compiler errors or warnings during development.
