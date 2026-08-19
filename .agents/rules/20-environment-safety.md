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

---

## 4. Layer 2 Mechanical Enforcement Matrix

| Category | Target Pattern | Mechanical Intercept | Status |
| :--- | :--- | :--- | :--- |
| **Safe Read** | `git status`, `git log`, `grep`, `cat`, `view_file` | `PreToolUse` hook -> `ALLOW` | `HARD-ENFORCED` |
| **Staging Dev** | File edits inside `/opt/ardhamind/staging/` | `PreToolUse` hook -> `ALLOW` | `HARD-ENFORCED` |
| **Production Read** | `git -C /opt/ArdhaMind status`, read tools | `PreToolUse` hook -> `ALLOW` | `HARD-ENFORCED` |
| **Production Write** | File edits/shell writes targeting `/opt/ArdhaMind` | `PreToolUse` hook -> `DENY` | `HARD-ENFORCED` |
| **Destructive Git** | `git reset --hard`, `git clean -fd`, `git push --force` | `PreToolUse` hook -> `DENY` | `HARD-ENFORCED` |
| **Service Control** | `systemctl restart`, `kill`, `pkill`, `fuser -k` | `PreToolUse` hook -> `ASK` | `HARD-ENFORCED` |
| **Deployment / Env** | `nginx` config edits/reload, `.env.production` | `PreToolUse` hook -> `ASK` | `HARD-ENFORCED` |
| **Destructive DB** | `DROP DATABASE`, `DROP TABLE`, `TRUNCATE`, `rm *.db` | `PreToolUse` hook -> `DENY` | `HARD-ENFORCED` |
| **Live Broker** | `place_order`, `modify_order`, `exit_position`, Kite API | `PreToolUse` hook -> `DENY` | `HARD-ENFORCED` |
