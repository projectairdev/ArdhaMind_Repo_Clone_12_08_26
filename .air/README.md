# AIR Engineering Workflow — ArdhaMind

The **AIR Engineering Workflow** governs all engineering tasks, quality standards, and environment isolation policies for **AIR ArdhaMind**.

---

## Operating Lifecycle

```text
USER / LEAD
     │
     ▼
Gemini AIR Architect
     │
     ▼
PROPOSED TASK  (.air/tasks/proposed/*.md)
     │
     ▼
HUMAN REVIEW & APPROVAL
     │
     ▼
APPROVED TASK  (.air/tasks/approved/*.md)
     │
     ▼
Antigravity Executor
     │
     ├─ Environment & Permission Verification
     ├─ Architecture & Scope Audit
     ├─ Root Cause Diagnosis
     ├─ Bounded Implementation
     ├─ Tests & Quality Gates
     └─ Runtime / UI Verification
     │
     ▼
COMPLETION REPORT  (.air/reports/<task-id>.md)
     │
     ▼
HUMAN ACCEPTANCE
```

---

## Authoritative Approval & Safety Rules

1. **Approved Folder Mandate**:
   - Antigravity must **NEVER** execute tasks directly from `.air/tasks/proposed/`.
   - Only task markdown files located in `.air/tasks/approved/` are authorized for implementation.

2. **Task Permission Frontmatter**:
   - Every task must explicitly declare environment flags and permission grants:
     ```yaml
     environment: staging | production | both
     production_write_allowed: false
     deployment_allowed: false
     service_restart_allowed: false
     database_write_allowed: false
     live_broker_execution_allowed: false
     ```

3. **Default-Deny Environment Principles**:
   - Being in `.air/tasks/approved/` does **NOT** grant implicit production access.
   - Unless `production_write_allowed: true` is explicitly granted, **PRODUCTION IS READ-ONLY**.
   - Unless `deployment_allowed: true` is explicitly granted, **DEPLOYMENT IS FORBIDDEN**.
   - Unless `service_restart_allowed: true` is explicitly granted, **SERVICE RESTART IS FORBIDDEN**.
   - Unless `database_write_allowed: true` is explicitly granted, **DATABASE WRITES ARE FORBIDDEN**.
   - Unless `live_broker_execution_allowed: true` is explicitly granted, **LIVE BROKER ORDERS ARE FORBIDDEN**.

4. **Directory Structure**:
   - `.air/architecture/`: Technical constitutions, architecture graphs, and environment details.
   - `.air/tasks/proposed/`: Initial proposed tasks waiting for human review.
   - `.air/tasks/approved/`: Human-reviewed, authorized tasks ready for Antigravity execution.
   - `.air/tasks/blocked/`: Tasks blocked on dependencies or scope expansions.
   - `.air/tasks/completed/`: Finished tasks archived after acceptance.
   - `.air/templates/`: Standardized task and report templates.
   - `.air/reports/`: Immutable completion reports generated upon execution.
