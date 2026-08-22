# AIR Ardha Staging — Portfolio & Execution Data-Field Inventory

**Surface:** `Portfolio Workspace` (`PortfolioWorkspace.tsx`, `ActiveOpportunityHero.tsx`, `LivePositionDrawer.tsx`, `TradeLineageModal.tsx`, `OrderPreviewModal.tsx`)  
**Environment:** Staging (`staging.ardhamind.projectair.in`)  
**Audit Date:** August 2026  
**Scope:** Complete visible data fields across Header Banner, Execution Safety Gates, Active Trade Opportunity Hero, Live Broker Positions Table, Active Broker Order Book, Execution Journal (M5), and Modals.

---

## 1. HEADER BANNER & TOP METRIC STRIP (`PortfolioWorkspace.tsx`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Workspace Phase Badge | PHASE 3 ACTIVE | Badge | System Context | Static Phase Tag | Static | "PHASE 3 ACTIVE" |
| Authoritative Broker Status | BROKER STATE | Enum/Badge | Broker Health Gateway | `brokerHealth.normalized_status` | 5s polling / WS | "CONNECTED_AUTHENTICATED" / "AUTH_REQUIRED" |
| Sync Broker Action Trigger | Sync Broker | Button/Spinner | Broker Gateway | `handleReconcile()` | User click | Spinner on reconcile |
| Kill Switch Toggle Button | Kill Switch / Resume | Button/Toggle | Safety State Machine | `safetyStatus.kill_switch_active` | User click | "Kill Switch" / "Resume Entries" |
| Live Open Positions Count | Live Open Positions | String/Count | Broker Gateway | `positions.length` | 5s / WS push | "0 Active" / "X Active" |
| Total Unrealized P&L | Total Unrealized P&L | Currency (INR) | Portfolio State | `totalUnrealizedPnl` | 1s tick / WS | "₹+0.00" |
| Daily Realized Loss Gate | Daily Realized Loss Gate | Currency Ratio | Safety State Machine | `safetyStatus.daily_realized_loss / daily_loss_limit` | On trade close | "₹0.00 / ₹25000" |
| Execution State Gate | Execution State | Enum/Badge | Safety & Broker State | Derived execution state | Real-time | "PRE-FLIGHT GUARDED" / "AUTH_REQUIRED" |
| Action Feedback Banner | Success Alert | String | REST Response | `actionFeedback` | On action | Green alert bar |
| Action Error Banner | Error Alert | String | REST Response | `actionError` | On error | Red alert bar |

---

