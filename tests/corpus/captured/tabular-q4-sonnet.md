**Recommendation: monorepo.**

| Factor | Monorepo | Multiple repos | Verdict for 8 engineers |
| --- | --- | --- | --- |
| Cross-cutting changes | One atomic PR/commit | Coordinated PRs and version bumps | Monorepo |
| Tooling and CI setup | One pipeline, one set of configs | Duplicated per repo | Monorepo |
| Code sharing | Direct imports, no publishing | Requires packages and versioning | Monorepo |
| Onboarding and discoverability | Clone once, search everything | Must learn which repo holds what | Monorepo |
| Scaling cost (CI time, repo size) | Needs caching/affected-only builds later | Not an issue | Not a concern at this size |
| Access control | Coarse (whole repo) | Per-repo permissions | Only matters with strict security boundaries |
| Independent release cadence | Needs path-based pipelines | Natural | Manageable in a monorepo |

| Choose multiple repos only if... | Why |
| --- | --- |
| Components have different security or compliance boundaries | Per-repo access control |
| Parts are open-sourced or owned by external teams | Separate lifecycle and visibility |
| Services use unrelated stacks with no shared code | Little benefit from colocation |

A team of eight is small enough that the usual monorepo pain points (slow CI, ownership conflicts) rarely appear. Start with one repo, and split later if a real boundary emerges.
