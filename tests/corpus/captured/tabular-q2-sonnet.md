| Criterion | PostgreSQL | MySQL | SQLite |
| --- | --- | --- | --- |
| Architecture | Client-server | Client-server | Embedded, in-process library, single file |
| Setup effort | Moderate (server, roles, config) | Moderate | None, no server to run |
| Concurrency | Excellent (MVCC, many concurrent writers) | Good (InnoDB row locking) | Many readers, one writer at a time (WAL mode helps) |
| SQL features | Richest: CTEs, window functions, JSONB, arrays, full-text search, extensions (PostGIS, pgvector) | Solid; improved with 8.x (CTEs, window functions), JSON support is weaker | Good core SQL and JSON; fewer types, looser typing by default |
| Data integrity | Strict, strong constraints and transactional DDL | Good with InnoDB; some historically lenient modes | Foreign keys need to be enabled; flexible typing |
| Performance | Strong on complex queries and mixed workloads | Strong on simple read-heavy queries | Very fast for local reads, with no network hop |
| Scaling | Vertical plus read replicas; many managed options | Vertical plus read replicas; mature replication | Single machine only (tools like Litestream and LiteFS add replication) |
| Ops and cost | Managed offerings everywhere (RDS, Supabase, Neon) | Managed offerings everywhere | Near zero: backup is copying a file |
| Ecosystem | Very strong, popular default for new apps | Huge, especially for PHP and WordPress stacks | Ubiquitous, used by many frameworks for dev and tests |

| Your situation | Recommendation |
| --- | --- |
| Small app, one server, low to moderate traffic, simplicity is the priority | SQLite (WAL mode) |
| Expect growth, multiple app servers, or complex queries and JSON | PostgreSQL |
| Existing MySQL skills or a PHP/WordPress stack | MySQL |
| Unsure | PostgreSQL, since it has the most room to grow and the fewest surprises later |
