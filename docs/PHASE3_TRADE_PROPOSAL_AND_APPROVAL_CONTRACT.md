# PHASE 3 — TRADE PROPOSAL & TRADER APPROVAL CONTRACT

**Document Version:** 1.0.0 — Authoritative Contract Specification  
**Scope:** Typed Schemas, Lifecycle States, Expiry Invariants, and Human-in-the-Loop Interaction Contracts  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** DESIGN COMPLETE (Staging Only — Production Untouched)

---

## 1. TRADE PROPOSAL DTO CONTRACT

A `TradeProposal` is a deterministic, typed, immutable structure generated when a `MarketDecisionSummary` reaches `READY_FOR_APPROVAL`.

```python
@dataclass(frozen=True)
class TradeProposal:
    proposal_id: str                      # Format: PROP-{session_date}-{decision_id_hash}-{seq}
    decision_id: str                      # Lineage to MarketDecisionSummary
    opportunity_id: str                   # Lineage to OpportunityRegistry
    created_at: str                       # ISO-8601 UTC timestamp
    session_date: str                     # Format: YYYY-MM-DD
    canonical_sequence: int               # Workstation state sequence number
    runtime_id: str                       # Active runtime identifier
    
    # Contract Specifications
    underlying: str                       # "NIFTY 50"
    tradingsymbol: str                    # e.g., "NIFTY2682724300CE"
    instrument_token: int                 # Broker instrument token
    expiry_date: str                      # Format: YYYY-MM-DD
    option_type: str                      # "CE" | "PE"
    strike_price: float                   # e.g., 24300.0
    
    # Trade Setup & Parameters
    direction: str                        # "LONG" | "SHORT"
    setup_name: str                       # e.g., "PULLBACK CONTINUATION"
    entry_condition: str                  # Structured trigger statement
    reference_spot_price: float           # Spot at proposal generation
    reference_option_ltp: float           # Option LTP at proposal generation
    recommended_quantity: int             # Deterministic lot-sized allocation
    recommended_order_type: str           # "LIMIT" | "SL-M" | "MARKET"
    recommended_limit_price: Optional[float]
    
    # Risk & Boundaries
    invalidation_level: float             # Spot invalidation boundary
    stop_loss_price: float                # Target option stop level
    target_prices: List[float]            # Scaled target levels [T1, T2]
    max_capital_allocation: float         # In INR
    estimated_risk_inr: float             # Sizing * (Entry - Stop)
    risk_reward_ratio: float              # e.g., 2.2
    
    # Multi-Factor Context
    confidence_score: int                 # 0 - 100
    liquidity_grade: str                  # "EXCELLENT" | "GOOD" | "FAIR" | "POOR"
    data_quality_grade: str               # "HIGH" | "MEDIUM" | "LOW" | "DEGRADED"
    overall_risk_grade: str               # "LOW" | "MODERATE" | "HIGH" | "VERY_HIGH"
    
    # Audit & Provenance
    supporting_evidence: List[str]        # Max 3-5 chips
    blocking_reasons: List[str]           # Empty if proposal is clean
    proposal_status: str                  # DRAFT | READY_FOR_REVIEW | WAITING_FOR_APPROVAL | APPROVED | REJECTED | EXPIRED | INVALIDATED | BLOCKED
    proposal_expiry_at: str               # ISO-8601 UTC (Hard timeout, e.g. created_at + 120s)
    policy_versions: Dict[str, str]       # {"liquidity": "1.0.0", "risk": "2.1.0"}
```

---

## 2. PROPOSAL LIFECYCLE STATE MACHINE

```
┌─────────┐
│  DRAFT  │
└────┬────┘
     │ (All parameters validated)
     ▼
┌──────────────────┐       (Trigger not yet active)       ┌────────────────────────┐
│ READY_FOR_REVIEW ├─────────────────────────────────────►│  WAITING_FOR_TRIGGER   │
└────┬─────────────┘                                      └───────────┬────────────┘
     │                                                                │
     │ (Presented to Trader)                                          │ (Trigger activated)
     ▼                                                                ▼
┌──────────────────────┐       (Trader confirms)          ┌────────────────────────┐
│ WAITING_FOR_APPROVAL ├─────────────────────────────────►│        APPROVED        │
└────┬──────────┬──────┘                                  └───────────┬────────────┘
     │          │                                                     │
     │ (Reject) │ (Timeout / Invalidated / Stale)                     │ (Pre-Trade Gate)
     ▼          ▼                                                     ▼
┌──────────┐ ┌────────────────────────┐                   ┌────────────────────────┐
│ REJECTED │ │ EXPIRED / INVALIDATED  │                   │      ORDER INTENT      │
└──────────┘ └────────────────────────┘                   └────────────────────────┘
```

---

## 3. TRADER APPROVAL CONTRACT & INTERACTION

Trader authorization is an **explicit human event**. The resulting `TraderApproval` record is immutable.

```python
@dataclass(frozen=True)
class TraderApproval:
    approval_id: str                      # Format: APPR-{proposal_id}-{seq}
    proposal_id: str                      # Lineage to TradeProposal
    decision_id: str                      # Lineage to MarketDecisionSummary
    approved_at: str                      # ISO-8601 UTC timestamp
    approved_by: str                      # "TRADER_MANUAL" (or session token hash)
    
    # Authorized Execution Parameters (Trader may adjust within risk policy)
    authorized_quantity: int              # Must be <= recommended_quantity
    authorized_order_type: str            # "LIMIT" | "MARKET"
    authorized_limit_price: Optional[float]
    authorized_stop_loss: float
    authorized_targets: List[float]
    
    # Expiry & Freshness Invariants
    approval_valid_until: str             # Max 30 seconds from approval_at
    canonical_sequence_at_approval: int
    spot_price_at_approval: float
    option_price_at_approval: float
    action_type: str                      # "APPROVE_AS_PROPOSED" | "EDITED_AND_APPROVED"
    modifications_log: Dict[str, Any]     # Recorded changes if edited
```

---

## 4. APPROVAL EXPIRY & SLIPPAGE INVARIANTS

An approval becomes `EXPIRED` or requires `REVALIDATION_REQUIRED` if any of the following occur before broker submission:
1. **Time Elapsed:** $>30.0$ seconds have passed since `approved_at`.
2. **Spot Slippage:** Spot index moves $>15.0$ points away from `spot_price_at_approval`.
3. **Option Premium Slippage:** Option quote moves $>3.0\%$ or $>50$ bps beyond `authorized_limit_price`.
4. **Data Feed Staleness:** Spot or target contract quote exceeds $>15.0$s age.
5. **Structural Invalidation:** Spot crosses `invalidation_level`.
