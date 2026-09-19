The TLS 1.3 handshake that HTTPS runs on top of TCP. It takes one round trip before encrypted HTTP starts.

```
 BROWSER                                                     SERVER
 ───────                                                     ──────
┌──────────────────────────────┐
│ 1. DNS lookup + TCP connect  │  (or QUIC/UDP for HTTP/3)
│    to port 443               │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ 2. ClientHello               │ ─────────────────────────────→
│  • TLS versions supported    │
│  • cipher suites (AES-GCM,   │
│    ChaCha20-Poly1305)        │
│  • client random             │
│  • ephemeral ECDHE key share │
│    (e.g. X25519 / hybrid PQ) │
│  • SNI = hostname wanted     │
└──────────────────────────────┘
                                         ┌──────────────────────────────┐
                                         │ 3. ServerHello               │
               ←──────────────────────── │  • chosen cipher + version   │
                                         │  • server random             │
                                         │  • server ECDHE key share    │
                                         └──────────────┬───────────────┘
                                                        ↓
┌───────────────────────────────────────────────────────────────────────┐
│ 4. BOTH SIDES independently compute the shared secret:                │
│    ECDHE(my private key, peer's public share)                         │
│      → HKDF key schedule → handshake keys                             │
│    The secret itself never goes over the wire. Ephemeral keys give    │
│    forward secrecy: a stolen server key can't decrypt past traffic.   │
└───────────────────────────────────────────────────────────────────────┘
                                                        ↓
                                         ┌──────────────────────────────┐
                                         │ 5. Encrypted from here on:   │
               ←──────────────────────── │  • Certificate chain         │
                                         │  • CertificateVerify         │
                                         │    (signature over the whole │
                                         │    handshake transcript,     │
                                         │    made with the cert's      │
                                         │    private key)              │
                                         │  • Finished (MAC)            │
                                         └──────────────────────────────┘
               ↓
┌──────────────────────────────┐
│ 6. Browser verifies server   │
│  • chain leads to a trusted  │
│    root CA in the trust store│
│  • hostname matches the cert │
│  • cert not expired/revoked, │
│    has CT log proofs         │
│  • signature valid → server  │
│    holds the private key     │
└──────────────┬───────────────┘
               ↓
        ◇ all checks pass? ◇
        │                  │
       no                 yes
        ↓                  ↓
┌──────────────────┐  ┌──────────────────────────────┐
│ Abort: shows     │  │ 7. Client Finished (MAC)     │ ────→
│ "Your connection │  │    proves nobody tampered    │
│ is not private"  │  │    with the handshake        │
└──────────────────┘  └──────────────┬───────────────┘
                                     ↓
┌───────────────────────────────────────────────────────────────────────┐
│ 8. Switch to application traffic keys (one set per direction)         │
│    HTTP requests/responses go inside AEAD-encrypted TLS records:      │
│      confidentiality (encrypted) + integrity (auth tag) + ordering    │
│      (sequence numbers stop replayed or reordered records)            │
└───────────────────────────────────────────────────────────────────────┘
                                     ↓
┌───────────────────────────────────────────────────────────────────────┐
│ 9. Later visits: a session ticket or PSK allows resumption, and       │
│    0-RTT early data lets the browser send a request immediately.      │
│    0-RTT data can be replayed, so only idempotent requests use it.    │
└───────────────────────────────────────────────────────────────────────┘
```

In short, the key exchange (ECDHE) keeps the data secret, the certificate and CA chain prove which server you're talking to, and the Finished MACs over the transcript mean a middleman can't alter the handshake without being detected.
