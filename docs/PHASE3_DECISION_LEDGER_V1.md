# PHASE 3 — IMMUTABLE DECISION LEDGER V1 SPECIFICATION

**Document Version:** 1.0.0 — Authoritative Ledger Architecture  
**Component:** `DecisionLedger` (`src/storage/decision_ledger/`)  
**Scope:** Event-Sourced Immutable System of Record for Market Decisions, Proposals, Approvals, and Execution Truth  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** DESIGN COMPLETE (Staging Only — Production Untouched)

---

## 1. PURPOSE & CORE INVARIANTS

The **Decision Ledger** replaces hindsight-based trade reconstruction by capturing an **immutable, append-only historical record** of:
- **WHAT ARDHA KNEW:** Canonical market data, option chain depth, breadth, and VIX.
- **WHAT ARDHA SAID:** Market bias, setup, target strike, entry trigger, and confidence score.
- **WHEN IT SAID IT:** High-resolution ISO-8601 timestamps and canonical sequence numbers.
- **WHY IT SAID IT:** Supporting evidence chips, pivot zones, and invalidation boundaries.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              DECISION LEDGER INVARIANTS                                │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Immutable & Append-Only: Records once written are cryptographically hashed & frozen │
│ 2. Zero Hindsight Mutation: Performance evaluation reads historical ledger data only   │
│ 3. Event-Sourced: Records structural transitions, not every micro-tick                 │
│ 4. Deterministic Lineage: Binds Decision -> Proposal -> Approval -> Intent -> Order   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. DECISION LEDGER SCHEMA & EVENT TAXONOMY

### Allowed Event Types:
- `DECISION_QUALIFIED`: `MarketDecisionSummary` reached actionable state.
- `PROPOSAL_GENERATED`: Immutable `TradeProposal` created.
- `APPROVAL_REQUESTED`: Presented to trader on UI.
- `TRADER_APPROVED`: Trader authorized proposal (with authorized quantity & limit).
- `TRADER_REJECTED`: Trader explicitly dismissed proposal.
- `SAFETY_EVALUATED`: `PreTradeSafetyGate` result recorded.
- `ORDER_SUBMITTED`: `OrderIntent` dispatched to Kite.
- `ORDER_FILLED`: Broker fill confirmed and stamped.
- `EXIT_RECOMMENDED`: Structural exit recommendation generated.
- `POSITION_CLOSED`: Final position square-off confirmed.

---

## 3. DECISION LEDGER RECORD STRUCTURE

```python
@dataclass(frozen=True)
class DecisionLedgerRecord:
    record_id: str                        # UUIDv7 / Sequential ledger ID
    session_date: str                     # YYYY-MM-DD
    timestamp_utc: str                    # ISO-8601
    canonical_sequence: int               # Workstation state sequence
    event_type: str                       # From event taxonomy above
    
    # Core Entity Identifiers
    decision_id: str
    opportunity_id: Optional[str]
    proposal_id: Optional[str]
    approval_id: Optional[str]
    order_intent_id: Optional[str]
    broker_order_id: Optional[str]
    
    # Snapshot Data Payload (Immutable JSON)
    payload: Dict[str, Any]
    
    # Cryptographic Integrity
    previous_record_hash: str
    record_hash: str                      # SHA256(previous_hash + payload + timestamp)
```
