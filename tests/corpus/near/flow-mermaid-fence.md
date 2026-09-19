```mermaid
flowchart TD
  A[Resolve DNS] --> B[TCP handshake]
  B --> C[TLS handshake]
  C --> D[Encrypted requests]
```
