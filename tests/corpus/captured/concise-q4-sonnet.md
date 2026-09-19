**Monorepo.** At eight engineers, it's the better default.

- **Atomic changes:** one PR can touch a service, its shared library, and its consumers. No version-bump choreography.
- **Less overhead:** one CI config, one set of tooling, one dependency policy, one place to search.
- **Easier onboarding and refactors:** everything is visible and greppable.
- **Multi-repo costs:** cross-repo coordination, version drift, and duplicated setup all pay off only when teams need independence you don't have yet.

**Caveats:**
- Use path-filtered or affected-only CI (Nx, Turborepo, Bazel, or simple path filters) so builds stay fast.
- Use CODEOWNERS if ownership matters.

**Choose multiple repos instead if:**
- Components have different release cadences or hard security or access boundaries.
- Parts are open-sourced or shared externally.
- Services are in different languages with no shared code or tooling.

You can split a monorepo later much more easily than you can merge many repos.
