---
task_id: AM-TEST-001
project: AIR ArdhaMind
status: APPROVED

environment: both
preferred_executor: antigravity-ide

production_write_allowed: false
deployment_allowed: false
service_restart_allowed: false
database_write_allowed: false
live_broker_execution_allowed: false

created_by: AIR Engineering Workflow Setup
approved_by: User
approved_at: workflow-bootstrap
---

# Objective

Audit the currently opened ArdhaMind repository and determine whether the AIR engineering workflow correctly understands staging and production boundaries.

# Observed Problem / Requirement

Verify the newly established AIR workflow, rules, permissions, and report generation mechanism without modifying any application source code or runtime environment.

# Expected Behaviour

Antigravity executes a complete read-only workspace audit, verifies environment isolation, and generates `.air/reports/AM-TEST-001.md`.

# Root-Cause Investigation Required

N/A (Read-only setup verification).

# Environment

`both` (Read-only inspection of both staging `/opt/ardhamind/staging` and production `/opt/ArdhaMind`).

# Active Scope

Workspace documentation and governance files in `.air/` and `.agents/`.

# Protected Scope

Application source code (`src/`), server entrypoints (`server.ts`, `dist/`), tests (`tests/`), configuration files, systemd, nginx, broker credentials, databases, production repository `/opt/ArdhaMind`.

# Architectural Invariants

Zero application code mutations. Zero production writes.

# Discovery Targets

- Repository architecture
- Staging runtime on Port 3001
- Production status on Port 3000

# Functional Requirements

1. Verify `.air/` and `.agents/` workflow structure.
2. Audit staging and production environment boundaries.
3. Generate completion report `.air/reports/AM-TEST-001.md`.

# Acceptance Criteria

- All application files remain 100% untouched (`src/`, `tests/`, `server_bridge.py`).
- Production path `/opt/ArdhaMind` status is clean.
- Completion report `.air/reports/AM-TEST-001.md` created with `COMPLETE_VERIFIED`.

# Verification Requirements

- `git status` check
- `git -C /opt/ArdhaMind status --porcelain` check

# Deployment / Runtime Authorization

NONE. Strictly read-only task.

# Completion Report Requirements

Generate report at `.air/reports/AM-TEST-001.md`.
