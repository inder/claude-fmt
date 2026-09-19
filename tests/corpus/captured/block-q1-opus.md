HTTPS is HTTP sent over TLS. The diagram shows the TLS 1.3 handshake, which needs one round trip and runs over TCP before any HTTP data is sent.

```
┌──────────────────────────┐                              ┌──────────────────────────┐
│         BROWSER          │                              │          SERVER          │
│         (client)         │                              │    (example.com:443)     │
└────────────┬─────────────┘                              └────────────┬─────────────┘
             │                                                         │
             │  0. TCP handshake (SYN / SYN-ACK / ACK)                 │
             │◄───────────────────────────────────────────────────────►│
             │                                                         │
 ┌───────────┴──────────────────────┐                                  │
 │ 1. ClientHello                   │                                  │
 │  • TLS versions & cipher suites  │                                  │
 │  • client random                 │                                  │
 │  • ECDHE key share (client pub)  │                                  │
 │  • SNI = "example.com", ALPN=h2  │                                  │
 └───────────┬──────────────────────┘                                  │
             │────────────────────────────────────────────────────────►│
             │                                                         │
             │                               ┌─────────────────────────┴────────────┐
             │                               │ 2. ServerHello (in the clear)        │
             │                               │  • chosen cipher, e.g. AES-128-GCM   │
             │                               │  • server random                     │
             │                               │  • ECDHE key share (server pub)      │
             │                               ├──────────────────────────────────────┤
             │                               │  ░ both sides now compute the ░      │
             │                               │  ░ shared secret → HKDF keys  ░      │
             │                               ├──────────────────────────────────────┤
             │                               │ 3. Encrypted with handshake keys:    │
             │                               │  • Certificate (chain up to a CA)    │
             │                               │  • CertificateVerify (signed with    │
             │                               │    server's private key)             │
             │                               │  • Finished (MAC of the transcript)  │
             │                               └─────────────────────────┬────────────┘
             │◄────────────────────────────────────────────────────────│
             │                                                         │
 ┌───────────┴──────────────────────────────┐                          │
 │ 4. Browser verifies                      │                          │
 │  • chain links to a trusted root CA      │                          │
 │  • hostname matches cert SAN             │                          │
 │  • not expired / revoked, CT logged      │                          │
 │  • CertificateVerify signature valid     │                          │
 │    → server holds the private key        │                          │
 │  • Finished MAC → nothing was tampered   │                          │
 └───────────┬──────────────────────────────┘                          │
             │                                                         │
             │  5. Client Finished                                     │
             │────────────────────────────────────────────────────────►│
             │                                                         │
 ┌───────────┴─────────────────────────────────────────────────────────┴───────────┐
 │ 6. SECURE CHANNEL: HTTP requests & responses sent with symmetric AEAD            │
 │    (AES-GCM or ChaCha20-Poly1305)                                                │
 │    • Confidentiality: eavesdroppers see only ciphertext                          │
 │    • Integrity: any modified byte fails the auth tag                             │
 │    • Authentication: the certificate proves the server's identity                │
 │    • Forward secrecy: ephemeral ECDHE keys mean a later key leak can't           │
 │      decrypt past sessions                                                       │
 └──────────────────────────────────────────────────────────────────────────────────┘
```
The key idea: asymmetric crypto (ECDHE plus certificate signatures) agrees on keys and proves who the server is, then faster symmetric encryption protects the data. Resumed sessions can skip steps using PSK or 0-RTT.
