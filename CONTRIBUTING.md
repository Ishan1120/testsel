# Contributing to Testsel

Thank you for contributing to Testsel. This guide outlines branch naming, commit conventions, PR guidelines, and testing requirements for the team.

## Branch Naming
All branches must follow one of these prefixes:
- `feat/`: New features, capabilities, or pipeline additions (e.g., `feat/junit-retry-parser`, `feat/lightgbm-training`)
- `fix/`: Bug fixes and error handling corrections (e.g., `fix/github-rate-limit-backoff`)
- `docs/`: Documentation, ADRs, or architectural guides (e.g., `docs/adr-dataset-storage`)
- `chore/`: Tooling updates, dependency bumps, or repo maintenance (e.g., `chore/pre-commit-upgrade`)

## Commit Conventions
We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
- Format: `<type>(<scope>): <short description>`
- Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`
- Scope: Module or area modified (e.g., `collector`, `shared`, `ci`, `store`, `evaluation`)
- Examples:
  - `feat(collector): support multi-token rotation for GitHub client`
  - `fix(store): resolve schema path resolution in monorepo layout`
  - `test(junit): add XML entity injection bomb rejection test`

## Pull Request Rules
1. **Size Limit**: Keep PRs focused and under approximately 400 lines of changed code whenever feasible.
2. **Review Process**: The other developer must review and approve the PR before merging (see `.github/CODEOWNERS`).
3. **Merge Method**: Use **Squash and Merge** to maintain a linear and scannable Git history on `main`.
4. **Clean CI**: All CI checks (`test` job running linter, formatter, and pytest) must pass green before merging.
5. **Secrets Hygiene**: Never commit `.env` files, production credentials, or personal access tokens.

## Testing Rules
- Every feature or bug fix must include accompanying unit tests under `tests/unit/`.
- Integration tests requiring live PostgreSQL or network services belong in `tests/integration/` and must be marked with `@pytest.mark.integration`.
- Run verification locally before submitting PRs:
  ```bash
  make lint
  make test
  ```
