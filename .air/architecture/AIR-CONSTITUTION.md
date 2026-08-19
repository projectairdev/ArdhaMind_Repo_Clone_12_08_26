# AIR Engineering Constitution

This constitution establishes the non-negotiable principles governing all engineering work on **ArdhaMind**.

---

## 1. Safety & Environment Isolation

1. **Default-Deny Production Access**:
   - Production (`/opt/ArdhaMind`, Port 3000) is strictly read-only by default.
   - Any modification to production files, configuration, or processes requires explicit task permission (`production_write_allowed: true`).

2. **Zero Unapproved Deployment / Service Restarts**:
   - Automated scripts or agents must never deploy, push, merge, restart systemd services, or reload nginx without explicit task flags (`deployment_allowed: true`, `service_restart_allowed: true`).

3. **Live Broker Safety**:
   - Real money trading operations via Zerodha Kite or external brokers require `live_broker_execution_allowed: true`. Default state is `false`.

---

## 2. Code & Architecture Integrity

1. **Inspect Before Modifying**:
   - Agents must inspect existing source files, schemas, and API contracts before proposing or writing code.

2. **Root Cause Analysis**:
   - Never resolve errors by masking symptoms, commenting out assertions, or returning synthetic fallback data. Identify and fix underlying root causes.

3. **Single Canonical Source of Truth**:
   - Server-authoritative calculations must not be duplicated or re-implemented independently on the client side.

4. **Bounded Implementation Scope**:
   - Implement only the smallest complete fix required by the approved task scope. Do not expand scope or touch unrelated technical debt silently.

5. **Empirical Verification**:
   - No task is complete until verified by automated tests, build/lint checks, and empirical runtime/API confirmation.

---

## 3. Governance Enforcement & Future Hardening Architecture

1. **Current Enforcement Level**:
   - AIR framework rules, task validation, production default-deny, and scope restrictions currently operate as **AGENT-INSTRUCTION** principles in Markdown files.
   - Destructive Git operations are **PARTIALLY ENFORCED** by IDE tool guidelines.

2. **Future Mechanical Hardening Target**:
   - Subsequent hardening tasks will investigate Antigravity `PreToolUse hooks` and `permissions` to mechanically restrict high-risk operations (production file writes, service restarts, deployments, live broker execution, destructive git commands) at the execution layer.
   - Git hooks alone are recognized as insufficient because they do not prevent direct tool file edits or shell script modifications outside of Git workflows.

3. **OS-Level Production Isolation**:
   - OS-level isolation will rely on properly designed Unix user/group permissions, directory ownership, and least-privilege service configurations. Blanket recursive `chmod` operations (e.g. `chmod -R 555`) are forbidden as production requires writable paths for logs, runtime caches, and transactional persistence.

## 4. Layer 2 Mechanical Enforcement Implementation Status

The workspace now features an active, repository-local `PreToolUse` lifecycle hook configured in `.agents/hooks.json` executing `.agents/hooks/air_guard.py`:

- **Production Write**: `HARD-ENFORCED` (`DENY` for file-edit tools & shell write commands targeting `/opt/ArdhaMind`).
- **Destructive Git**: `HARD-ENFORCED` (`DENY` for `reset --hard`, `clean -fd`, `push --force`).
- **Destructive DB**: `HARD-ENFORCED` (`DENY` for `DROP DATABASE`, `TRUNCATE`, `rm *.db`).
- **Live Broker Execution**: `HARD-ENFORCED` (`DENY` for `place_order`, `exit_position`, Kite API orders).
- **Service Control**: `HARD-ENFORCED` (`ASK` for `systemctl restart`, `kill`, `pkill`, `fuser -k`).
- **Deployment / Env**: `HARD-ENFORCED` (`ASK` for `nginx` reloads, `.env.production`).
- **Safe Read & Staging Dev**: `HARD-ENFORCED` (`ALLOW` for normal low-friction staging development).
