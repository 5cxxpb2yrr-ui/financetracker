# Cloudflare deployment plan

Tracking issue: [#1 — Prepare FinanceTracker for secure Cloudflare production deployment](https://github.com/5cxxpb2yrr-ui/financetracker/issues/1)  
Storage work: [#3 — Design transaction-safe persistent storage for Flask and SaaS data](https://github.com/5cxxpb2yrr-ui/financetracker/issues/3)

## Current architecture findings

- The primary app is a Flask application in `app.py`, using the Python `sqlite3` API directly.
- SaaS mode uses a second, separate SQLite database through `saas.py`.
- The Docker image starts Gunicorn on port 8000. The current Pages build command (`docker compose up -d --build`) is not a valid Cloudflare Pages build.
- Docker Compose assumes a host Docker daemon, Traefik, and persistent named volumes. Those assumptions do not map directly to Cloudflare Workers/Pages.
- Cloudflare Containers have an ephemeral filesystem. A SQLite file stored inside the container cannot be the production source of truth.
- An empty Cloudflare D1 database named `financetracker-prod` has been provisioned in the US jurisdiction. It contains no imported user or financial data.

## Safety decisions

1. Do not switch production traffic or declare deployment complete until persistent storage and restart behavior are verified.
2. Do not use a per-query remote database shim that silently changes SQLite transaction boundaries.
3. Keep existing routes, templates, account logic, and import/report features intact while storage is migrated.
4. Keep the app's financial data separate by user and test access-control boundaries.
5. Require a strong configured `SECRET_KEY` in production; do not permit the development fallback.
6. Do not migrate any real financial records without explicit authorization and a verified backup/restore procedure.

## Implementation sequence

1. Inventory existing database assumptions and compare durable-storage options in [STORAGE_COMPATIBILITY.md](./STORAGE_COMPATIBILITY.md). The current provisional recommendation is to evaluate managed PostgreSQL with a supported Python driver/TLS first; this is not a provider selection or approval to create a paid service.
2. Select/provision the storage topology only after its connection, transaction, security, and cost requirements are understood.
3. Implement the selected storage layer and migrate both the main app and SaaS database access deliberately; do not leave a hidden SQLite file as a fallback in production.
4. Add tests for registration, account creation, transaction writes, CSV import, email-transaction approval, rollback behavior, restart persistence, and cross-user isolation.
5. Add a Cloudflare Workers + Containers entry point and bind only the required services. Confirm current account support/limits because Containers are a beta product.
6. Deploy to an isolated preview with synthetic test data. Verify login, core flows, persistence after container stop/restart, and logs.
7. Only after checks pass, prepare a reviewed production cutover and rollback plan.

## Current status

- [x] Create deployment tracking issue.
- [x] Provision an empty D1 database in the US jurisdiction.
- [x] Inspect the current app and container setup.
- [x] Inventory SQL/transaction assumptions and compare storage approaches in [STORAGE_COMPATIBILITY.md](./STORAGE_COMPATIBILITY.md).
- [ ] Approve/select the durable storage topology and validate connection/transaction behavior ([issue #3](https://github.com/5cxxpb2yrr-ui/financetracker/issues/3)).
- [ ] Implement transaction-safe persistent storage.
- [x] Add production secret-configuration tests and CI workflow (run [38891026944](https://github.com/5cxxpb2yrr-ui/financetracker/actions/runs/38891026944) passed).
- [ ] Add and pass storage and app regression tests.
- [ ] Configure and validate an isolated Cloudflare preview.
- [ ] Review and authorize production cutover.
