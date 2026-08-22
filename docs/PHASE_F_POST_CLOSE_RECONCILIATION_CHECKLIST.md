# PHASE F — POST-CLOSE RECONCILIATION CHECKLIST

**Document Version:** 1.0.0 — Authoritative Post-Close Checklist  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Execution Window:** Monday 2026-08-24 (15:30 IST → 15:45 IST)  

---

## 1. RECONCILIATION STEPS

```
[ ] 1. 15:30 IST — Confirm transition to CLOSE_PENDING state.
[ ] 2. 15:30:15 IST — Confirm ingestion stream remains alive for weighted average ticks.
[ ] 3. 15:35:00 IST — Fetch official settled close from Kite Quote API (`OHLC.close`).
[ ] 4. 15:35:30 IST — Apply CloseReconciliationPolicy:
      - Compare candidate close from 15:29:59 against official settled close.
      - If delta <= 5.0 pts -> MATCHED / WITHIN_TOLERANCE.
      - If delta > 5.0 pts -> Update to official settled close (CORRECTED_FROM_PROVIDER).
[ ] 5. 15:38:00 IST — Finalize SessionCloseCore (data/session_store/close/2026-08-24.json).
[ ] 6. 15:38:30 IST — Finalize OptionsCloseBaseline (data/session_store/options_close/2026-08-24.json).
[ ] 7. 15:39:00 IST — Finalize SessionIntegrityEnvelope (data/session_store/integrity/2026-08-24.json).
[ ] 8. 15:40:00 IST — Run RetentionManager.prune_expired_records().
[ ] 9. 15:42:00 IST — Perform shadow diff between legacy session_history and lightweight artifacts.
[ ] 10. 15:45:00 IST — Complete Phase F Acceptance Report.
```
