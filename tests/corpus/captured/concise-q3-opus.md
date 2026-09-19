```
Browser/Mobile ──HTTPS──> CDN / Load balancer ──> Web/API server ──> Database
                                                    │   │
                                                    │   ├──> Cache (Redis)
                                                    │   └──> Queue ──> Workers
                                                    └──> Third-party APIs
```

- **Client (frontend):** HTML/CSS/JS in the browser, or a mobile app. It renders the UI and calls the backend over **HTTP(S)**, usually with REST or GraphQL requests that carry JSON. **WebSockets** handle real-time updates.
- **CDN / load balancer:** A CDN serves static files. A load balancer handles TLS and spreads requests across the servers.
- **Backend (API server):** Runs business logic, authentication and validation. It's stateless, so you can add more servers to handle more traffic.
- **Database:** Stores the data that must last, such as Postgres or MongoDB. The backend talks to it through a driver or ORM using SQL or queries.
- **Cache:** Keeps frequently read data in memory to cut database load.
- **Queue + workers:** Handle slow work in the background, like sending emails or processing images.
- **External services:** Payments, auth providers and email, called over their HTTP APIs or through webhooks.
