Resolve DNS → open TCP → TLS handshake → verify certificate → exchange keys → encrypted HTTP.

The browser first resolves the domain name, then opens a TCP connection to the server. During the TLS handshake the server presents its certificate, the browser checks it against trusted authorities, and both sides agree on session keys that encrypt everything that follows.
