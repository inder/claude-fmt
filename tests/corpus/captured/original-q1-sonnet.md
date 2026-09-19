HTTPS is HTTP running over TLS (Transport Layer Security). Here is how the connection is set up, using TLS 1.3, the current version.

## 1. TCP connection
The browser opens a normal TCP connection to the server, usually on port 443.

## 2. TLS handshake

**ClientHello (browser → server)**
- Supported TLS versions and cipher suites.
- A random value.
- The server name being requested (SNI).
- A key share, which is the browser's half of a Diffie-Hellman key exchange, usually X25519.

**ServerHello (server → browser)**
- The chosen cipher suite.
- The server's own random value and key share.

At this point both sides can compute the same shared secret without ever sending it. Everything after this point is encrypted.

**Server authentication**
- The server sends its **certificate chain**: its own certificate, plus intermediate CA certificates.
- It also sends a **CertificateVerify** signature, made with the certificate's private key over the handshake transcript. This proves the server holds the private key.
- It ends with a **Finished** message, a MAC over the whole handshake.

**Browser verifies the certificate**
- The chain leads to a root CA that the OS or browser already trusts.
- The signatures in the chain are valid.
- The certificate has not expired or been revoked (via OCSP or CRLs).
- The certificate's domain (Subject Alternative Name) matches the site being visited.

**Client Finished**
- The browser sends its own Finished message, and the handshake is complete.

## 3. Encrypted data transfer
Both sides derive symmetric session keys from the shared secret using a key derivation function (HKDF). HTTP requests and responses are then encrypted and authenticated with an AEAD cipher such as AES-GCM or ChaCha20-Poly1305. This provides confidentiality, and it also detects any tampering.

## What this gives you
- **Confidentiality:** eavesdroppers see only ciphertext.
- **Integrity:** modified data is detected.
- **Authentication:** the certificate and signature prove you are talking to the real domain owner.
- **Forward secrecy:** the Diffie-Hellman keys are ephemeral, so a later theft of the server's private key can't decrypt past traffic.

## Key design point
Asymmetric cryptography (key exchange and signatures) is used only during the handshake to establish trust and agree on keys. The bulk data then uses fast symmetric encryption.

## Differences from TLS 1.2
- TLS 1.2 needs two round trips for the handshake, while TLS 1.3 needs one, and can resume with zero round trips.
- In TLS 1.2 the certificate is sent unencrypted.
- TLS 1.3 removed older, weaker options such as RSA key exchange, so forward secrecy is mandatory.
