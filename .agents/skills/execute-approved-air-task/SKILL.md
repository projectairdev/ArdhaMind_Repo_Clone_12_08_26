---
name: execute-approved-air-task
description: Executes an approved AIR task file (.air/tasks/approved/<task-id>.md) while enforcing environment permissions and generating completion reports.
---

# Execute Approved AIR Task Skill

This skill provides step-by-step instructions for Antigravity when executing an approved task inside **AIR ArdhaMind**.

---

## Workflow Steps

### Step 1: Task Authorization Check
1. Search for the task file in `.air/tasks/approved/<task-id>.md`.
2. **REFUSE EXECUTION** if the task file is missing or only exists in `.air/tasks/proposed/`.
3. Read the task markdown frontmatter completely and extract permission flags:
   - `environment`: `staging` | `production` | `both`
   - `production_write_allowed`: `true` | `false`
   - `deployment_allowed`: `true` | `false`
   - `service_restart_allowed`: `true` | `false`
   - `database_write_allowed`: `true` | `false`
   - `live_broker_execution_allowed`: `true` | `false`

---

### Step 2: Environment Safety Check
1. Verify working directory (`pwd`), git branch, and git status.
2. Confirm target path matches authorization:
   - Staging: `/opt/ardhamind/staging`
   - Production: `/opt/ArdhaMind`
3. If task targets production (`production`) and `production_write_allowed == false`:
   - **ENFORCE READ-ONLY MODE**. Deny any write/edit commands on production files.

---

### Step 3: Discovery & Root Cause Analysis
1. Inspect source files listed in task `Discovery Targets`.
2. Perform code searches and view relevant files.
3. Establish empirical root cause before modifying code.
4. Verify if active task scope is sufficient. If modifications to protected scope are required:
   - Stop and report `SCOPE_EXPANSION_REQUIRED`.

---

### Step 4: Bounded Fix & Implementation
1. Execute necessary file edits within approved active scope.
2. Do not modify unrelated files or technical debt.

---

### Step 5: Verification & Quality Gates
1. Run automated test suites (e.g. `PYTHONPATH=. .venv/bin/python -m pytest <test-file>`).
2. Run TypeScript linting and build checks (`npm run lint && npm run build`).
3. Verify live REST API or UI state.
4. Verify production status (`git -C /opt/ArdhaMind status --porcelain` is clean).

---

### Step 6: Completion Report Generation
1. Write completion report to `.air/reports/<task-id>.md`.
2. Document root cause, findings, changed files, verification outputs, and final status (`COMPLETE_VERIFIED`).
3. Leave changes uncommitted for human review (do not commit, push, deploy, or restart services unless explicitly authorized).
