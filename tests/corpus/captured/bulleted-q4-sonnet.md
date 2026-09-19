- **Recommendation: monorepo.** At eight engineers, it's the better default.

- **Why it fits a team this size**
  - Atomic changes: one PR can touch a library and all its consumers, so there's no version-skew or cross-repo coordination.
  - One place for CI config, linting, tooling, and dependency versions.
  - Easier discovery and onboarding: everything is searchable and cloneable in one step.
  - Refactors are cheap, which matters most while the architecture is still changing.

- **Costs of the monorepo (small at this scale)**
  - CI can get slow as the repo grows. Path-based filtering or a build tool (Nx, Turborepo, Bazel, Pants) fixes this when needed.
  - Coarse access control. That's rarely a problem for eight people who all work together.
  - Requires some discipline about module boundaries, for example via CODEOWNERS and lint rules.

- **When multiple repos make more sense**
  - Components have truly independent release cycles or separate owning teams.
  - You need different access or compliance boundaries, such as open-source pieces or contractors.
  - Services use completely different stacks with no shared code.
  - You're publishing libraries externally with their own versioning and issue trackers.

- **Practical advice**
  - Start with a monorepo and split out a piece later if a real need appears. Splitting is easier than merging repos back together.
  - Don't adopt heavy tooling like Bazel up front. Workspaces (pnpm, Cargo, Go modules, etc.) plus path-filtered CI are enough at this size.

- **Caveat**: if your eight engineers are split into two or three sub-teams working on unrelated products, separate repos are reasonable. Tell me your stack and how the team divides up, and I can be more specific.
