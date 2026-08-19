# Development Protocol Rules

---

## 1. Development Lifecycle Steps

```text
DISCOVER ──► TRACE ──► ROOT CAUSE ──► BOUNDED FIX ──► TARGETED TEST ──► QUALITY GATES ──► VERIFY ──► REPORT
```

1. **Discover & Trace**: Inspect source code, error logs, and state propagation before editing.
2. **Root Cause**: Identify exact defect origin instead of patching symptoms.
3. **Bounded Fix**: Make the minimal complete code edit within approved task scope.
4. **Targeted Test**: Run relevant Pytest suites and unit tests.
5. **Quality Gates**: Run `npm run lint` (`tsc --noEmit`) and `npm run build` to confirm 0 compilation errors.
6. **Verify**: Check REST API endpoints or UI state to verify live runtime behavior.
7. **Completion Report**: Generate markdown report in `.air/reports/<task-id>.md`.

---

## 2. Single Causal Resolution

- Solve one causal defect completely in one engineering cycle instead of fragmenting work into unnecessary micro-sprints.
- Keep git diff clean and limited strictly to the approved task.
