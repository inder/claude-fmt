A typical web app has three tiers: client, server and data. Most requests travel down that stack and back up.

```
                ┌──────────────────────────────────────┐
                │  CLIENT (browser / mobile app)       │
                │  HTML/CSS/JS, React/Vue, etc.        │
                │  Renders the UI, handles user input  │
                └──────────────────┬───────────────────┘
                                   │ HTTPS requests (REST/GraphQL, JSON)
                                   │ WebSockets / SSE for real-time updates
          ┌────────────────────────┼─────────────────────────┐
          ▼                        ▼                         │
┌───────────────────┐   ┌──────────────────────────┐         │
│ CDN               │   │ LOAD BALANCER / GATEWAY  │         │
│ Static files:     │   │ TLS termination, routing │         │
│ JS, CSS, images   │   │ rate limits, auth checks │         │
└───────────────────┘   └────────────┬─────────────┘         │
                                     │ HTTP (internal)       │
                                     ▼                       │
                ┌──────────────────────────────────────┐     │
                │  APPLICATION SERVER(S)               │     │
                │  Node / Django / Rails / Spring ...  │     │
                │  Routing, business logic, sessions,  │     │
                │  validation, authN/authZ             │     │
                └──┬──────────┬──────────┬──────────┬──┘     │
       SQL/driver  │   get/set│  publish │   HTTPS  │        │
                   ▼          ▼          ▼          ▼        │
          ┌──────────┐ ┌─────────┐ ┌──────────┐ ┌──────────────────┐
          │ DATABASE │ │ CACHE   │ │ QUEUE    │ │ EXTERNAL APIs    │
          │ Postgres,│ │ Redis,  │ │ SQS,     │ │ payments, email, │
          │ MySQL,   │ │ Memcache│ │ RabbitMQ,│ │ OAuth/identity   │
          │ Mongo    │ │ hot data│ │ Kafka    │ └──────────────────┘
          └──────────┘ └─────────┘ └────┬─────┘
                ▲                       │ consume jobs
                │                       ▼
                │            ┌──────────────────────┐
                └────────────┤ BACKGROUND WORKERS   │
                 read/write  │ emails, reports,     │
                             │ image processing     │
                             └──────────┬───────────┘
                                        │ store files
                                        ▼
                             ┌──────────────────────┐
                             │ OBJECT STORAGE       │
                             │ S3/GCS: uploads,     │
                             │ media, backups       │◄── the CDN can serve
                             └──────────────────────┘    these files too

 Typical request: Client ─► LB ─► App ─► Cache (hit? return) ─► DB ─► App ─► JSON ─► Client
 Slow work:       App ─► Queue ─► Worker (runs async; client gets a quick 202/ack)
 Cross-cutting:   logging, metrics, tracing, secrets, CI/CD across all tiers
```

Small apps often start with just the client, one app server and a database. The cache, queue, workers and CDN get added as traffic grows.
