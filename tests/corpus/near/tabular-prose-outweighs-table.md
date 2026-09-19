| Database | Pick |
| --- | --- |
| PostgreSQL | yes |
| SQLite | maybe |

PostgreSQL gives you strict typing, rich indexes and extensions such as PostGIS, which matters once the data model grows. MySQL is familiar to most hosting providers and performs well on simple read-heavy workloads. SQLite needs no server at all and is fastest for a single process on one machine.

For a team of eight, the deciding factors are how often changes cross service boundaries, whether you want one CI pipeline or several, and how much tooling you are willing to maintain. A monorepo makes atomic cross-cutting changes easy; separate repositories keep ownership and permissions simple.
