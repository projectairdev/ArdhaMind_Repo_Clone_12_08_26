# Paper and execution boundary

Classification:

- Shared domain concepts worth keeping: immutable reports, validation/audit
  fixtures and position/order read models.
- Future paper-app extraction: `src/paper_trading/`, its panel, and paper tests.
- Future execution-phase interfaces: `src/execution_engine/` and lifecycle tests.
- Dead runtime hooks removed now: `virtual_execution.py`, broker virtual
  position/order merges, bridge execution arguments/branches, and production
  paper pipeline registration.

The paper pipeline is test support only. The canonical broker always selects the
read-only Kite adapter, rejects non-Zerodha modes, and raises `PermissionError`
for place, modify, cancel and exit operations before calling a gateway. No paper
or execution object enters canonical workstation state.
