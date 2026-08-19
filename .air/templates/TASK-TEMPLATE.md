---
task_id: AM-YYYY-XXX
project: AIR ArdhaMind
status: PROPOSED

environment: staging

preferred_executor: antigravity-ide

production_write_allowed: false
deployment_allowed: false
service_restart_allowed: false
database_write_allowed: false
live_broker_execution_allowed: false

created_by: Gemini AIR Architect
approved_by:
approved_at:
---

# Objective

Brief 1-2 sentence description of what this task accomplishes.

# Observed Problem / Requirement

Detailed context and problem statement.

# Expected Behaviour

Target behavior after successful task completion.

# Root-Cause Investigation Required

Hypotheses and files to inspect before changing code.

# Environment

Target environment (`staging`, `production`, or `both`).

# Active Scope

Specific components, files, and features authorized for modification.

# Protected Scope

Files, features, and environments strictly forbidden from modification.

# Architectural Invariants

Core invariants that must be preserved.

# Discovery Targets

Suspected modules to inspect (not approved implementation decisions).

# Functional Requirements

Detailed functional specifications.

# Acceptance Criteria

Measurable verification criteria.

# Verification Requirements

Automated tests, linting, build checks, and API/UI verification commands.

# Regression Requirements

Existing features that must be verified against regressions.

# Deployment / Runtime Authorization

Explicit authorization statement for services, deployments, or restarts.

# Completion Report Requirements

Expected report filename (`.air/reports/<task-id>.md`) and required sections.
