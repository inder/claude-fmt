Most web apps follow a client → server → data layout, with supporting infrastructure in between.

| Component | What it does | Typical tech |
| --- | --- | --- |
| Client (browser / mobile app) | Renders the UI, handles user input, and calls the backend | HTML/CSS/JS, React, Vue, Svelte, iOS/Android |
| DNS | Turns the domain name into an IP address | Route 53, Cloudflare DNS |
| CDN | Serves static assets (JS, CSS, images) from edge servers close to the user | Cloudflare, CloudFront, Fastly |
| Load balancer / reverse proxy | Handles TLS and spreads requests across app servers | Nginx, HAProxy, AWS ALB, Envoy |
| API gateway (optional) | Routing, auth checks, rate limiting, request aggregation | Kong, AWS API Gateway |
| Application server (backend) | Business logic, validation, authorization, and orchestrating calls to other components | Node/Express, Django, Rails, Spring, Go, FastAPI |
| Auth service | Identity, login, tokens and sessions | OAuth2/OIDC, Auth0, Cognito, Keycloak |
| Database | Durable storage of core data (the source of truth) | PostgreSQL, MySQL, MongoDB, DynamoDB |
| Cache | Fast in-memory reads and session storage; takes load off the DB | Redis, Memcached |
| Message queue / event bus | Async work and decoupling between services | RabbitMQ, Kafka, SQS |
| Background workers | Run queued jobs: emails, image processing, reports | Celery, Sidekiq, BullMQ |
| Object storage | Files and uploads (blobs) | S3, GCS, Azure Blob |
| Search index (optional) | Full-text and faceted search | Elasticsearch, OpenSearch, Meilisearch |
| Third-party APIs | Payments, email, maps, etc. | Stripe, SendGrid, Twilio |
| Observability | Logs, metrics, traces, alerts | Prometheus, Grafana, Datadog, OpenTelemetry |

| Connection | Protocol / mechanism | Notes |
| --- | --- | --- |
| Client → DNS | DNS over UDP/TCP | Happens first, to find where to connect |
| Client → CDN | HTTPS GET | Cached static files; the page loads before any API calls |
| Client → Load balancer → App server | HTTPS: REST (JSON), GraphQL, or gRPC-web | Stateless requests; carry cookies or a bearer token (JWT) |
| Client ↔ App server (real-time) | WebSockets, Server-Sent Events, long polling | For chat, notifications and live updates |
| App server → Auth | OIDC/OAuth2 redirects; token validation | Tokens are often checked locally using the provider's public keys |
| App server → Database | Native wire protocol via driver/ORM, with connection pooling | SQL queries, wrapped in transactions for consistency |
| App server → Cache | Redis protocol over TCP | Cache-aside: check the cache, on a miss read the DB, then fill the cache |
| App server → Queue → Workers | Publish/subscribe or job enqueue | Lets the API respond fast while slow work runs later |
| Service ↔ Service (microservices) | REST, gRPC, or events | Service discovery and a service mesh are optional |
| App server / Client → Object storage | HTTPS; pre-signed URLs | Clients often upload straight to storage using a signed URL |
| App server → Third-party APIs | HTTPS REST plus webhooks back to you | Webhooks are how outside services call you back |
| All components → Observability | Log shipping, metrics scraping, trace propagation | A trace ID travels in headers across every hop |

| Step in a typical request ("load my dashboard") | What happens |
| --- | --- |
| 1 | The browser resolves the domain via DNS and fetches the app bundle from the CDN |
| 2 | JS calls `GET /api/dashboard` over HTTPS with the auth token |
| 3 | The load balancer terminates TLS and forwards to a healthy app server |
| 4 | The app server validates the token and checks permissions |
| 5 | It reads from the cache and falls back to the database on a miss |
| 6 | Any slow side effects (e.g. analytics) are put on a queue for workers |
| 7 | The server returns JSON, and the client renders it |
