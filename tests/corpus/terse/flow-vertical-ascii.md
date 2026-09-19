```
  Resolve DNS
       |
       v
  TCP handshake
       |
       v
  TLS handshake
       |
       v
  Encrypted HTTP
```

Each step depends on the one before it; the TLS handshake is where the certificate is checked and session keys are agreed.
