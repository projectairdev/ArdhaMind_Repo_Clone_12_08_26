# Architecture Cleanup Verification Log

All times are Asia/Calcutta (IST). Commands were run from `E:\AIR\ArdhaMind01`.

## 2026-08-06 — Checkpoint 1 baseline

| Command | Exit | Result |
|---|---:|---|
| `python --version` | 0 | Python 3.12.0 |
| `node --version` | 0 | v24.14.1 |
| `npm --version` | 0 | 10.8.1 |
| `git --version` | 0 | 2.45.2.windows.1 |
| `git init -b main` | 0 | New repository initialized |
| `git config --get user.name` | 0 | `pvpk06` |
| `git config --get user.email` | 0 | `pvpk06@gmail.com` |
| `python -m pytest -q -p no:cacheprovider` using system Python | 1 | `pytest` is not installed in the system interpreter |
| `new\Scripts\python.exe -m pytest -q -p no:cacheprovider` | 0 | 231 passed; 109 warnings; 4.24 seconds on final baseline run |
| Original `npm run lint` before `tsconfig` hygiene | 1 | TypeScript scanned `new/Lib/site-packages/.../stable-link.js` and failed with TS1102 |
| `npm run lint` after scoped `tsconfig.json` | 0 | TypeScript application check passed |
| `npm run build` | 0 | Vite and Express bundle passed; main JS 600.86 kB and generated a chunk-size warning |
| `new\Scripts\python.exe src\server_bridge.py --action get_workspace` | 1 | `ModuleNotFoundError: No module named 'src'` without `PYTHONPATH=.` |
| `new\Scripts\python.exe -m src.server_bridge --action get_workspace` | 0 | Process returned JSON error `Unknown action: get_workspace`; action is not implemented |

### Interpretation

- The expected 231-test Python baseline is confirmed.
- The original TypeScript failure was repository-scope pollution, not an application type error.
- The permitted `tsconfig.json` hygiene change restores a meaningful type check.
- The production frontend/server build passes.
- No separate ESLint command or frontend test command is configured.
- No documented standalone smoke action succeeds exactly as attempted; Express supplies `PYTHONPATH=.` when it starts the daemon, so the direct-file import failure is launch-context dependent.
- No real broker operation was attempted.

