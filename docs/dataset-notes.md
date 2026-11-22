# Dataset Notes & Quality Log

## Repositories Chosen
Document target open-source repositories verified to publish JUnit XML test reports via GitHub Actions artifacts.
- Target candidates:
  - Repositories using `pytest --junitxml=...`, Maven Surefire, or Jest JUnit reporters.
  - Repositories with frequent pull request activity, non-trivial test suites, and mixed pass/fail signals.

| Repository | Tech Stack | Report Pattern | Notes / Validation Date |
|------------|------------|----------------|-------------------------|
| *Example: owner/repo* | Python / Pytest | `pytest-junit` | Initial verification pending |

## Data-Quality Problems Found
Log edge cases and anomalies encountered during historical data collection:
- **Missing or Expired Artifacts**: GitHub Actions artifacts expire after 90 days (or repo-specific retention windows).
- **Flaky Tests**: Tests that fail on run attempt 1 but pass on run attempt 2 without code changes.
- **Fork PR Disconnection**: GitHub Actions workflow runs triggered from fork pull requests omit PR associations in API responses.
- **XML Format Deviations**: Differences in JUnit XML schemas across frameworks (e.g., missing `classname` or non-standard time attributes).
- **Large Diffs**: PRs with massive generated files or vendored dependencies requiring patch truncation.

## Decisions & Filtering Strategies
- **Deduplication**: Keep the most severe outcome (`error` > `fail` > `pass` > `skip`) when duplicate test IDs occur within a single run.
- **Security Limits**: Enforce maximum uncompressed size and entry limits on zip files to guard against archive bombs; reject XML containing `DOCTYPE` or `ENTITY` declarations.
- **Scope Constraints**: Skip runs whose conclusions are neither `success` nor `failure` (e.g., `cancelled`, `timed_out`, `action_required`).
- **Baseline Freezing**: Freeze finalized datasets into versioned Parquet splits using DVC before training baseline models.
