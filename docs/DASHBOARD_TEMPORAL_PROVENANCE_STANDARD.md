# AIR ArdhaMind — Dashboard Temporal Provenance Standard

**Environment**: STAGING ONLY (`/opt/ardhamind/staging`)  
**Standard Version**: 2.0.0  
**Status**: ACTIVE & AUTHORITATIVE  

---

## 1. Principles of Temporal Provenance

Every material market-derived component in AIR Ardha must satisfy the **Four Core Temporal Questions**:
1. **WHAT SESSION / DATE DOES THIS REPRESENT?** (Target trading date / dataset session date).
2. **WHEN WAS THE SOURCE OBSERVED?** (Original provider observation timestamp).
3. **WHEN DID ARDHA LAST VALIDATE THIS DATA?** (Server commit / canonical adapter validation timestamp).
4. **WHAT IS THE TEMPORAL STATUS?** (`LIVE`, `PRE-MARKET`, `POST-MARKET`, `LAST VALID SESSION`, `NEXT SESSION PREVIEW`, `WEEKEND`, `HOLIDAY`, `STALE`, `DEGRADED`).

---

## 2. Global Status Semantics & Color Hierarchy

- **`LIVE`**: Active NSE market trading session (09:15–15:30 IST). Accent: Emerald (`#00C896`).
- **`PRE-MARKET`**: Active NSE pre-open window (09:00–09:15 IST). Accent: Sky Blue (`#38BDF8`).
- **`POST-MARKET`**: Active NSE post-close consolidation (15:30–16:00 IST). Accent: Violet (`#8B5CF6`).
- **`WEEKEND`**: Non-trading Saturday or Sunday. Accent: Sky Blue (`#38BDF8`).
- **`HOLIDAY`**: Scheduled NSE exchange holiday. Accent: Amber (`#E59700`).
- **`LAST VALID SESSION`**: Off-market view showing historical close data. Accent: Neutral Slate (`#707987`).
- **`STALE`**: Telemetry feed paused for $> 10\text{s}$. Accent: Amber (`#E59700`).
- **`DEGRADED`**: Telemetry gap or provider failure. Accent: Rose (`#E5484D`).

---

## 3. Staging Preview Control Rules
- QA staging preview controls (`PRE`, `LIVE`, `POST`) affect presentation mode only.
- Preview controls MUST NOT rewrite canonical timestamps or present historical/weekend data as live today data.
- When preview control is active during closed hours, `TemporalContextStrip` displays an explicit preview banner:
  `STAGING PREVIEW · NEXT SESSION PREVIEW (24 Aug 2026)` or `STAGING PREVIEW · LAST SESSION REVIEW (21 Aug 2026)`.

---

## 4. Date & Timestamp Formatting Rules
- Canonical Date Format: `22 Aug 2026`
- Canonical Time Format: `15:30 IST` or `15:30:08 IST`
- Full Timestamp Format: `21 Aug 2026 · 15:30:08 IST`
- Millisecond precision ($15:30:08.382 \text{ IST}$) is reserved exclusively for live tick and internal latency diagnostics under `Settings → Advanced`.
