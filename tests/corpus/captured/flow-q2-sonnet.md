```
Small web app: which database?
        │
        ↓
Single server, one app process, low write concurrency?
        │
   ┌────┴─────┐
  YES         NO / unsure
   │           │
   ↓           ↓
 SQLite     Need multiple app servers, heavy concurrent
 (WAL mode)  writes, or a managed DB?
   │           │
   │      ┌────┴─────┐
   │     YES         NO
   │      │           │
   │      ↓           ↓
   │   Need rich features (JSONB, full-text, arrays,
   │   extensions like PostGIS/pgvector, strict typing)?
   │      │
   │  ┌───┴────┐
   │ YES       NO
   │  │         │
   │  ↓         ↓
   │ PostgreSQL MySQL / MariaDB
   │  │         │
   ↓  ↓         ↓
Trade-offs:

SQLite     + zero setup, one file, no server, fastest for local reads
           + trivial backups (Litestream, file copy)
           - one writer at a time, no network access
           - weaker ALTER TABLE, loose typing by default

PostgreSQL + best features and standards compliance, strong integrity
           + extensions, JSONB, full-text search, row-level security
           + wide managed support (Neon, Supabase, RDS, Fly)
           - needs a server and a bit more ops/tuning

MySQL      + mature, fast for simple read-heavy workloads
           + ubiquitous hosting (shared hosts, PlanetScale, RDS)
           - fewer advanced features than Postgres
           - historically looser defaults (check strict SQL mode)
        │
        ↓
Recommendation: start with SQLite if you're on one box, otherwise
PostgreSQL. Choose MySQL mainly when your host or existing stack
(WordPress, PHP apps) already expects it.
```

Migration path is easiest SQLite → PostgreSQL if you use an ORM (Prisma, SQLAlchemy, Django, etc.) and avoid engine-specific SQL early.
