# news_provider state vocabulary and health

This document documents the provider execution architecture, circuit breaker policies, fetch scheduling control, and health metrics defined in Phase 5.2.

## 1. Provider State Vocabulary

Each news ingestor tracks its status against standard vocabulary schemas:

- **`ready`**: Normal state; the provider is enabled, operational, and has successfully fetched items during the last scheduled run.
- **`degraded`**: The provider experienced an error (e.g. timeout) but has not crossed the maximum consecutive failures threshold (3).
- **`unavailable`**: The provider has failed consecutively three or more times. The circuit breaker is open.
- **`blocked`**: Explicitly blocked or disabled via system preferences.
- **`stale`**: Last successful update occurred more than 10-30 minutes ago.

## 2. Ingestion Fetch Controls

- **Exponential Backoff**: If a fetch fails, the retry interval is doubled (`2.0 ** consecutive_failures * 10s`) up to a maximum limit of 3600 seconds, with random jitter added to prevent thundering herds.
- **Circuit Breaker**: When failures occur, the provider's circuit is opened, preventing any new network requests from being sent until the backoff timeout expires.
- **ETag & Last-Modified Checks**: Providers parse `ETag` and `Last-Modified` headers from response messages. Subsequent fetches append `If-None-Match` and `If-Modified-Since` requests. If the server responds with a `304 Not Modified`, content download is aborted to save bandwidth.
- **Refresh Scheduling**: Fetch queries are paced according to their refresh intervals (default 5 minutes). The background daemon checks if `should_fetch()` evaluates to true before performing any HTTP actions.
