# The core idea
- HTTPS is ordinary HTTP sent inside a TLS (Transport Layer Security) connection. Today that is usually TLS 1.3.
- TLS provides three guarantees:
  - **Confidentiality:** eavesdroppers can't read the traffic.
  - **Integrity:** any change to the traffic in transit is detected.
  - **Authentication:** the browser can confirm it's talking to the real `example.com`, not an impostor.

# Step 1: TCP (or QUIC) connection
- The browser opens a TCP connection to port 443.
- HTTP/3 uses QUIC over UDP instead, with TLS 1.3 built into it.

# Step 2: ClientHello (browser → server)
- The browser sends the TLS versions and cipher suites it supports, e.g. `TLS_AES_128_GCM_SHA256`.
- It sends a random nonce.
- It sends **SNI** (Server Name Indication), the hostname it wants. This lets one IP address host many certificates.
- It sends a **key share**: a temporary (ephemeral) Diffie-Hellman public key, usually X25519.
  - Newer browsers often also send a post-quantum hybrid share such as X25519MLKEM768.
- It sends **ALPN**, the application protocols it can use (`h2`, `http/1.1`).

# Step 3: ServerHello and server authentication (server → browser)
- The server picks a cipher suite and sends its own random nonce and ephemeral key share.
- Both sides now run **Diffie-Hellman** to compute the same shared secret.
  - The secret itself never crosses the network.
  - A passive eavesdropper can't work it out.
- Both sides feed that secret into a key derivation function (HKDF) to produce symmetric encryption keys.
  - Everything after this point is encrypted, including the certificate.
- The server sends its **certificate chain**: its leaf certificate plus intermediate CA certificates.
- The server sends **CertificateVerify**: a signature over the handshake transcript, made with the certificate's private key.
  - This proves the server actually holds that key.
  - It also ties the key exchange to the server's identity, which blocks man-in-the-middle attacks.
- The server sends **Finished**: a MAC over the whole handshake, which proves nothing was tampered with.

# Step 4: Browser verifies the certificate
- It follows the chain up to a root CA in its trusted store (from the OS or browser).
- It checks that the hostname matches the certificate's Subject Alternative Name.
- It checks that the certificate hasn't expired.
- It checks revocation status (OCSP stapling, CRLite and similar) and Certificate Transparency logs.
- If any check fails, the browser shows the full-page "Your connection is not private" warning.

# Step 5: Client Finished and application data
- The browser sends its own Finished message.
- HTTP requests and responses now flow, encrypted with authenticated encryption (AES-GCM or ChaCha20-Poly1305).
- The full handshake takes **one round trip** in TLS 1.3 (TLS 1.2 needed two).

# Why an ephemeral key exchange matters
- The server's long-term private key is used only to *sign*, never to encrypt the session key.
- So if that key is stolen later, recorded past sessions still can't be decrypted. This is **forward secrecy**.
- Older RSA key exchange (removed in TLS 1.3) didn't have this property.

# Speed-ups
- **Session resumption:** the server gives the browser a pre-shared key (PSK) ticket, so the next handshake can skip certificate checks.
- **0-RTT:** a returning client can send data in its very first message.
  - The trade-off is that this early data can be replayed, so it's limited to safe requests.
- **HSTS:** a site can tell the browser to always use HTTPS, which prevents downgrade to plain HTTP.

# Summary
- Diffie-Hellman creates a shared secret.
- The certificate plus signature proves who holds it.
- Symmetric authenticated encryption protects the actual traffic.
