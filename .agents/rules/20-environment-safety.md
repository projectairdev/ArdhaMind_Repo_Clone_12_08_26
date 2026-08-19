# Environment Safety & Isolation Rules

---

## 1. Environment Verification

Before executing runtime or deployment operations, Antigravity MUST verify:
1. Current working directory
2. Git status and branch
3. Target environment (`staging` vs `production`)
4. Target process, port, and service
5. Task permission flags

---

## 2. Production Default-Deny Principles

- **PRODUCTION IS READ-ONLY**: Unless the approved task explicitly specifies `production_write_allowed: true`, production (`/opt/ArdhaMind`, Port 3000) is strictly read-only.
- **DEPLOYMENT IS FORBIDDEN**: Unless `deployment_allowed: true`, no code may be deployed, pushed, or merged.
- **SERVICE RESTARTS FORBIDDEN**: Unless `service_restart_allowed: true`, systemd services or production processes may not be restarted.
- **DATABASE WRITES FORBIDDEN**: Unless `database_write_allowed: true`, production database schemas or files may not be modified.
- **LIVE BROKER FORBIDDEN**: Unless `live_broker_execution_allowed: true`, no orders may be submitted to Zerodha Kite or external brokers.

---

## 3. Production Escalation Protocol

Before performing any write operation on production, Antigravity MUST verify:
- Target path == `/opt/ArdhaMind`
- Approved task file exists in `.air/tasks/approved/`
- `production_write_allowed == true`
- Current git status clean
- Recovery / rollback path understood

If any condition is not met: **STOP** immediately and report `SCOPE_EXPANSION_REQUIRED` or `BLOCKED`.
