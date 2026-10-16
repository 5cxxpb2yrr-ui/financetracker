# Storage compatibility inventory

This document records the current database API assumptions before a durable-storage migration. It is not an implementation and does not authorize production data migration.

## Main application (`app.py`)

The Flask app uses Python's native `sqlite3` API throughout request handlers.

- Connection lifecycle: request-scoped connection stored on Flask `g`, closed in `teardown_appcontext`.
- Result behavior: `sqlite3.Row` supports both column-name and positional access.
- Query API: `execute(sql, params)`, `fetchone()`, `fetchall()`, and direct cursor iteration.
- Writes: explicit `commit()` calls after logical operations; some operations execute multiple related statements before committing.
- Generated IDs: handlers depend on `cursor.lastrowid` after inserts.
- Schema creation: `executescript()` and SQLite `INTEGER PRIMARY KEY AUTOINCREMENT`.
- SQL dialect: positional `?` parameters, SQLite `strftime('%Y-%m', date)`, `INSERT OR ...` patterns where used, and SQLite date/text conventions.
- Data tables include users, accounts, categories, transactions, budgets, category rules, email inboxes, and parsed email transactions.

## SaaS module (`saas.py`)

- Uses a separate connection stored on Flask `g` and a separate local `saas.db` file.
- Uses `sqlite3.Row`, `execute()`, `executescript()`, explicit commits, and `lastrowid`.
- Tables include tenants, tenant users, invoices, and tenant instances.
- SaaS mode therefore has an independent schema and must be included in any storage migration, not silently left on local disk.

## Transaction-sensitive flows to test

1. Registration: user creation and default-category creation.
2. Account creation and related initial data.
3. Transaction create/edit/delete and category reassignment.
4. CSV import and its handling of partial/invalid rows.
5. Email parsing, approval, and creation of the corresponding ledger transaction.
6. SaaS signup and tenant creation.
7. Rollback after a deliberate failure midway through a multi-write operation.
8. Concurrent duplicate registration/subdomain attempts.
9. Cross-user authorization checks on every record type.
10. Persistence after container restart and a new deployment.

## Storage architecture decision

Do **not** put an HTTP wrapper around each `execute()` call and claim it is transaction-safe. It would split a logical SQLite transaction across independent remote requests and could change rollback behavior, visibility of uncommitted writes, generated IDs, and constraint handling.

Cloudflare documents that Container disk is ephemeral by default. A Container can reach Worker bindings through outbound handlers, but that transport fact alone does not preserve the application's connection-level SQL semantics. Durable Object SQLite storage is accessible to the Worker/Durable Object runtime, not as a normal SQLite file directly mounted into the Python process.

### Options compared

| Option | Advantages | Main work / risk |
|---|---|---|
| Managed PostgreSQL with a supported Python driver over TLS | Preserves connection-level transactions and request-scoped connection pattern; avoids creating an operation API for every workflow | Requires selecting a provider, storing credentials securely, converting SQLite-specific SQL/schema and validating all behavior; database network access must be tested from the actual Container runtime |
| Cloudflare D1 behind a private Worker operation API | Keeps durable storage inside Cloudflare; D1 supports SQLite-style SQL and transactional batches | Requires moving each logical multi-statement operation into a Worker endpoint/batch, securing Container-to-Worker access, and explicitly preserving generated-ID/result semantics. A generic SQL proxy is not acceptable |
| Local SQLite inside the Container | Minimal code changes | **Rejected for production:** container disk is ephemeral and cannot be the durable source of truth |

### Provisional recommendation

For the smallest semantic change to the existing Flask app, evaluate **managed PostgreSQL with a supported Python driver and TLS first**. This is a recommendation to validate, not a provider selection or authorization to create a paid service. The connection test must prove TLS, secret handling, transactions/rollback, and restart persistence in a Cloudflare preview before migrating application data.

Keep the already-provisioned `financetracker-prod` D1 database empty unless the architecture is deliberately changed to the D1 operation-API approach. Do not build a one-query-per-HTTP-call D1 adapter.

## Release gates

- Do not route production traffic or import real records until the architecture is approved, transaction and isolation tests pass, and backup/restore is proven.
- Use synthetic data in preview.
- Test both the main app and SaaS persistence; neither may silently fall back to local SQLite in production.
- Keep credentials in platform secrets, never in source control or image layers.

## References

- [Cloudflare Containers lifecycle and ephemeral disk](https://developers.cloudflare.com/containers/concepts/architecture/)
- [Cloudflare Containers outbound traffic](https://developers.cloudflare.com/containers/configuration/outbound-traffic/)
- [Cloudflare Containers access to Worker bindings](https://developers.cloudflare.com/containers/configuration/workers-connections/)
- [Cloudflare D1 transactional batch behavior](https://developers.cloudflare.com/d1/worker-api/d1-database/)
- [Cloudflare database connection options](https://developers.cloudflare.com/workers/databases/connecting-to-databases/)
