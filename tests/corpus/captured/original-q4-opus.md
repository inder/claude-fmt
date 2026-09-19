**My recommendation for eight engineers is a monorepo**, unless one of the exceptions below applies.

## Why a monorepo usually works better at this size

- **Changes that touch several parts land together.** One PR can change an API, its callers and the shared types. With separate repos you'd need a chain of PRs and version bumps.
- **You don't have to manage versions of your own code.** Internal libraries don't need publishing, semver or "which service is on which version" tracking. Everything builds against HEAD.
- **Tooling is set up once.** One CI config, one lint and format setup, one dependency update process (Renovate or Dependabot), one place to search.
- **Refactoring is easier.** Renaming something across the codebase is one grep and one PR.
- **The usual downsides mostly start with larger teams.** Slow CI, confusing ownership and build-tool complexity tend to hurt at 50+ engineers or very large codebases, not at 8.

## When multiple repos make sense

- **The parts really are independent,** with different languages, release cycles or users. An example is a mobile app, a backend and an unrelated data pipeline that rarely change together.
- **Access has to be restricted,** for compliance reasons or because contractors should only see part of the code.
- **You publish open-source components** that need their own issues, releases and contributors.
- **The deploy cadences are very different,** such as firmware shipped quarterly next to a web app deployed 20 times a day.

## If you choose a monorepo, set these up early

1. **CI that only builds what changed**, using path filters or a tool like Turborepo, Nx, Bazel or Pants. Pick the lightest tool that works for your language.
2. **A CODEOWNERS file**, so reviews go to the right people.
3. **A clear folder layout**, for example `apps/`, `services/`, `packages/` or `libs/`.
4. **Deploys for each service** that trigger when that service's paths change.

## A quick test

Ask how often one feature needs changes in more than one component. If it happens often, use a monorepo. If it almost never does, separate repos cost little and keep boundaries clear.

A common middle ground is one monorepo for the product, with separate repos only for components that are truly independent or public.

If you tell me your languages, number of services and how you deploy, I can give a more specific answer.
