# Contributing to AIR ArdhaMind

Welcome to the AIR ArdhaMind project. AIR ArdhaMind is a read-only NIFTY 50 intelligence workstation built for institutional reliability, deterministic analytics, and uncompromising data integrity.

---

## 🛡️ Absolute Safety & Data Truth Principles

1. **Read-Only Invariant**: Never add order execution, broker state mutation, or trading actions.
2. **Never Fabricate Market Data**: Missing data is `null`/`undefined`, never synthetic or guessed.
3. **Plausible Market Data Fallback Prohibition**:
   > *"fallback values must never be plausible market data — always null/undefined so the UI can render an explicit awaiting-data state."*

---

## 📋 Code Review Checklist

Before approving any pull request or staging frontend changes, verify the following checklist items:

- [ ] **No Plausible Market Data Fallbacks**:
  - `??` and `||` fallbacks must never resolve to plausible market numbers (e.g. `?? 24080.40`), plausible dates (e.g. `?? "2026-09-01"`), percentages (e.g. `?? "10.68"`), or formatted strike strings (e.g. `|| "24,520"`).
  - Unloaded or missing data must remain `null`/`undefined` so that UI views can render an explicit awaiting-data / empty skeleton state.
  - Non-market structural constants (such as array lengths `items.length || 0` or pagination defaults `limit ?? 10`) are legitimate.
- [ ] **Type Safety**:
  - TypeScript compiles cleanly without error (`npm run lint` / `npx tsc --noEmit`).
- [ ] **Fallback Review Scan**:
  - Run `npm run lint:fallbacks` to scan for expressions flagged for peer review.
- [ ] **Stateless Backend Engines**:
  - Backend engines maintain zero mutable shared state and return frozen dataclasses.
- [ ] **Automated Test Coverage**:
  - All regression test suites pass (`pytest`).

---

## 🛠️ Developer Commands

```bash
# Type-check frontend code
npm run lint

# Scan for plausible market data fallback expressions
npm run lint:fallbacks

# Build production bundle
npm run build

# Run automated tests
pytest -q -p no:cacheprovider
```

For full architectural guidelines, refer to [docs/developer_guide.md](file:///p:/ArdhaMind-Local/ardhamind/staging/docs/developer_guide.md).
