```
                 ┌──────────────────────────────┐
                 │  8 engineers: use a MONOREPO │
                 └──────────────┬───────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐      ┌─────────────────┐     ┌─────────────────┐
│ Why it wins   │      │ Cost at your    │     │ Keep it healthy │
│               │      │ size            │     │                 │
│ - Atomic      │      │ - Minimal:      │     │ - CODEOWNERS    │
│   cross-      │      │   plain CI and  │     │   per directory │
│   service     │      │   git are fine  │     │ - Path-filtered │
│   changes     │      │ - Clone/build   │     │   CI jobs       │
│ - One CI,     │      │   time stays    │     │ - Shared deps   │
│   one tooling │      │   small         │     │   in one place  │
│   setup       │      │ - No need for   │     │ - Add Nx/Turbo/ │
│ - Easy code   │      │   Bazel-scale   │     │   Bazel only if │
│   sharing and │      │   tooling       │     │   builds slow   │
│   refactors   │      │                 │     │                 │
└───────────────┘      └─────────────────┘     └─────────────────┘
                                │
                                ▼
                 ┌──────────────────────────────┐
                 │ Split into multiple repos    │
                 │ only if:                     │
                 │ - Components need different  │
                 │   access control or licenses │
                 │ - Independent release cycles │
                 │   with separate owners       │
                 │ - Open-sourcing one piece    │
                 └──────────────────────────────┘
```

With eight people, you probably share context and change things across boundaries often. A monorepo makes those changes atomic and avoids the overhead of versioning and publishing internal packages between repos. Multi-repo pays off when teams are autonomous or when you have security or licensing boundaries, which a team this size usually doesn't have. You can also split a monorepo later with `git filter-repo`, and that is easier than merging many repos.
