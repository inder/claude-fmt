Recommendation: a monorepo, unless you have a hard reason to split.

```
Start: 8 engineers
   │
   ↓
Do you ship independently deployed
services with separate release cycles
AND separate owning teams?
   │
   ├── No (typical for 8 people) ──→ MONOREPO
   │                                    │
   │                                    ↓
   │                          One PR spans app + lib + infra
   │                          Shared tooling, CI, versions
   │                          No cross-repo dependency drift
   │
   └── Yes
        │
        ↓
   Do you have compliance/access limits,
   open-source components, or wildly
   different stacks?
        │
        ├── Yes ──→ MULTIPLE REPOS (split only those parts)
        │
        └── No ───→ MONOREPO anyway
                        │
                        ↓
              Revisit if: CI exceeds ~15 min
              without caching, or teams
              start blocking each other
```

Why: at eight people, coordination cost is low, so atomic cross-project changes, one CI setup, and a single source of truth for dependencies matter more than repo isolation. The usual monorepo downsides (slow builds, permission granularity, tooling at scale) don't show up until you're much larger, and splitting later is easier than merging many repos back together.

Keep it healthy with path-based CI filtering or a build cache (Turborepo, Nx, Bazel), plus CODEOWNERS for clear ownership.
