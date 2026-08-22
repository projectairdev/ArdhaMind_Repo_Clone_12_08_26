# TRADING CHEATSHEET EXTRACTION MANIFEST

**Version:** 1.0 (Staging Consolidation Sprint)  
**Status:** Consolidated into Dedicated Feature Boundary (`src/frontend/features/trading-cheatsheet/`)

---

## 1. FILES NOW OWNED BY CHEATSHEET

The following files constitute the self-contained implementation boundary of Trading Cheatsheet:

- `src/frontend/features/trading-cheatsheet/index.ts`
- `src/frontend/features/trading-cheatsheet/TradingCheatsheetWorkspace.tsx`
- `src/frontend/features/trading-cheatsheet/data/tradingCheatsheet.ts`
- `src/frontend/features/trading-cheatsheet/README.md`
- `src/frontend/features/trading-cheatsheet/EXTRACTION_MANIFEST.md`

---

## 2. SHARED FILES STILL OUTSIDE

These files remain in the shared Ardha infrastructure layer and are referenced by or reference Trading Cheatsheet:

- `src/frontend/context/NavigationContext.tsx` (Defines `trading_cheatsheet` in `PrimaryModuleId` / `TabType`)
- `src/frontend/layout/DashboardLayout.tsx` (Mounts `TradingCheatsheetWorkspace` inside active module container)

---

## 3. ARDHA DOMAIN DEPENDENCIES

- **CanonicalWorkstationState:** NONE
- **Market Data Pipeline:** NONE
- **Options / Derivatives Engine:** NONE
- **News Engine:** NONE
- **Portfolio / Broker Service:** NONE
- **OpenAI / LLM Service:** NONE

---

## 4. BACKEND DEPENDENCIES

- **API Endpoints:** 0 Endpoints
- **Database Tables:** 0 Tables
- **Python Microservices:** 0 Services

---

## 5. CONFIG DEPENDENCIES

- **Browser Storage:** `localStorage.getItem("trading_cheatsheet_experience_level")` / `localStorage.setItem(...)` for local user preference.

---

## 6. ENVIRONMENT VARIABLES

- **Required ENV Variables:** NONE

---

## 7. ROUTING DEPENDENCIES

- Uses `useNavigation()` hook from `src/frontend/context/NavigationContext.tsx` to handle shell tab switching.

---

## 8. DESIGN SYSTEM DEPENDENCIES

- Uses Tailwind CSS utility classes.
- Uses `lucide-react` for standard UI icons.

---

## 9. TEST DEPENDENCIES

- `tests/test_trading_cheatsheet_workspace.py` (Exclusively tests Trading Cheatsheet presentation layers, zero live data invariant, and scenario engine).
- `tests/test_global_shell_rebuild.py` (Verifies sidebar item registration).

---

## 10. KNOWN EXTRACTION BLOCKERS

1. **Routing Adapter:** Replace `useNavigation` import with local router or props-based tab change callback prior to standalone package extraction.
2. **Package Bundling:** Wrap module in a standalone Vite/Next.js shell if building a separate web app product.
