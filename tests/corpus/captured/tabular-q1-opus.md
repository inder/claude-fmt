HTTPS is HTTP running over TLS. Here is how a modern TLS 1.3 connection is set up:

| Step | What happens | Why it matters |
| --- | --- | --- |
| 1. TCP (or QUIC) connection | The browser opens a connection to the server, usually on port 443. HTTP/3 uses QUIC over UDP instead of TCP. | Gives the handshake a channel to run over. |
| 2. ClientHello | The browser sends the TLS versions and cipher suites it supports, a random nonce, the site name (SNI), and ALPN (e.g. `h2`). It also sends its half of an ephemeral key exchange, usually X25519 and now often a hybrid with ML-KEM. | Starts negotiation. Sending the key share right away is what lets TLS 1.3 finish in 1 round trip. |
| 3. ServerHello | The server chooses the version and cipher suite and returns its own random nonce and ephemeral key share. | Both sides can now compute the same shared secret without ever sending it. |
| 4. Key derivation | Each side runs HKDF on the shared secret and the handshake transcript to get the handshake keys. | Everything after ServerHello is encrypted, including the certificate. |
| 5. Certificate | The server sends its certificate chain: leaf, intermediate(s), and a chain up to a root CA the browser trusts. | Proves the public key belongs to this domain. |
| 6. Certificate validation | The browser checks the signatures up to a trusted root, the validity dates, that the hostname matches the SAN, revocation (OCSP stapling or CRLs), and Certificate Transparency logs. | Stops someone else from pretending to be the server. |
| 7. CertificateVerify | The server signs the handshake transcript with its certificate's private key. | Proves the server actually holds that private key and that nobody altered the handshake. |
| 8. Finished messages | Both sides exchange a MAC over the whole transcript. | Confirms both computed the same keys and detects any downgrade or tampering. |
| 9. Application data | HTTP requests and responses are encrypted with an AEAD cipher: AES-GCM or ChaCha20-Poly1305. | Gives confidentiality and integrity for the rest of the session. |

| Security property | Mechanism |
| --- | --- |
| Confidentiality | Symmetric AEAD encryption using session keys |
| Integrity | AEAD authentication tags, plus Finished MACs over the handshake |
| Server authentication | CA-signed certificate, plus the CertificateVerify signature |
| Forward secrecy | Ephemeral (EC)DHE keys. A private key stolen later can't decrypt past sessions. |
| Downgrade protection | Transcript hashing, plus special sentinel values in ServerHello.random |
| Quantum resistance (emerging) | Hybrid key exchange such as X25519MLKEM768 |

| Optimization | Effect |
| --- | --- |
| 1-RTT handshake (TLS 1.3) | One round trip, versus two in TLS 1.2 |
| Session resumption (PSK tickets) | Skips certificate exchange on reconnect |
| 0-RTT early data | Sends data in the first flight. It can be replayed, so it should only be used for idempotent requests. |
| HSTS | Makes the browser always use HTTPS for the site, which blocks SSL-stripping |
