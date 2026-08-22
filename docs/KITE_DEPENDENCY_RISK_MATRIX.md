# KITE DEPENDENCY RISK MATRIX & SINGLE POINTS OF FAILURE

**Document Version:** 1.0.0 — Authoritative Dependency Risk Matrix  
**Target Architecture:** AIR Ardha External Provider Integrations

---

## 1. DEPENDENCY RISK CLASSIFICATION

| System Capability | Primary Provider | Secondary Backup | Dependency Risk Tier | Impact of Complete Provider Outage | Staging Mitigation Strategy |
|:---|:---|:---|:---:|:---|:---|
| **NIFTY Spot Streaming** | Zerodha Kite Ticker | None (Single Source) | **CRITICAL_SINGLE_POINT** | Live index charts, momentum detectors, and spot tracking freeze | Silent stall detector triggers auto-reconnect; safely shifts to `DEGRADED` |
| **Option Chain Depth** | Zerodha Kite Ticker | None (Single Source) | **HIGH** | Strike LTPs, IV, and Greeks freeze | Pre-close candidate preservation locks last valid snapshot |
| **NIFTY 5m Candles** | Zerodha Kite Historical | Rolling Local Cache | **MEDIUM** | Real-time backfill delayed | In-memory bar builder synthesizes candles from live ticks |
| **Market Breadth** | Zerodha Kite Quote | Local Index Weighted Proxy | **MEDIUM** | Constituent advance/decline frozen | Degrades breadth weight in intelligence; maintains spot trading |
| **India VIX** | Zerodha Kite Ticker | None (Single Source) | **MEDIUM** | Volatility regime shifts to neutral | Intelligence engine assumes conservative volatility range |
| **FII / DII Flows** | NSE India EOD Scraper | Secondary StockEdge Feed | **LOW** | Delayed institutional figures | Carries forward T-1 institutional posture until published |
| **News & Catalysts** | Multi-Source RSS | Web Scraping Engine | **LOW** | Macro news sentiment paused | Operates purely on price action and structural levels |

---

## 2. SINGLE POINT OF FAILURE MITIGATION RECOMMENDATIONS

1. **Secondary NSE Snapshot Fallback:** An independent HTTPS poller to `nseindia.com/api/equity-stockIndices?index=NIFTY%2050` can serve as an out-of-band sanity check during broker outages.
2. **Deterministic Pre-Close Options Freeze:** Staging already implements [`OptionsCloseBaseline`](file:///opt/ardhamind/staging/src/storage/schemas.py#L98) candidate preservation so off-hours empty responses never overwrite closing derivatives structure.
