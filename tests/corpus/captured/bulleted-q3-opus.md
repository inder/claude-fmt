- **Client (frontend)**
  - Runs in the browser or a mobile app: HTML, CSS, JavaScript (often a framework like React, Vue, or Svelte)
  - Renders the UI, handles user input, and manages local state
  - Talks to the backend over **HTTP(S)**, usually through REST or GraphQL APIs that exchange JSON
  - Uses **WebSockets** or Server-Sent Events for real-time updates such as chat or live dashboards

- **DNS and CDN**
  - DNS turns the domain name into an IP address
  - The CDN (Cloudflare, CloudFront) caches static assets like JS bundles, images, and fonts at edge locations close to users
  - Often the first thing a request hits; it serves cached content directly and forwards everything else to the origin

- **Load balancer / reverse proxy**
  - Nginx, HAProxy, or a cloud load balancer (ALB, GCP LB)
  - Terminates TLS, spreads traffic across several server instances, and runs health checks
  - May also handle rate limiting, compression, and routing by path or host

- **Application server (backend)**
  - Holds the business logic, e.g. Node/Express, Django, Rails, Spring, Go, FastAPI
  - Handles authentication and authorization (sessions, cookies, JWTs, OAuth)
  - Validates input, coordinates calls to the database, cache, and other services, and returns responses
  - Should be **stateless** where possible so you can scale it horizontally behind the load balancer

- **Database**
  - Relational (PostgreSQL, MySQL) for structured, transactional data
  - NoSQL (MongoDB, DynamoDB) for flexible schemas or very high scale
  - The backend connects over a database wire protocol, usually through an ORM or query builder and a connection pool

- **Cache**
  - Redis or Memcached, an in-memory key-value store
  - Holds frequently read data, session data, and computed results to take load off the database
  - Common pattern is **cache-aside**: check the cache, fall back to the DB on a miss, then write the result into the cache

- **Message queue and background workers**
  - RabbitMQ, Kafka, SQS, or a Redis-backed queue like Sidekiq or Celery
  - The backend **publishes** a job (send email, resize image, generate report) and returns right away
  - Workers **consume** jobs asynchronously, which keeps request latency low and separates slow work from user-facing paths

- **Object storage**
  - S3, GCS, or Azure Blob for user uploads and large files
  - Clients often upload directly using **presigned URLs**, so file bytes never pass through the app server

- **Third-party services**
  - Payments (Stripe), email (SendGrid, SES), auth (Auth0, Clerk), search (Elasticsearch, Algolia)
  - The backend calls them over HTTPS APIs, and they call back through **webhooks**

- **Observability**
  - Logs, metrics, and traces (Datadog, Grafana/Prometheus, OpenTelemetry, Sentry)
  - Every component sends telemetry here so you can debug and alert across the whole system

# How a typical request flows

- User clicks a button, and the frontend sends `GET /api/orders/42` with an auth token
- DNS resolves the domain, and the CDN sees an uncacheable API route and forwards it
- The load balancer terminates TLS and picks a healthy app server
- The app server checks the token, then asks the cache for `order:42`
  - Hit: return it immediately
  - Miss: query the database, store the result in the cache, return it
- If the request triggers side effects (e.g. "resend receipt"), the server enqueues a job and a worker handles it later
- The server responds with JSON, and the frontend updates the UI

# Communication patterns summary

- **Synchronous request/response**: HTTP/REST, GraphQL, gRPC (common between internal services)
- **Asynchronous messaging**: queues and pub/sub for background work and event-driven systems
- **Persistent connections**: WebSockets or SSE for server-to-client push
- **Callbacks**: webhooks for external services notifying your app

# Scaling note

- Small apps often run the frontend, backend, and database on one server, or as a monolith on a PaaS like Heroku, Render, or Fly.io
- As traffic grows, the components get split apart and scaled independently, and the backend may break into **microservices** that talk over HTTP/gRPC or a message bus
