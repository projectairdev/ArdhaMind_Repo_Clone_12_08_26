# PHASE 3 — PRE-TRADE SAFETY GATE SPECIFICATION

**Document Version:** 1.0.0 — Authoritative Safety Gate Specification  
**Component:** `PreTradeSafetyGate` (`src/execution_engine/pre_trade_safety_gate.py`)  
**Scope:** 22-Point Pre-Submission Hard Barrier, Real-Time Invariant Evaluation, and Output Contract  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** DESIGN COMPLETE (Staging Only — Production Untouched)

---

## 1. PURPOSE & ARCHITECTURAL PLACEMENT

The `PreTradeSafetyGate` is the **single authoritative barrier** between trader authorization and broker order submission. It executes synchronously at the exact millisecond of submission.

```
[Trader Approval] ──► [PreTradeSafetyGate (22 Checks)] ──► [OrderIntent Dispatch]
                               │ (Any critical check fails)
                               ▼
                    [SUBMISSION ABORTED & AUDITED]
```

---

## 2. THE 22 PRE-TRADE SAFETY CHECKS INVENTORY

| Check ID | Safety Gate Name | Invariant Requirement | Failure Action | Existing Engine Lineage |
|:---|:---|:---|:---:|:---|
| **G-01** | Broker Authentication | Broker state == `CONNECTED_VERIFIED` & token unexpired | **BLOCK** | `StreamingOrchestrator` / `SessionManager` |
| **G-02** | Execution API Reachability | Kite order API ping / health check active | **BLOCK** | `AuthoritativeBrokerHealth` |
| **G-03** | WebSocket Stream Health | Stream state == `CONNECTED`, 0 silent stall flags | **BLOCK** | `StreamHealthMonitor` |
| **G-04** | Market Session Phase | Session phase in (`MARKET_OPEN`, `NORMAL_TRADING`) | **BLOCK** | `MarketStatusService` |
| **G-05** | Spot Quote Freshness | Spot price observed age $<15.0$ seconds | **BLOCK** | `DataQualityService` |
| **G-06** | Option Contract Freshness | Target contract quote observed age $<15.0$ seconds | **BLOCK** | `OptionChainBuilder` / `MarketFeed` |
| **G-07** | Symbol Subscription State | Target instrument token in active subscription list | **BLOCK** | `SubscriptionManager` |
| **G-08** | Breadth / VIX Feed Status | Breadth coverage $\ge 80\%$, VIX valid (not degraded) | **BLOCK** | `MarketContextBuilder` |
| **G-09** | Order Reconciliation Clear | Zero unresolved pending order/position states | **BLOCK** | `OrderLifecycleManager` |
| **G-10** | Decision Identity Valid | Lineage `decision_id` matches active state identity | **BLOCK** | `MarketDecisionSummaryComposer` |
| **G-11** | Proposal Freshness | Current time $\le$ `proposal_expiry_at` | **BLOCK** | `TradeProposalService` |
| **G-12** | Trader Approval Valid | Valid signature/record & time $\le$ `approval_valid_until` | **BLOCK** | `TraderApprovalService` |
| **G-13** | Risk Boundary Compliance | Trade risk within per-trade risk policy limit | **BLOCK** | `DeterministicRiskEngine` |
| **G-14** | Margin Sufficiency | Live available margin $\ge 1.15 \times$ required margin | **BLOCK** | `FundsService` |
| **G-15** | Lot Size Sizing | Quantity is exact non-zero multiple of NSE lot size | **BLOCK** | `InstrumentService` |
| **G-16** | Limit Price Sanity | Limit price $\in [\text{Bid} - 2.0\%, \text{Ask} + 2.0\%]$ | **BLOCK** | `OptionChainBuilder` |
| **G-17** | Bid-Ask Spread Policy | Contract spread bps $\le \text{policy.max\_spread\_bps}$ | **BLOCK** | `DecisionLiquidityPolicy` |
| **G-18** | Contract Expiry Window | Expiry date $\ge$ current date; not expired contract | **BLOCK** | `InstrumentService` |
| **G-19** | Duplicate Order Guard | No identical active/submitting intent in flight | **BLOCK** | `OrderIntentService` |
| **G-20** | Position Direction Conflict | No opposing open position without explicit reversal | **BLOCK** | `PositionsService` |
| **G-21** | Daily Loss / Trade Limit | Daily cumulative loss $<$ Max Daily Loss limit | **BLOCK** | `RiskEngineV2` |
| **G-22** | Global Kill-Switch | Global execution kill-switch == `EXECUTION_ENABLED` | **BLOCK** | `ExecutionManager` |

---

## 3. PRE-TRADE SAFETY RESULT CONTRACT

```python
@dataclass(frozen=True)
class PreTradeSafetyResult:
    result_id: str                        # Format: SAF-{timestamp_ms}-{seq}
    safe_to_submit: bool                  # True ONLY if all 22 gates pass
    checked_at: str                       # ISO-8601 UTC timestamp
    canonical_sequence: int
    proposal_id: str
    approval_id: str
    
    # Detailed Evaluation Breakdown
    passed_gates: List[str]               # e.g. ["G-01", "G-02", ..., "G-22"]
    failed_gates: List[Dict[str, str]]    # [{"gate_id": "G-14", "reason": "Insufficient margin"}]
    warnings: List[str]                   # Non-blocking advisory flags
    
    # State Snapshots at Instant of Check
    spot_price_snapshot: float
    option_bid_snapshot: float
    option_ask_snapshot: float
    spread_bps_snapshot: float
    available_margin_inr: float
    required_margin_inr: float
    policy_versions: Dict[str, str]
```
