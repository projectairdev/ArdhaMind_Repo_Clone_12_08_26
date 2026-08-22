# PHASE F — AUTHORITATIVE LIVE ACCEPTANCE CRITERIA

**Document Version:** 1.0.0 — Authoritative Acceptance Contract  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Scope:** Strict PASS / FAIL Gates for Monday Live Observation  

---

## 1. MANDATORY PASS CRITERIA (ALL MUST BE SATISFIED)

1. **Real-Time Live Observation:** Observed real NSE session on Monday 2026-08-24 from 08:45 to 15:40 IST with actual recorded timestamps.
2. **Dual-Write Shadow Operational:** Legacy `session_history_2026-08-24.json` and `data/session_store/` write concurrently without exceptions.
3. **Critical Shadow Mismatches = 0:** Zero discrepancies between legacy and lightweight stores for Spot OHLC, close candidate, canonical sequence, and key option levels.
4. **Latest Valid Options Protection:** 15:20 valid options snapshot is locked and stored in `OptionsCloseBaseline` without post-market empty packet overwrite.
5. **Close Reconciliation Clean:** Final close settles and records in `SessionCloseCore` using `CloseReconciliationPolicy`.
6. **Zero Unreconciled Critical Data Gaps:** Any natural network disconnection is fully recovered without unresolvable structural data loss.
7. **Session Integrity Envelope Finalized:** Envelope written with full connectivity timeline and finalized state.
8. **Retention Policy Enforced:** Lightweight pruning runs cleanly; rolling caches adhere to policy windows.

---

## 2. AUTOMATIC FAIL CRITERIA

- Any lightweight artifact corrupt or failing JSON schema validation.
- Legacy writes crash or block workstation execution.
- 15:20 pre-close valid options overwritten by empty post-market packet.
- Unreconciled critical data gap remaining at 15:40 IST.
- Fabricated or synthetic market data generated for missing ticks.
