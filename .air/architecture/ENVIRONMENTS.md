# ArdhaMind Environments Reference

This document records verified operational boundaries for **STAGING** and **PRODUCTION**.

---

## 1. Environment Specifications

### STAGING
- **Path**: `/opt/ardhamind/staging`
- **Http Port**: `3001`
- **Domain / Nginx Upstream**: `staging.ardhamind.projectair.in` -> `http://127.0.0.1:3001`
- **Vite Mode**: `VITE_STAGING_MODE=true`
- **Process**: `NODE_ENV=development PORT=3001 VITE_STAGING_MODE=true npm run start`
- **Permissions**: Authorized tasks may inspect, test, and edit staging code within scope.

### PRODUCTION
- **Path**: `/opt/ArdhaMind`
- **Http Port**: `3000`
- **Service**: `ardhamind.service`
- **Status**: Must remain 100% untouched (`git -C /opt/ArdhaMind status --porcelain` clean) unless explicitly authorized by an approved task with `production_write_allowed: true`.
- **Default State**: **READ-ONLY**.

---

## 2. Environment Isolation Invariants

1. **No Shared Writable Caches**: Staging processes write strictly to `/opt/ardhamind/staging/data` and `/opt/ardhamind/staging/.cache`.
2. **Independent Daemon Instances**: Staging daemon runs on Port 3001; Production daemon runs on Port 3000.
3. **Strict Git Isolation**: Working in staging (`/opt/ardhamind/staging`) must never alter the working directory or git state of production (`/opt/ArdhaMind`).
