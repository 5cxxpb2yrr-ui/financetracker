# Cloudflare deployment plan

Tracking issue: [#1 — Prepare FinanceTracker for secure Cloudflare production deployment](https://github.com/5cxxpb2yrr-ui/financetracker/issues/1)

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

1. Build a storage compatibility layer that preserves the app's required database semantics, including transaction boundaries, row results, and generated IDs.
2. Migrate both the main app and SaaS database access deliberately; do not leave a hidden SQLite file as a fallback in production.
3. Add tests for registration, account creation, transaction writes, CSV import, email-transaction approval, rollback behavior, restart persistence, and cross-user isolation.
4. Add a Cloudflare Workers + Containers entry point and bind only the required services. Confirm current account support/limits because Containers are a beta product.
5. Deploy to an isolated preview with synthetic test data. Verify login, core flows, persistence after container stop/restart, and logs.
6. Only after checks pass, prepare a reviewed production cutover and rollback plan.

## Current status

- [x] Create deployment tracking issue.
- [x] Provision an empty D1 database in the US jurisdiction.
- [x] Inspect the current app and container setup.
- [ ] Implement transaction-safe persistent storage.
- [ ] Add and pass production-readiness tests.
- [ ] Configure and validate an isolated Cloudflare preview.
- [ ] Review and authorize production cutover.
