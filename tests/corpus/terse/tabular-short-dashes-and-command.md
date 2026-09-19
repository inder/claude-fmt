| Database |Best for|
|:-|--:|
| SQLite | one machine, no server, one file on disk, trivial backups |
| PostgreSQL | growth, strict typing, rich indexes, extensions, concurrent writes |
| MySQL | simple read-heavy sites on shared hosting and PHP stacks |
| DuckDB | analytics on local files, not a web app's main store |

To try SQLite locally:

```bash
sqlite3 app.db "create table users (id integer primary key, email text not null unique, created_at text);"
sqlite3 app.db "insert into users (email, created_at) values ('a@example.com', datetime('now'));"
```
