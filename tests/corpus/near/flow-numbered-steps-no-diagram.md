1. The browser resolves the domain name to an IP address.
2. It opens a TCP connection to the server on port 443.
3. The server sends its certificate during the TLS handshake.
4. The browser verifies the certificate against trusted authorities.
5. Both sides derive session keys and encrypt the traffic that follows.
