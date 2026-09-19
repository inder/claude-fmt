```
flowchart of the handshake
DNS lookup → TCP connect → TLS handshake → encrypted HTTP
```

The handshake verifies the certificate and agrees on session keys before any request is sent, so everything after it is encrypted. The browser also checks that the certificate names the site it asked for.
