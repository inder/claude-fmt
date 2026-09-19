SQLite: no server, one file, fastest for a single process on one machine.
PostgreSQL: strict typing, rich indexes, extensions such as PostGIS, the safest default for growth.
MySQL: familiar to hosting providers, good for simple read-heavy workloads, fewer advanced features.
Recommendation: start with SQLite on one box and move to PostgreSQL when you need a second server.
