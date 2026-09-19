```
graph TD
  A[Resolve DNS] --> B[TCP handshake]
  B --> C[TLS handshake]
  C --> D[Encrypted requests]
```

The browser first resolves the domain name, then opens a TCP connection to the server. During the TLS handshake the server presents its certificate, the browser checks it against trusted authorities, and both sides agree on session keys that encrypt everything that follows.
