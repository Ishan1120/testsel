# Contributing to testsel

Welcome to the `testsel` project! We use a collaborative workflow built around clear ownership, automated quality gates, and structured commit history.

## Branch Naming Conventions
Always create descriptive branch names prefixed with the category of change:
- `feat/<description>`: New functionality (e.g., `feat/collector-retry-logic`)
- `fix/<description>`: Bug fixes (e.g., `fix/junit-duration-parsing`)
- `docs/<description>`: Documentation changes (e.g., `docs/update-adr`)
- `chore/<description>`: Maintenance, tool upgrades, dependency bumps (e.g., `chore/bump-psycopg`)

## Conventional Commits
All commit messages must adhere to the [Conventional Commits](https://www.conventionalcommits.org/) specification:
```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```
Types include: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`.

## Pull Request Guidelines
- **Scope & Size**: Keep PRs focused, ideally under ~400 lines of changes. Smaller PRs are easier to review and merge quickly.
- **Review Requirement**: The other developer must review and approve before merging.
- **Merge Strategy**: Use **Squash and Merge** to maintain a clean linear history on `main`.
- **Progress Tracking**: Update [docs/PROGRESS.md](docs/PROGRESS.md) in every PR that completes or starts a task.
- **Pre-flight Checks**: Before opening or requesting review on a PR, run:
  ```bash
  make lint
  make test
  ```
  Ensure all automated GitHub Actions checks pass.

## Testing Guidelines
- Add unit tests under `tests/unit/` for all new core logic.
- Place integration tests requiring a live PostgreSQL instance under `tests/integration/` and mark them with `@pytest.mark.integration`.
- All tests must pass cleanly without network flakiness.
