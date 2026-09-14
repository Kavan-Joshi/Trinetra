# Trinetra — Cybersecurity Architecture

## 1. Identity & Access

- **Authentication:** OAuth2 password flow → JWT (HS256), 12 h expiry, signed with a secret injected via environment (`TRINETRA_JWT_SECRET`). Production: RS256 with JWKS rotation and refresh tokens; optional SSO integration with state identity systems.
- **Authorization (RBAC):**

| Capability | admin | analyst | operator |
|---|---|---|---|
| View dashboard/map/alerts/events | ✓ | ✓ | ✓ |
| Ack / resolve alerts | ✓ | ✓ | ✓ |
| Watchlist create/import/deactivate | ✓ | ✓ | ✗ |
| Camera registry create/update | ✓ | ✗ | ✗ |
| View audit log | ✓ | ✗ | ✗ |

  Roles enforced **server-side** on every route (`require_role` dependency); the UI only mirrors what the API permits.

- **Seeded accounts are demo credentials** — production forces first-login password change + MFA (roadmap: TOTP).

## 2. Audit & Non-repudiation

- Every mutation writes an append-only `audit_log` row: actor, action, entity, JSON details, server timestamp. Login, watchlist changes, imports, alert dispositions, registry edits, seeds are all captured.
- Alert lifecycle (`new → ack → resolved`) records the acting user; watchlist deactivation is soft (retains history) rather than deletion.

## 3. Transport & Network

- **TLS everywhere:** nginx terminates client TLS (UI + API + WebSocket); service-to-service traffic rides isolated Docker overlay networks — in the pilot compose file, only the API (8000) and UI (8080) are host-published. Postgres, Redis, NATS have **no host ports**.
- **Site gateways initiate outbound-only connections** (no inbound firewall pinholes to police sites). NATS auth (user/pass/JWT) and TLS can be enabled at the bus for cross-WAN links.
- Production network zones: Site LAN → DMZ gateway → state DC. No camera ever talks directly to the internet.

## 4. Data Protection

- **At rest:** Postgres volume encryption (LUKS/cloud KMS in production); evidence object storage with SSE; nightly encrypted backups (pg_dump + evidence sync) with 35-day retention.
- **In transit:** TLS 1.2+ on every hop; VPN/leased-line for site-to-DC links.
- **PII policy:** watchlist entries carry purpose and FIR reference; person photos/face embeddings (phase 2) stored in a separate encrypted store with access-level gates; plates kept in normalized (search) + raw (display) forms.
- **Retention roadmap:** raw video 30 days (site NVR), evidence frames 90 days, event metadata 5 years, audit log 7 years — configurable per DPDP Act 2023 / state retention rules; automated expiry via object-store lifecycle + DB cron. **Per-department retention** (7/15/30 days) is modelled per department and enforced by the `janitor` service (dry-run by default).

### 4.1 Government records & biometric data

- **Chain of custody:** every government-records lookup (VAHAN/SARTHI/CCTNS/NAFIS) is audited (actor, system, plate/person queried, FIR ref). Records-sourced watchlist entries carry `source_system` + `source_ref` so the provenance of every alert is traceable to a FIR/record.
- **Biometric isolation:** NAFIS fingerprint/face match results are stored as metadata (match + score + FIR ref), not raw biometric templates. Production stores any templates in a separate encrypted store with access-level gates.
- **Least-privilege connectors:** each records connector holds only its own service credential; the correlator's enrichment call is best-effort and never blocks alert delivery.

### 4.2 Community cameras & viewing

- **Consent gate:** community cameras onboard only with explicit consent (`consent=true`); the onboarding is audited and the feed is tagged `source_type=community` with a restricted scope.
- **On-demand viewing:** live streams are pulled only on operator demand (no continuous central ingestion); viewing tokens are short-lived (TTL). Production adds a viewing-audit log (who watched which camera, when).

## 5. Application Security

- Input validation via Pydantic on every boundary (events from the bus, API payloads, CSV import with strict category whitelist).
- SQL injection: SQLAlchemy parameterized queries only — no string SQL.
- WebSocket endpoints authenticate by token query param and close with 4401 on failure; snapshot files served from a dedicated static mount, not the filesystem root.
- Rate limiting on login (roadmap: per-IP + per-user lockout).
- Dependency hygiene: pinned requirements, slim base images, non-root container users (production hardening item).

## 6. Secrets & Config

- All secrets via environment injection; `.env.example` ships dev defaults only. Production: Vault/KMS-backed injection, quarterly rotation of JWT signing keys, per-site NATS credentials.

## 7. Threat Model Highlights

| Threat | Mitigation |
|---|---|
| Stolen operator token | 12 h expiry, logout clears token, audit trail of actions |
| Rogue camera/feed injection | Registry is the only path to ingestion; events from unregistered cameras are dropped and logged by the correlator |
| Alert tampering | Alerts are append-only rows; status changes are themselves audited |
| Watchlist exfiltration by insider | RBAC + audit; analyst role cannot read audit trail or manage registry |
| Gateway compromise at site | Gateway holds no PII database — only a bus credential; blast radius = its own cameras' events |
| DoS on event bus | JetStream persistent queues + consumer limits; dedup window absorbs floods |
