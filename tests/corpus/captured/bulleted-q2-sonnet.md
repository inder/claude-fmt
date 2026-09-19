# Quick take

- **Default pick for a small web app:** PostgreSQL if you'll deploy to a managed host and expect to grow. SQLite if it's a single-server app and you want the simplest ops. MySQL is a fine middle option but rarely the best pick for a new project.

# SQLite

- **Setup and ops**
  - Embedded: a single file, no server process, no network, no credentials.
  - Backups are a file copy (or `.backup` / Litestream for continuous replication).
  - Very low latency, because queries are in-process.
- **Strengths**
  - Zero admin and cheap to run, so it's great for prototypes, internal tools and low-to-moderate traffic sites.
  - With WAL mode it handles many concurrent readers well.
  - Easy to test with (in-memory or temp-file DBs).
- **Limitations**
  - One writer at a time, so heavy concurrent writes will queue.
  - Limited to one machine. Multi-server or serverless deployments need extras (Turso/libSQL, LiteFS).
  - Fewer types and features: looser typing by default, limited `ALTER TABLE`, no user/role permissions.
- **Best for**
  - Single-server apps, side projects, and read-heavy sites.

# PostgreSQL

- **Strengths**
  - The richest feature set: JSONB, arrays, full-text search, CTEs, window functions, partial and expression indexes, and strong constraints.
  - Extensions such as PostGIS and pgvector.
  - Strict, predictable behavior and excellent concurrency (MVCC).
  - Widely available as a managed service (Supabase, Neon, RDS, Fly, Render), often with a free tier.
- **Limitations**
  - Needs a server, and connection pooling matters once you scale.
  - A bit more tuning and operational overhead than SQLite.
- **Best for**
  - Apps you expect to grow, complex queries, or data integrity needs.

# MySQL (and MariaDB)

- **Strengths**
  - Mature, fast on simple read-heavy workloads, and very widely hosted (including cheap shared hosting).
  - Huge ecosystem, and a natural fit for PHP/WordPress stacks.
- **Limitations**
  - Historically looser defaults and quirks (silent coercions, though strict mode helps).
  - Fewer advanced features than Postgres, though it has improved (CTEs, window functions, JSON).
  - DDL and transactional behavior have some gotchas depending on the storage engine and version.
- **Best for**
  - Existing MySQL ecosystems, PHP/WordPress apps, and hosts that only offer MySQL.

# Side-by-side

| | SQLite | PostgreSQL | MySQL |
|---|---|---|---|
| Architecture | Embedded file | Client/server | Client/server |
| Ops effort | Minimal | Moderate | Moderate |
| Write concurrency | Single writer | Excellent | Good |
| Feature depth | Basic | Deepest | Good |
| JSON support | Good (JSON1) | Excellent (JSONB) | Good |
| Multi-server scaling | Hard | Easy | Easy |
| Cost to start | Free, no hosting | Free tiers available | Free tiers available |

# Recommendation

- **Choose SQLite** if the app runs on one server, traffic is modest, and you want minimal moving parts.
- **Choose PostgreSQL** if you want room to grow, richer queries, or you're not sure. It's the safest default.
- **Choose MySQL** if your host, framework or team already leans that way.
- **Migration note:** starting on SQLite and moving to Postgres later is manageable if you use an ORM and avoid engine-specific SQL.
