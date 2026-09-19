For most small web apps, **start with SQLite if you'll run on one server, or PostgreSQL if you won't.** MySQL is a good choice, but at this size it rarely beats either one.

## At a glance

| | **SQLite** | **PostgreSQL** | **MySQL / MariaDB** |
|---|---|---|---|
| **Architecture** | A library inside your app; the database is one file | A separate server process | A separate server process |
| **Setup and ops** | Nothing to set up | Moderate: users, config, backups | Moderate, similar to Postgres |
| **Concurrent writes** | One writer at a time; WAL mode lets reads run alongside writes | Excellent (MVCC, row-level locks) | Very good (InnoDB) |
| **Multiple app servers** | ❌ Not practical, since the file sits on one machine | ✅ | ✅ |
| **Features** | Core SQL, JSON functions, FTS5 full-text search, window functions | The richest: JSONB, arrays, CTEs, full-text search, PostGIS, pgvector, extensions | Solid but fewer: JSON, CTEs (8.0+), full-text search |
| **Type strictness** | Loose by default (`STRICT` tables are optional) | Strict | Mostly strict now; older configs are loose |
| **Backups** | Copy the file, or use Litestream or `.backup` | `pg_dump`, PITR | `mysqldump`, binlogs |
| **Managed hosting** | Turso, Cloudflare D1, LiteFS | Everywhere: RDS, Supabase, Neon, Render, Fly, Railway | Everywhere: RDS, PlanetScale, most shared hosts |
| **Cost for a small app** | Free, no extra service | $0–15/mo (free tiers are common) | $0–15/mo |

## When each one fits

**SQLite** fits when:
- The app runs as one process or on one VM (a VPS, a single Fly machine, and so on).
- Most traffic is reads, with modest writes. It can handle thousands of writes per second if each transaction is short.
- You want the fewest moving parts and the lowest latency, because queries are function calls rather than network trips.
- Use `PRAGMA journal_mode=WAL`, `busy_timeout`, and `synchronous=NORMAL`, and back up with Litestream.

**PostgreSQL** fits when:
- You'll scale horizontally, deploy on serverless or ephemeral containers, or run several app instances.
- You want room to grow into features like JSONB, full-text search, geospatial queries (PostGIS), vector search (pgvector), and strict constraints.
- You want the framework and ORM default: Django, Rails, Prisma and Drizzle all treat it as a first-class target.
- It's the safest long-term default.

**MySQL / MariaDB** fits when:
- You're on shared hosting or a PHP stack (WordPress, Laravel), where it's already provided.
- Your team already knows how to run it.
- You specifically want PlanetScale/Vitess-style scaling later.
- Otherwise it has no clear advantage over Postgres for a new small app.

## Pitfalls to know about

- **SQLite:** write-heavy concurrent workloads will hit "database is locked" errors. `ALTER TABLE` is limited, so some migrations mean rebuilding the table. Don't put the file on network storage such as NFS or EFS.
- **PostgreSQL:** each connection costs memory, so on serverless platforms you'll need a pooler such as PgBouncer or your provider's built-in one. Major-version upgrades take some care.
- **MySQL:** watch the charset (use `utf8mb4`, not `utf8`) and the collation defaults. Older versions and some settings silently truncate or coerce data.

## How to decide

1. **Will more than one app server write to the database?** If yes, use **PostgreSQL**.
2. **Are you on a PHP or shared-hosting stack?** If yes, use **MySQL**.
3. **Otherwise:** use **SQLite** for simplicity, or **PostgreSQL** if you expect to grow.

If you're unsure, write standard SQL through an ORM. Moving from SQLite to Postgres later is then fairly easy, though you should test in dev against the database you'll run in production, because type handling differs.
