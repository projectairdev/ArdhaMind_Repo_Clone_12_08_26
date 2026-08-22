# PHASE 3 — EXECUTION POLICY REGISTRY SPECIFICATION

**Document Version:** 1.0.0 — Authoritative Policy Registry Specification  
**Component:** `ExecutionPolicyRegistry` (`src/execution_engine/policy_registry.py`)  
**Scope:** Versioned, Centralized, Testable Policy Contracts Replacing Architectural Constants  
**Target Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Status:** DESIGN COMPLETE (Staging Only — Production Untouched)

---

## 1. VERSIONED POLICY CONTRACTS INVENTORY

```python
@dataclass(frozen=True)
class ApprovalValidityPolicy:
    policy_version: str = "1.0.0"
    max_duration_seconds: float = 30.0
    max_spot_deviation_pts: float = 15.0
    max_option_deviation_pct: float = 3.0
    max_option_deviation_bps: float = 50.0
    require_fresh_quotes: bool = True
    invalidate_on_structural_breach: bool = True

@dataclass(frozen=True)
class SlippagePolicy:
    policy_version: str = "1.0.0"
    max_acceptable_slippage_bps: float = 50.0
    max_premium_drift_inr: float = 3.0
    revalidation_threshold_bps: float = 40.0

@dataclass(frozen=True)
class MarginSafetyPolicy:
    policy_version: str = "1.0.0"
    buffer_multiplier: float = 1.15       # Requires 115% of exchange margin
    min_free_cash_buffer_inr: float = 2000.0
    disallow_unsettled_collateral: bool = True

@dataclass(frozen=True)
class OrderPriceSanityPolicy:
    policy_version: str = "1.0.0"
    max_bid_ask_collar_pct: float = 2.0   # Limit price inside [Bid-2%, Ask+2%]
    min_tick_size: float = 0.05
    enforce_exchange_circuit_collar: bool = True

@dataclass(frozen=True)
class DailyRiskPolicy:
    policy_version: str = "1.0.0"
    max_trades_per_day: int = 4
    max_daily_loss_inr: float = 5000.0
    max_open_positions: int = 1
    max_simultaneous_exposure_inr: float = 25000.0
    is_live_enabled: bool = False         # Safety default: disabled until explicitly configured

@dataclass(frozen=True)
class ProtectiveOrderPolicy:
    policy_version: str = "1.0.0"
    preferred_mechanism: str = "BROKER_SL_M"  # "BROKER_SL_M" | "BROKER_GTT" | "NONE"
    block_if_unsupported: bool = True     # Block execution if broker SL cannot be set

@dataclass(frozen=True)
class PositionTimeExitPolicy:
    policy_version: str = "1.0.0"
    mandatory_exit_cutoff_time: str = "15:15:00"  # IST
    liquidity_warning_time: str = "15:00:00"      # IST
    force_square_off_on_close: bool = True
```
