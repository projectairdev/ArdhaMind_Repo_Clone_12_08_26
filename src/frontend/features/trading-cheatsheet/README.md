# Trading Cheatsheet Feature Module

## Feature Purpose
Trading Cheatsheet is an adaptive, single-source trading reference and scenario computation engine for Indian equity and options markets (NIFTY / BANKNIFTY). It presents trading concepts across 3 experience levels (**BEGINNER**, **INTERMEDIATE**, **ADVANCED**) and includes a multi-layered scenario explorer and metric detail popover system.

---

## Public Entry Point
- **`src/frontend/features/trading-cheatsheet/index.ts`**
  - Exports `TradingCheatsheetWorkspace` component.
  - Exports TypeScript interfaces for domain concepts, scenario states, and presentation models.

---

## Folder Structure
```
src/frontend/features/trading-cheatsheet/
├── index.ts                            # Public module entry point
├── TradingCheatsheetWorkspace.tsx      # Main workspace component & presentation UI
├── data/
│   └── tradingCheatsheet.ts            # Canonical domain knowledge base & scenario logic
├── README.md                           # Feature module documentation (this file)
└── EXTRACTION_MANIFEST.md              # Explicit manifest of owned/shared assets & readiness
```

---

## Internal Dependencies
- `TradingCheatsheetWorkspace.tsx` imports domain constants, concept models, and scenario evaluation helpers directly from `./data/tradingCheatsheet`.

---

## External / Shared Dependencies
1. **Icon Library**: `lucide-react` (standard icon components: `BookOpen`, `Info`, `Search`, `Shield`, `Zap`, etc.).
2. **Navigation Context**: `../../context/NavigationContext` (`useNavigation()` hook to interact with shell navigation).
3. **Design System Tokens / Classes**: Standard Tailwind CSS utility classes.

---

## Backend Dependencies
- **0 Backend Endpoints**: Trading Cheatsheet is 100% self-contained and client-side. It makes no HTTP requests and relies on no Python backend services.

---

## Canonical-State Dependencies
- **0 Live Market State Coupling**: Trading Cheatsheet does not import or subscribe to `CanonicalWorkstationState`, Kite ticker, broker data, news feeds, or options chain pipelines.

---

## Assets
- No external media or static image files. All visual indicators use inline SVG icons from `lucide-react`.

---

## Shell Routes & Tabs
- Tab ID: `trading_cheatsheet`
- Registered in: `src/frontend/context/NavigationContext.tsx`
- Rendered in: `src/frontend/layout/DashboardLayout.tsx`

---

## Test Suites
- Primary Test Suite: `tests/test_trading_cheatsheet_workspace.py`
  - Validates zero live data dependencies.
  - Validates 3 experience level presentation layers.
  - Validates scenario taxonomy alignment.

---

## Extraction Blockers & Requirements for Standalone Product
1. **Navigation Context Decoupling**: Currently imports `useNavigation()` from Ardha shell context. For standalone deployment, replace with a local routing adapter or standard router.
2. **Standalone App Wrapper**: Wrap component in a dedicated Vite/Next.js shell if deployed as an independent domain.

---

## Extraction Readiness Rating
- **READY (98% / 100%)**
  - Completely isolated domain logic and UI.
  - 0 backend or database dependencies.
  - Zero coupling to live market data streams.
