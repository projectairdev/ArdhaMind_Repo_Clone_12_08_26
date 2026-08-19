# ArdhaMind Architecture & Data Flow Rules

---

## 1. Verified Analytical Pipeline Chain

```text
Market Feed Provider
  └── Normalization
        └── Options Engine (Max Pain, Walls, PCR)
              └── Market Context Builder (Spot, VWAP, Range)
                    └── Opportunity Engine (Detectors, Scoring)
                          └── Pre-Market & Strategy Engines (Scenarios, Corridors)
                                └── CanonicalWorkstationState
                                      └── Server Bridge Daemon & WebSocket / REST API
                                            └── React Workstation UI
```

## 2. Component Ownership Rules

- **Single Analytical Ownership**: Python backend (`src/`) owns options calculations, opportunity detection, pre-market briefings, and evaluation engines.
- **Node Server (`server.ts`)**: Acts as a lightweight API gateway and static server without recreating analytical logic.
- **React Frontend (`src/frontend/`)**: Renders trader workstation components using server-emitted state. React components must not duplicate Python mathematical calculations.
