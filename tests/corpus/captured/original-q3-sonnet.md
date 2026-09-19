A typical web application has these main components:

## Components

1. **Client (frontend)**: The browser UI, built with HTML/CSS/JavaScript, often using a framework like React, Vue, or Svelte. It renders pages, handles user input, and makes requests.

2. **DNS**: Translates a domain name (example.com) into the IP address of the server or CDN.

3. **CDN / edge**: Caches and serves static assets (JS, CSS, images) from locations near the user. It can also terminate TLS and absorb traffic spikes.

4. **Load balancer / reverse proxy**: (Nginx, HAProxy, cloud LBs) Distributes incoming requests across multiple app servers, and often handles TLS, compression, and rate limiting.

5. **Application server (backend)**: Runs business logic (Node, Django, Rails, Spring, Go, etc.). It authenticates users, validates input, and coordinates data access and other services.

6. **Database**: Persistent storage, either relational (PostgreSQL, MySQL) or NoSQL (MongoDB, DynamoDB). The app server is usually its only client.

7. **Cache**: (Redis, Memcached) In-memory storage for hot data, sessions, and computed results, to reduce database load and latency.

8. **Background workers and queues**: (SQS, RabbitMQ, Kafka, Celery, Sidekiq) Handle slow or deferred work such as sending email, processing uploads, and generating reports.

9. **Object storage**: (S3, GCS) Holds large files like images, videos, and user uploads.

10. **External services**: Third-party APIs for payments, email, auth providers, analytics, and so on.

## How they talk to each other

- **Browser to server: HTTP(S).** The browser sends requests (GET, POST, etc.) and gets responses (HTML, JSON, assets). Common API styles are REST, GraphQL, and gRPC-web. For real-time features, WebSockets or Server-Sent Events keep a connection open.
- **Request path:** Browser → DNS lookup → CDN (static assets served here) → load balancer → app server.
- **App server to database:** Over a database protocol (e.g. the PostgreSQL wire protocol), usually through a driver or ORM and a connection pool.
- **App server to cache:** Over a fast key-value protocol (e.g. Redis). The app checks the cache first and falls back to the database on a miss (the "cache-aside" pattern).
- **App server to workers:** Asynchronously through a message queue. The app enqueues a job and returns immediately, and workers pick it up later.
- **App server to external services:** Outbound HTTPS API calls, with inbound **webhooks** when the third party needs to notify you of an event.
- **Service to service (in microservices):** Synchronous HTTP/gRPC calls, or asynchronous events over a message broker.
- **State and identity:** HTTP is stateless, so the client sends a session cookie or token (e.g. JWT) on each request. The server uses it to identify the user, often looking up session data in the cache.

## Example flow: loading a user's dashboard

1. Browser resolves the domain and fetches the JS bundle from the CDN.
2. The JS calls `GET /api/dashboard` with an auth token.
3. The load balancer routes it to an app server.
4. The app server validates the token, checks Redis for cached data, and on a miss queries the database, then caches the result.
5. It returns JSON, and the frontend renders it.
6. If the user then uploads a file, the app stores it in object storage and enqueues a job for a worker to process it.

Smaller apps often collapse this down to just a browser, one server, and one database. The other pieces get added as scale and complexity demand.
