**Default pick: PostgreSQL.** SQLite is the exception for single-server, low-write apps.

| | PostgreSQL | MySQL | SQLite |
|---|---|---|---|
| Setup | Separate server | Separate server | None (a file) |
| Concurrency | Excellent (MVCC) | Good | One writer at a time (WAL helps) |
| Features | Richest: JSONB, full-text, extensions, strict typing | Solid, simpler | Basic, loose typing (use STRICT tables) |
| Ops cost | Managed options everywhere | Same | Near zero; backups = copy the file |
| Scaling | Vertical plus read replicas | Same | Single machine |
| Best for | Most apps that may grow | Legacy/LAMP stacks, familiar teams | Prototypes, small or read-heavy apps, embedded |

**Choose:**
- **SQLite** if one server, modest write load, and you want simplicity. Litestream can handle replication.
- **PostgreSQL** if you expect growth, multiple app servers, or need advanced queries.
- **MySQL** if your host or team already standardizes on it.

Migrating from SQLite to Postgres later is manageable if you use an ORM and avoid engine-specific SQL.