## 2. ACTIVE OPPORTUNITY HERO (`ActiveOpportunityHero.tsx`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Proposal Direction | DIRECTION | Enum/Badge | Opportunity Engine | `proposal.direction` | Real-time / 8s poll | "BULLISH" / "BEARISH" / "STANDBY" |
| Contract Symbol | CONTRACT | String | Opportunity Engine | `proposal.contract_symbol` | Real-time / 8s poll | "NIFTY 24900 CE" |
| Setup Type | SETUP TYPE | String | Opportunity Engine | `proposal.setup_type` | Real-time / 8s poll | "MOMENTUM_BREAKOUT" |
| Lots Selector Buttons | Lots: 1, 2, 3, 5, 10 | Interactive Toggle | Frontend State | `selectedLots` | User click | 1 Lot default |
| Proposal State Badge | PROPOSAL STATE | Enum/Badge | Opportunity Engine | `proposal.state` | Real-time / 8s poll | "PROPOSED" / "DRY_RUN_RECORDED" |
| Conviction Score | Conviction | Percentage | Opportunity Engine | `proposal.confidence_score` | Real-time / 8s poll | "78%" |
| Entry Reference Price | Entry Reference | Number/INR | Opportunity Engine | `proposal.entry_price` | Real-time / 8s poll | "₹145.00" |
| Stop-Loss Price | Stop-Loss | Number/INR | Opportunity Engine | `proposal.stop_loss` | Real-time / 8s poll | "₹115.00" |
| Target 1 / Target 2 Prices | Target 1 / Target 2 | Numbers/INR | Opportunity Engine | `proposal.target_1`, `proposal.target_2` | Real-time / 8s poll | "₹190.0 / ₹235.0" |
| Risk : Reward Ratio | Risk : Reward | Ratio String | Opportunity Engine | `proposal.risk_reward_ratio` | Real-time / 8s poll | "1 : 2.5" |
| Total Exposure Quantity | Exposure | Units / Lots | Mathematical Model | `selectedLots * lot_size` | Real-time | "50 Qty (25/lot)" |
| Max Capital Risk (INR) | Max Capital Risk | Currency (INR) | Risk Model | `calculatedMaxLoss` | Real-time | "₹1,500.00" |
| Deterministic Rationale Points | RATIONALE (1, 2, 3) | Array<String> | Opportunity Engine | `proposal.rationale[]` | Real-time / 8s poll | 3 structured bullets |
| Invalidation Condition Trigger | Invalidation Trigger | String | Opportunity Engine | `proposal.invalidation_condition` | Real-time / 8s poll | "Break below 24,800" |
| Proposal Audit Metadata: ID | Proposal ID | String | Opportunity Engine | `proposal.proposal_id` | Real-time | "PROP-20260822-001" |
| Proposal Generated Timestamp | Generated At | Timestamp | Opportunity Engine | `proposal.timestamp` | Real-time | ISO timestamp |
| Priority / Quality Scores | Priority / Quality | Integers | Scoring Engine | `proposal.priority_score`, `quality_score` | Real-time | "75 / 82" |
| Exchange / Contract String | Exchange/Symbol | String | Order Gateway | `proposal.contract_symbol` | Real-time | "NFO:NIFTY26AUG24900CE" |
| Order Intent Execution Gateway | Execution Gateway | String | Order Gateway | Static Gateway Label | Static | "AUTHORITATIVE KITE CONNECT ROUTER" |

---

## 3. LIVE BROKER POSITIONS TABLE (`PortfolioWorkspace.tsx`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Total Open Positions Header | LIVE BROKER POSITIONS | Integer Count | Broker State | `positions.length` | 5s / WS push | "LIVE BROKER POSITIONS (0)" |
| Contract Symbol & Badges | Contract Symbol | String & Badges | Broker Positions Feed | `pos.contract_symbol` | 1s stream | "NIFTY26AUG24900CE" (`STOP` / `TARGET`) |
| Product Classification | Product | String | Broker Positions Feed | `pos.product` | 5s stream | "NRML" / "MIS" |
| Position Quantity | Quantity | Integer | Broker Positions Feed | `pos.quantity` | 5s stream | "50" |
| Average Buy Price | Buy Avg | Currency (INR) | Broker Positions Feed | `pos.buy_price` | 5s stream | "₹145.20" |
| Current Live LTP | Live LTP | Currency (INR) | Live Feed Stream | `pos.current_ltp` | 1s stream | "₹158.40" |
| Unrealized Position P&L | Unrealized P&L | Currency (INR) | Mathematical Model | `pos.unrealized_pnl` | 1s stream | "₹+660.00" |
| Stop Loss Level | Stop Loss | Currency (INR) | Trade State Machine | `pos.stop_loss` | 5s stream | "₹115.00" |
| Target Level | Target | Currency (INR) | Trade State Machine | `pos.target` | 5s stream | "₹190.00" |
| Actions: Lineage Trigger | Lineage | Button | Frontend State | `setSelectedProposalId(pos.order_id)` | User click | Opens Lineage Modal |
| Actions: Single Position Exit | Exit | Button | REST API Trigger | `setExitConfirmPos(pos)` | User click | Opens Exit Confirm Modal |
| Emergency Close All Trigger | Emergency Close All | Button | REST API Trigger | `setShowEmergencyModal(true)` | User click | Opens Close All Modal |

---

