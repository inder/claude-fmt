Database | Setup | Best for
SQLite | none | a single process on one machine
PostgreSQL | a server | complex queries and growth
MySQL | a server | simple read-heavy sites

PostgreSQL gives you strict typing, rich indexes and extensions such as PostGIS, which matters once the data model grows. MySQL is familiar to most hosting providers and performs well on simple read-heavy workloads. SQLite needs no server at all and is fastest for a single process on one machine.
