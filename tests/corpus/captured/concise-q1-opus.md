HTTPS is HTTP sent over TLS. With TLS 1.3, a connection is set up like this:

1. **ClientHello:** The browser sends the TLS versions and cipher suites it supports, a random value, and a key share (an ephemeral Diffie-Hellman public key).
2. **ServerHello:** The server picks the cipher and sends its own key share. Both sides can now work out the same shared secret, and it never crosses the network.
3. **Certificate:** The server sends its certificate chain and signs the handshake with its private key. This proves it owns the certificate.
4. **Verification:** The browser checks that the chain leads to a trusted root CA, that the hostname matches, that the certificate hasn't expired, and whether it has been revoked.
5. **Finished:** Both sides turn the shared secret into symmetric session keys (for example AES-GCM or ChaCha20). They then exchange MACs over the handshake to detect tampering.
6. **Data:** All HTTP traffic is now encrypted and integrity-protected.

Because the keys are ephemeral, this also gives forward secrecy.
