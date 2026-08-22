# LIGHTWEIGHT STORAGE RETENTION & PRUNING POLICY SPECIFICATION

**Document Version:** 1.1.0 — Authoritative Corrected Retention Policy  
**Target Module:** `src/storage/retention_manager.py`

---

## 1. DOMAIN-BY-DOMAIN RETENTION POLICY

| Storage Domain | Artifact Path | Retention Window | Storage Mechanism | Estimated File Size | Lifetime Growth Projections |
|:---|:---|:---:|:---:|:---:|:---|
| **Session Close Core** | `data/session_store/close/YYYY-MM-DD.json` | **PERMANENT** | Individual JSON per date | ~3.8 KB / session | 250 sessions (1 Year) = **~950 KB**; 5 Years = **~4.7 MB** |
| **Options Close Baseline** | `data/session_store/options_close/YYYY-MM-DD.json` | **PERMANENT** | Individual JSON per date | ~2.1 KB / session | 250 sessions (1 Year) = **~525 KB**; 5 Years = **~2.6 MB** |
| **Session Integrity Envelope** | `data/session_store/integrity/YYYY-MM-DD.json` | **PERMANENT** | Individual JSON per date | ~1.8 KB / session | 250 sessions (1 Year) = **~450 KB**; 5 Years = **~2.2 MB** |
| **Rolling Candle Cache** | `data/session_store/cache/nifty_5m_candles.json` | **Rolling 5 Trading Sessions** (375 bars) | Single rolling JSON file | ~32.4 KB total | Fixed ceiling: **~32.4 KB total** |
| **Intraday Telemetry Series** | `data/session_store/telemetry/YYYY-MM-DD.json` | **Rolling 5 Trading Sessions** | Individual JSON per date | ~4.2 KB / session | Fixed ceiling: 5 files = **~21.0 KB total** |
| **Connectivity Event Log** | `data/session_store/connectivity/YYYY-MM-DD.jsonl` | **Rolling 30 Trading Sessions** | Append-only JSONL | ~1.5 KB / session | 30 files = **~45.0 KB total** |
| **Active Catalysts & Themes** | `data/session_store/cache/active_catalysts.json` | **Active Items + 5-day resolved** | Single rolling JSON file | ~4.6 KB total | Fixed ceiling: **~4.6 KB total** |
| **Latest Recovery Snapshot** | `data/session_store/cache/latest_canonical_state.json` | **Latest 1 Valid State** | Atomic single JSON | ~40.0 KB total | Fixed ceiling: **~40.0 KB total** |
| **Closed Trade Journal (M5)** | `data/portfolio_journal.db` | **PERMANENT AUDIT** | SQLite Database | ~2.0 KB / trade | Permanent compliance ledger |
| **Proposal Decision Lineage** | `data/proposals_audit.db` | **PERMANENT AUDIT** | SQLite Database | ~1.5 KB / proposal | Permanent audit trail |
| **Prediction Accuracy Records** | `data/performance_records/*.json` | **PERMANENT AUDIT** | Individual JSON / SQLite | ~1.2 KB / record | Permanent longitudinal accuracy ledger |

---

## 2. AGGREGATE STORAGE FOOTPRINT PROJECTIONS

$$\text{Fixed Active Operational Working Set} = 32.4\text{ KB} + 21.0\text{ KB} + 45.0\text{ KB} + 4.6\text{ KB} + 40.0\text{ KB} = \mathbf{143.0\text{ KB}}$$

$$\text{Annual Permanent Market History Growth (250 sessions)} = 250 \times (3.8\text{ KB Close} + 2.1\text{ KB Options} + 1.8\text{ KB Integrity}) = \mathbf{1.92\text{ Megabytes / Year}}$$

### Comparison vs Legacy Snapshot Architecture

| Horizon | Legacy Snapshot Architecture (`session_history_*.json`) | Lightweight Session Storage Subsystem | Net Savings |
|:---:|:---:|:---:|:---:|
| **1 Day** | **~40.0 MB** | **~47.1 KB** | **99.88%** |
| **1 Month (20 trading days)** | **~800.0 MB** | **~300.0 KB** | **99.96%** |
| **1 Year (250 trading days)** | **~10.0 Gigabytes** | **~2.1 Megabytes** | **99.98% (4,760x reduction)** |
| **5 Years** | **~50.0 Gigabytes** | **~9.7 Megabytes** | **99.98%** |

---

## 3. AUTOMATED PRUNING LIFECYCLE ALGORITHM

```python
def prune_expired_sessions(base_dir: Path, max_sessions: int = 5) -> None:
    """
    Prunes rolling directories strictly by trading-session count.
    SessionCloseCore, OptionsCloseBaseline, and Integrity Envelopes are PERMANENT.
    """
    rolling_targets = [
        (base_dir / "telemetry", 5),
        (base_dir / "connectivity", 30),
    ]
    for target_dir, max_count in rolling_targets:
        if not target_dir.exists():
            continue
        files = sorted(target_dir.glob("*.*"), key=lambda p: p.name, reverse=True)
        if len(files) > max_count:
            for old_file in files[max_count:]:
                try:
                    old_file.unlink()
                except Exception as exc:
                    logger.warning(f"Could not prune {old_file.name}: {exc}")
```