## 4. ACTIVE BROKER ORDER BOOK TABLE (`PortfolioWorkspace.tsx`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Active Orders Header Count | ACTIVE BROKER ORDER BOOK | Integer Count | Broker Order Feed | `orders.length` | 5s / WS push | "ACTIVE BROKER ORDER BOOK (0)" |
| Contract Symbol | Contract | String | Broker Order Feed | `ord.contract_symbol` | 5s / WS push | "NIFTY26AUG24900CE" |
| Transaction & Order Type | Type | String | Broker Order Feed | `ord.transaction_type`, `ord.order_type` | 5s / WS push | "BUY • LIMIT" |
| Order Product | Product | String | Broker Order Feed | `ord.product` | 5s / WS push | "NRML" |
| Filled / Total Quantity | Filled / Total | Ratio & Remainder | Broker Order Feed | `ord.filled_quantity / ord.quantity` | 5s / WS push | "50 / 50 (Rem: 0)" |
| Order Limit Price | Limit Price | Currency (INR) | Broker Order Feed | `ord.price` | 5s / WS push | "₹145.00" |
| Broker Assigned Order ID | Broker ID | String | Broker Order Feed | `ord.broker_order_id` | 5s / WS push | "24082200014285" / "PENDING" |
| Authoritative Order Status | Status | Enum/Badge | Broker Order Feed | `ord.status` | 5s / WS push | "OPEN" / "COMPLETE" / "CANCELLED" |
| Actions: Cancel Order | Cancel | Button | Order Gateway | `handleCancelOrder(ord.order_id)` | User click | Dispatches cancel REST request |

---

## 5. CLOSED TRADE EXECUTION JOURNAL & LINEAGE (M5) (`PortfolioWorkspace.tsx`)

| Field Name | Visual Label | Data Type | Data Source | Canonical State Path | Update Frequency | Fallback / Unavailable Behavior |
|:---|:---|:---|:---|:---|:---|:---|
| Summary: Total Completed Trades | Total Trades | Integer | Journal Analytics | `journalSummary.total_trades` | On trade close | "12" |
| Summary: Realized Win Rate % | Win Rate | Percentage | Journal Analytics | `journalSummary.win_rate_pct` | On trade close | "66.7%" |
| Summary: Total Realized P&L | Realized P&L | Currency (INR) | Journal Analytics | `journalSummary.total_realized_pnl` | On trade close | "₹+14,250.00" |
| Journal Record: Session Date | Date | Date String | Journal Store | `j.trading_session_date` | On trade close | "2026-08-22" |
| Journal Record: Contract Symbol | Contract | String | Journal Store | `j.contract_symbol` | On trade close | "NIFTY26AUG24900CE" |
| Journal Record: Setup Type | Setup | String | Journal Store | `j.setup_type` | On trade close | "MOMENTUM_BREAKOUT" |
| Journal Record: Weighted Entry Price | Avg Entry | Currency (INR) | Journal Store | `j.weighted_average_entry` | On trade close | "₹145.20" |
| Journal Record: Weighted Exit Price | Avg Exit | Currency (INR) | Journal Store | `j.weighted_average_exit` | On trade close | "₹178.50" / "--" |
| Journal Record: Entry Slippage | Slippage | Points & Color | Journal Store | `j.entry_slippage_pts` | On trade close | "+0.2 pts" |
| Journal Record: Realized Trade P&L | Realized P&L | Currency (INR) | Journal Store | `j.realized_trade_pnl` | On trade close | "₹+1,665.00" |
| Journal Record: Realized R-Multiple | R-Multiple | Multiplier | Journal Store | `j.realized_r_multiple` | On trade close | "2.10R" |
| Journal Record: Closing Reason | Reason | String | Journal Store | `j.closing_reason` | On trade close | "TARGET_1_REACHED" |
| Journal Record: Audit Lineage Trigger | Audit Lineage | Button | Frontend State | `setSelectedProposalId(j.proposal_id)` | User click | Opens Lineage Modal |
