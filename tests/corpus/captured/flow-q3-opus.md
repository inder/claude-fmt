A typical web request, from the user's click to the response and back:

```
 ┌──────────────────────────────┐
 │ 1. CLIENT (browser / mobile) │  HTML/CSS/JS UI; runs frontend code (React, etc.)
 └──────────────┬───────────────┘
                │ user clicks → needs data or a page
                ↓
 ┌──────────────────────────────┐
 │ 2. DNS                       │  "app.example.com" → IP address
 └──────────────┬───────────────┘
                ↓  HTTPS (TLS-encrypted HTTP)
 ┌──────────────────────────────┐
 │ 3. CDN / edge                │  serves static assets (JS, images) from cache
 └──────────────┬───────────────┘  close to the user
                │ dynamic request (e.g. GET /api/orders)
                ↓
 ┌──────────────────────────────┐
 │ 4. LOAD BALANCER / GATEWAY   │  spreads traffic across servers, terminates TLS,
 └──────────────┬───────────────┘  rate limiting, routing
                ↓  HTTP (REST / GraphQL / gRPC)
 ┌──────────────────────────────┐
 │ 5. APPLICATION SERVER (API)  │  business logic: validate input, check auth
 └──┬───────────┬───────────┬───┘  (session cookie or JWT via auth service)
    │           │           │
    ↓           ↓           ↓
 ┌───────┐  ┌────────┐  ┌──────────────┐
 │ CACHE │  │   DB   │  │ MESSAGE QUEUE│
 │ Redis │  │Postgres│  │ Kafka / SQS  │
 └───┬───┘  └───┬────┘  └──────┬───────┘
     │ hit? →   │ SQL query     │ async job (email, image resize, reports)
     │ return   │ over TCP      ↓
     │ fast     │         ┌──────────────┐
     │ miss? ───┘         │ 6. WORKERS   │  process jobs in the background,
     │                    └──────┬───────┘  write results to DB / storage
     │                           ↓
     │                    ┌──────────────┐
     │                    │ OBJECT STORE │  S3 etc.: files, uploads, backups
     │                    └──────────────┘
     ↓
 ┌──────────────────────────────┐
 │ 7. RESPONSE                  │  server builds JSON (or HTML) → back through
 └──────────────┬───────────────┘  LB → client (HTTP status + body)
                ↓
 ┌──────────────────────────────┐
 │ 8. CLIENT RENDERS            │  updates the UI; may keep a WebSocket/SSE open
 └──────────────────────────────┘  for real-time server → client pushes

 Cross-cutting, alongside every step:
   logging/metrics/tracing → observability stack (Grafana, Datadog)
   third-party APIs (payments, email) ← called from app server or workers over HTTPS
```

The pattern to remember: clients talk to servers over HTTP(S). Servers talk to data stores over those stores' own protocols (SQL over TCP, the Redis protocol), and to each other either synchronously (HTTP/gRPC) or asynchronously (queues).
