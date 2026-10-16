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

The next implementation must select one of these approaches deliberately:

- **Preferred for compatibility:** a durable relational database with native connection-level transactions, accessed by the Python app through a supported driver and encrypted network connection. This requires selecting/provisioning the database provider, configuring credentials as secrets, and testing the provider's connectivity from the Cloudflare Container runtime.
- **Alternative:** redesign the persistence boundary so logical application operations execute atomically in a Worker/Durable Object service. This is a larger application change; it must define an operation-level API and preserve the existing app's behavior before switching callers.

The provisioned D1 database is currently empty. Do not route production traffic or import real records until the architecture is selected, the end-to-end transaction tests pass, and a backup/restore procedure is proven.

## References

- [Cloudflare Containers lifecycle and ephemeral disk](https://developers.cloudflare.com/containers/concepts/architecture/)
- [Cloudflare Containers access to Worker bindings](https://developers.cloudflare.com/containers/configuration/workers-connections/)
- [Cloudflare database connection options](https://developers.cloudflare.com/workers/databases/connecting-to-databases/)
