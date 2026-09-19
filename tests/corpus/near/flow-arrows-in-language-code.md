```rust
fn handshake(conn: &mut Conn) -> Result<Session> {
    let cert = conn.server_cert()?;
    let keys = negotiate(&cert)?;
    conn.state = State::Open;
    Ok(Session::new(keys))
}
impl Drop for Conn { fn drop(&mut self) -> () {} }
let f = |x| -> u8 { x };
```

The browser first resolves the domain name, then opens a TCP connection to the server. During the TLS handshake the server presents its certificate, the browser checks it against trusted authorities, and both sides agree on session keys that encrypt everything that follows.
