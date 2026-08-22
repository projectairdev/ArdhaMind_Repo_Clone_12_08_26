# PHASE 3 — POSITION LIFECYCLE & TRADER-CONTROLLED EXIT ARCHITECTURE

**Document Version:** 1.0.0 — Authoritative Position & Exit Specification  
**Component:** `PositionLifecycleManager` (`src/broker/services/positions_service.py`) & `ExitRecommendationService` (`src/execution_engine/exit_recommendation_service.py`)  
**Scope:** Position State Truth, Real-Time Exit Intelligence, Trader Exit Authorization, Broker-Native Protective Stops  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** DESIGN COMPLETE (Staging Only — Production Untouched)

---

## 1. POSITION MODEL & BROKER-TRUTH INVARIANT

Position state is **strictly reconstructed from broker-confirmed fills and Kite position books**. Local models never fabricate positions.

```python
@dataclass
class PositionState:
    position_id: str                      # Format: POS-{session_date}-{tradingsymbol}-{seq}
    proposal_id: str                      # Lineage to TradeProposal
    decision_id: str                      # Lineage to MarketDecisionSummary
    entry_order_ids: List[str]            # Broker order IDs that created this position
    fill_records: List[Dict[str, Any]]    # [{"trade_id": "...", "qty": 50, "price": 142.5}]
    
    # Contract & Holdings Truth
    tradingsymbol: str
    instrument_token: int
    quantity: int                         # Net open quantity
    average_entry_price: float            # Weighted average fill price
    current_ltp: float                    # Real-time tick LTP
    unrealized_pnl: float                 # (LTP - AvgEntry) * Qty
    realized_pnl: float                   # Closed trade P&L
    
    # Thesis & Health Tracking
    original_setup: str                   # e.g. "PULLBACK CONTINUATION"
    thesis_status: str                    # "THESIS_INTACT" | "THESIS_WEAKENING" | "THESIS_INVALIDATED"
    active_stop_loss: float               # Spot invalidation & Option SL
    active_targets: List[float]           # Target levels [T1, T2]
    risk_at_entry_inr: float
    current_risk_inr: float
    
    # Timestamps & Context
    opened_at: str                        # ISO-8601 UTC
    holding_duration_seconds: float
    position_status: str                  # OPEN | PARTIAL_EXIT | EXIT_PENDING | CLOSED | RECONCILING
    exit_recommendation: Optional[Dict[str, Any]]
```

---

## 2. EXIT INTELLIGENCE & RECOMMENDATION ENGINE

Ardha evaluates real-time market structure and emits a deterministic `ExitRecommendation`.

### Allowed Recommendation Directives:
1. **`HOLD`:** Thesis intact, spot sustaining above trailing support, momentum constructive.
2. **`TRAIL_STOP`:** Spot advances past intermediate pivot; recommend raising stop to lock gains.
3. **`PARTIAL_EXIT`:** First target achieved ($T_1$ reached); recommend booking $50\%$ allocation.
4. **`EXIT`:** Final target reached or dynamic momentum divergence detected.
5. **`THESIS_INVALIDATED`:** Spot breaches invalidation level; immediate risk cut recommended.
6. **`TIME_EXIT`:** Post 15:15 IST intraday wrap; square-off recommended before session close.

---

## 3. TRADER-CONTROLLED EXIT APPROVAL WORKFLOW

```
[Position Monitor] ──► [Exit Recommendation: TRAIL / EXIT]
                               │
                               ▼
                   [Trader Prompt & Notification]
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
     [TRADER APPROVES]                    [TRADER REJECTS / OVERRIDES]
            │                                     │
            ▼                                     ▼
 [PreTradeSafetyGate (Exit)]               [CONTINUE MONITORING]
            │
            ▼
[ExitOrderIntent (Market/Limit)] ──► [Broker Execution] ──► [Position CLOSED]
```

- **Trader Control Invariant:** In Phase 3, Ardha **NEVER executes an exit automatically** unless the trader has explicitly configured a **broker-native Stop-Loss Order** (e.g. SL-M placed at entry).
- **Protective Stop Architecture:** Strongly mandates broker-native GTT / SL-M orders over synthetic software polling stops to safeguard capital against local server disconnection.
