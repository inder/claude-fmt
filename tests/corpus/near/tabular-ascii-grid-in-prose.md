+------------+-----------------+
| Database   | Best for        |
+------------+-----------------+
| SQLite     | one machine     |
| PostgreSQL | growth          |
+------------+-----------------+

PostgreSQL gives you strict typing, rich indexes and extensions such as PostGIS, which matters once the data model grows. MySQL is familiar to most hosting providers and performs well on simple read-heavy workloads. SQLite needs no server at all and is fastest for a single process on one machine.
