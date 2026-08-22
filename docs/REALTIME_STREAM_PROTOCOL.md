# Realtime Stream Protocol Specification (STAGING ONLY)

**Environment**: STAGING ONLY (`/opt/ardhamind/staging`)  
**Specification**: Real-time event delta streaming protocol specification for WebSocket transport (`ws://localhost:3000/api/ws`).

---

## 1. Frame Header Specification

Every JSON frame emitted over the WebSocket stream contains the following envelope fields:

```json
{
  "type": "CHANNEL_NAME",
  "runtime_id": "STRING_UUID",
  "state_sequence": INTEGER,
  "observed_at": "ISO_TIMESTAMP_STRING",
  "transport_sent_at": "ISO_TIMESTAMP_STRING",
  "data": OBJECT
}
```

### Envelope Field Definitions
- **`type`**: Scoped channel type (`market.tick`, `options.tick`, `market.session`, `broker.status`, `live_event`).
- **`runtime_id`**: Unique session GUID of the active Python daemon (`WorkstationStateService._runtime_id`).
- **`state_sequence`**: Monotonically increasing sequence integer. Used by client to detect skipped or out-of-order frames.
- **`observed_at`**: Provider / exchange tick timestamp (T0 / T1).
- **`transport_sent_at`**: Outbound WebSocket serialization timestamp (T4).
- **`data`**: Payload object specific to the channel.

---

## 2. Channel Schemas

### Channel 1: `market.tick`
Emitted immediately on every valid NIFTY spot tick.
```json
{
  "type": "market.tick",
  "runtime_id": "a624d9b5-staging",
  "state_sequence": 8704,
  "observed_at": "2026-08-22T15:35:00.123Z",
  "transport_sent_at": "2026-08-22T15:35:00.128Z",
  "data": {
    "symbol": "NIFTY",
    "current_spot": 24450.75,
    "spot_change": 125.40,
    "spot_change_pct": 0.52,
    "last_tick_time": "2026-08-22T15:35:00.123Z"
  }
}
```

### Channel 2: `options.tick`
Emitted when an option contract LTP or OI tick update is received.
```json
{
  "type": "options.tick",
  "runtime_id": "a624d9b5-staging",
  "state_sequence": 8705,
  "observed_at": "2026-08-22T15:35:00.150Z",
  "transport_sent_at": "2026-08-22T15:35:00.155Z",
  "data": {
    "strike": 24450,
    "ce_ltp": 145.20,
    "pe_ltp": 112.80,
    "atm_iv": 13.8,
    "pcr": 1.12
  }
}
```

### Channel 3: `market.session`
Emitted immediately when market session state changes (e.g. `PRE_OPEN` &rarr; `OPEN` &rarr; `POST_CLOSE`).
```json
{
  "type": "market.session",
  "runtime_id": "a624d9b5-staging",
  "state_sequence": 8706,
  "observed_at": "2026-08-22T15:30:00.000Z",
  "transport_sent_at": "2026-08-22T15:30:00.005Z",
  "data": {
    "status": "CLOSED",
    "is_closed": true,
    "phase": "POST_MARKET"
  }
}
```
