- **Resolver cache**
  The operating system checks its own cache and the hosts file before asking anyone else.
- **Recursive resolver**
  Your ISP or a public resolver takes the query and does the remaining work for you.
- **Root and TLD servers**
  They point the resolver at the servers responsible for the domain's top-level zone.
- **Authoritative server**
  It returns the actual record, which is then cached for the time the record allows.
