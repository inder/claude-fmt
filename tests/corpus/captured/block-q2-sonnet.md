```
                     ┌──────────────────────────┐
                     │  Small web app: which DB? │
                     └────────────┬─────────────┘
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│ SQLite            │  │ MySQL             │  │ PostgreSQL        │
├───────────────────┤  ├───────────────────┤  ├───────────────────┤
│ Embedded, 1 file  │  │ Client/server     │  │ Client/server     │
│ Zero setup/ops    │  │ Easy, widely      │  │ Most featureful   │
│ Very fast reads   │  │ hosted            │  │ Strict SQL,       │
│ Single writer     │  │ Good read-heavy   │  │ strong integrity  │
│ (WAL helps)       │  │ perf              │  │ JSONB, arrays,    │
│ Limited types &   │  │ Weaker on complex │  │ full-text, CTEs,  │
│ ALTER TABLE       │  │ queries/DDL       │  │ extensions        │
│ Scales to 1 host  │  │ Replication       │  │ (PostGIS,pgvector)│
│                   │  │ mature            │  │ Slightly more     │
│                   │  │                   │  │ tuning/ops        │
└─────────┬─────────┘  └─────────┬─────────┘  └─────────┬─────────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│ Pick when:        │  │ Pick when:        │  │ Pick when:        │
│ • Single server   │  │ • Shared hosting/ │  │ • Default choice  │
│ • Low write       │  │   LAMP/WordPress  │  │   for a new app   │
│   concurrency     │  │ • Team knows it   │  │ • Complex queries,│
│ • Prototype, tool,│  │ • Simple CRUD,    │  │   reporting, JSON │
│   internal app    │  │   read-heavy      │  │ • Expect growth   │
│ • Want easy       │  │                   │  │ • Managed options │
│   backups (copy)  │  │                   │  │   (Neon, Supabase,│
│                   │  │                   │  │   RDS)            │
└───────────────────┘  └───────────────────┘  └───────────────────┘

Rule of thumb:  SQLite ──(need multi-server / heavy writes)──► PostgreSQL
                MySQL  ──(only if hosting/team constraints)──► stay
```

My recommendation: start with SQLite if you're running on one server and want minimal ops, or pick PostgreSQL if you expect to grow or need richer queries. Choose MySQL only when your host or team already uses it. Migrating from SQLite to PostgreSQL later is straightforward if you use an ORM and avoid SQLite-specific quirks.
