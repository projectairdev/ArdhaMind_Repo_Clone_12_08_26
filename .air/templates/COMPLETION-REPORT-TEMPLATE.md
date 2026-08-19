# Completion Report: [TASK-ID] — [TASK TITLE]

## Task Metadata
- **Task ID**: [TASK-ID]
- **Environment**: [staging | production | both]
- **Authorized Permissions**:
  - `production_write_allowed`: [true | false]
  - `deployment_allowed`: [true | false]
  - `service_restart_allowed`: [true | false]
  - `database_write_allowed`: [true | false]
  - `live_broker_execution_allowed`: [true | false]

---

## 1. Root Cause & Discovery Findings
Summary of root cause analysis and evidence discovered.

## 2. What Changed
Detailed list of architectural, analytical, or governance changes made.

## 3. Files & Modules Changed
- `path/to/file1`: Explanation
- `path/to/file2`: Explanation

## 4. Verification Results
- **Automated Tests**: Pytest command & output status
- **Typecheck & Build**: `npm run lint` & `npm run build` output status
- **Runtime / API Verification**: API endpoint responses
- **UI Verification**: Dashboard state

## 5. Environment & Production Safety Verification
- **Production Status**: `git -C /opt/ArdhaMind status --porcelain` status
- **Deployments / Restarts**: Actions taken or confirmed prohibited

## 6. Final Status
`COMPLETE_VERIFIED` | `IMPLEMENTED_NOT_FULLY_VERIFIED` | `BLOCKED` | `SCOPE_EXPANSION_REQUIRED` | `FAILED`
