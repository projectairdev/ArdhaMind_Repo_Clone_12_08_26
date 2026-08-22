# PHASE F — LIVE ACCEPTANCE REPORT TEMPLATE

**Session Date:** Monday 2026-08-24  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Operator:** Antigravity / Lead Engineer  
**Status:** PENDING REAL LIVE NSE OBSERVATION (To be populated strictly during live market)  

---

## 1. EXECUTIVE EVIDENCE SUMMARY

*Note: Timings must be recorded in high-resolution format (`HH:MM:SS.mmm IST`, e.g. `09:15:01.284 IST`). All fields must remain blank until actual Monday observations occur.*

```
1. Git Baseline Commit:
2. Service & Process Health:
3. Runtime Identity Continuity:
   - runtime_id at startup:
   - runtime_id at close:
   - Runtime ID Changed (Restart/Recovery): [ YES / NO ] (If yes, explain:               )
4. Canonical Sequence Monotonicity:
   - First live canonical_sequence (at ~09:15:00):
   - Final reconciled canonical_sequence (at ~15:40:00):
   - Monotonic Sequence Advance Confirmed: [ YES / NO ]
5. Broker Authentication Verified At:                   IST (e.g. 08:45:12.104 IST)
6. WebSocket Connected At:                              IST (e.g. 08:45:14.320 IST)
7. Subscriptions Restored At:                           IST (e.g. 08:45:15.890 IST)
8. First Real NIFTY Tick At:                            IST (Price:             )
9. First Breadth Observed At:                           IST
10. First India VIX Observed At:                        IST
11. First Options Observed At:                          IST
12. Canonical State Live At:                            IST
13. Intelligence Layer Ready At:                        IST
14. Stream Gaps Observed:
15. Natural Reconnect Events:
16. Critical Shadow Mismatches:
17. Lightweight Recovery Write Integrity:
18. Rolling 5m Candle Integrity:
19. 15-Minute Telemetry Series Integrity:
20. Connectivity Log Integrity:
21. 15:20 Valid Options Capture:
22. 15:30 CLOSE_PENDING State Transition:
23. EOD Close Reconciliation Outcome:
24. SessionCloseCore Verification:
25. OptionsCloseBaseline Verification:
26. SessionIntegrityEnvelope Verification:
27. Total Storage Generated (Legacy vs Lightweight):
28. Critical Data Gaps Breakdown:
    - Recovered Critical Gaps:
    - Unrecovered Critical Gaps:
    - Unrecoverable Option Evidence Gaps:
29. Market Decision Summary Live Behavior:
30. Next-Session Pre-Market Status: PENDING NEXT PRE-MARKET
31. Evidence Package Complete: [ YES / NO ]
    Required Evidence Checklist:
    [ ] Live observation log (08:45 -> 15:40 IST)
    [ ] Exact first-tick timestamps (millisecond precision)
    [ ] Shadow comparison (legacy session_history vs lightweight store)
    [ ] Lightweight store artifacts (latest_canonical, candles, telemetry)
    [ ] Connectivity log (2026-08-24.jsonl)
    [ ] 15:20 pre-close options capture proof
    [ ] 15:30 CLOSE_PENDING state transition evidence
    [ ] Post-close reconciliation execution record
    [ ] Final SessionCloseCore (close/2026-08-24.json)
    [ ] Final OptionsCloseBaseline (options_close/2026-08-24.json)
    [ ] Final SessionIntegrityEnvelope (integrity/2026-08-24.json)

32. Phase F Acceptance Verdict: [ PASS / FAIL ]
    (Rule: PASS = Real live NSE evidence + Zero critical shadow mismatches + Zero unreconciled critical data gaps + Valid final artifacts)

33. Phase G Decommissioning Recommendation:
```
