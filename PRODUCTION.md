# AIR ArdhaMind — Production Deployment & Release Guide

## System Requirements
- Node.js 18+ / npm 9+
- Python 3.10+ with active virtual environment (`new\Scripts\python.exe` or `venv`)
- Windows OS (Development and Production target)

## Production Build Instructions
1. Install dependencies:
   ```bash
   npm install
   ```

2. Run type checking & linting:
   ```bash
   npx tsc --noEmit
   ```

3. Run full automated test suite:
   ```bash
   new\Scripts\python.exe -m pytest -q -p no:cacheprovider
   ```

4. Build production bundle:
   ```bash
   npm run build
   ```

## Starting Production Application
To launch the production workstation bridge:
```bash
NODE_ENV=production node dist/server.cjs
```

## Security & Reliability Safeguards
- **Read-Only Architecture**: Order placement, modification, cancellation, and live portfolio execution commands are hard-blocked.
- **Atomic Cache Storage**: Local news and macro caches write to temporary files before atomic file replacement (`os.replace`) to prevent corruption.
- **SSRF Hardening**: All provider URL fetches validate hostname, scheme, port, and IP range to block private/link-local/metadata address exploitation.
- **REST Rate Limiting**: All Express `/api/` endpoints enforce in-memory rate limiting (max 150 requests/min per IP).
- **Graceful Provider Fallback**: Outages in News, Macro, or OpenAI layers trigger bounded fallbacks without interrupting canonical workstation state.

## E4B Verification Exception

Rendered UI verification is pending due to browser-control infrastructure failure: `Cannot redefine property: process`.

At the E4B checkpoint, pytest, TypeScript, the production build, and `git diff --check` passed; the canonical API returned healthy schema `2.0.0` state. The supported browser harness failed during its own initialization before page navigation, with no corresponding AIR ArdhaMind application exception. The six-workspace rendered smoke check must be rerun when the supported browser harness is operational.
