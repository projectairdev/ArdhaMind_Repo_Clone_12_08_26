# PHASE F — MONDAY OPERATIONAL COMMANDS

**Document Version:** 1.0.0 — Authoritative Copy-Paste Command Runbook  
**Execution Environment:** AIR Ardha Staging (`/opt/ardhamind/staging`)  
**Service Identifiers:** `ardhamind.service`, `nginx.service`  

---

## 1. 08:45 IST — STARTUP & PRE-FLIGHT CHECK
```bash
# 1. Check Git Baseline
cd /opt/ardhamind/staging
git status --short
git rev-parse HEAD
git describe --tags --always

# 2. Check Systemd & Process Health
sudo systemctl status ardhamind.service nginx.service
ss -tulpn | grep -E "3000|80|443"

# 3. Check Disk Space & Timezone
df -h /opt/ardhamind
date
timedatectl

# 4. Check Dual-Write Directories
ls -ld data/cache/ data/session_store/ data/session_store/cache/ data/session_store/telemetry/ data/session_store/connectivity/ data/session_store/close/ data/session_store/options_close/ data/session_store/integrity/
```

---

## 2. 09:15 IST — FIRST LIVE TICK CAPTURE
```bash
# 1. View live canonical state generated sequence and timestamp
curl -s http://127.0.0.1:3000/api/canonical/state | jq '{seq: .state_seq, gen: .generated_at, spot: .market_data.current_spot, phase: .market_session.status, broker: .broker_status.status}'

# 2. Check lightweight recovery snapshot write
ls -l data/session_store/cache/latest_canonical_state.json
cat data/session_store/cache/latest_canonical_state.json | jq '{sequence: .state_seq, spot: .market_data.current_spot, bias: .unified_intelligence.market_bias, decision: .unified_intelligence.decision_summary.status}'
```

---

## 3. MID-SESSION HEALTH & SHADOW CHECK
```bash
# 1. Check rolling candles
ls -l data/session_store/cache/nifty_5m_candles.json
cat data/session_store/cache/nifty_5m_candles.json | jq '.candles | length'

# 2. Check telemetry series
ls -l data/session_store/telemetry/$(date +%F).json
cat data/session_store/telemetry/$(date +%F).json | jq '.telemetry_points | length'

# 3. Check connectivity event log
tail -n 10 data/session_store/connectivity/$(date +%F).jsonl
```

---

## 4. 15:20 IST — PRE-CLOSE OPTIONS CAPTURE CHECK
```bash
# Check latest valid options snapshot captured
cat data/session_store/cache/latest_canonical_state.json | jq '.option_intelligence | {status: .status, pcr: .pcr, max_pain: .max_pain, call_wall: .call_wall, put_wall: .put_wall, observed_at: .observed_at}'
```

---

## 5. 15:35+ IST — POST-CLOSE FINALIZATION & RECONCILIATION
```bash
# 1. Verify SessionCloseCore
cat data/session_store/close/$(date +%F).json | jq .

# 2. Verify OptionsCloseBaseline
cat data/session_store/options_close/$(date +%F).json | jq .

# 3. Verify SessionIntegrityEnvelope
cat data/session_store/integrity/$(date +%F).json | jq .

# 4. Storage size comparison
du -sh data/cache/session_history_$(date +%F).json data/session_store/
```
