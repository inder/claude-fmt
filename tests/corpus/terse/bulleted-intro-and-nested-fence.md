Here is how I would choose:

- Start with SQLite if everything runs on one machine.
  - It needs no server; create the file with:
    ```bash
    sqlite3 app.db ".tables"
    sqlite3 app.db ".schema"
    ```
- Move to PostgreSQL once you add a second app server.
  - It handles concurrent writes and strict typing well.
- Pick MySQL only if your host already expects it.
