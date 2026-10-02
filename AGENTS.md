# AGENTS.md

This repo wraps [tomsquest/docker-radicale](https://github.com/tomsquest/docker-radicale)
and adds DecSync support. A scheduled workflow (`.github/workflows/check-upstream.yaml`,
cron `0 6 * * 1`) watches two upstream sources and opens PRs/issues automatically. This
file explains that automation so an agent picking up one of those PRs/issues knows what
to do without re-deriving it.

## 1. Radicale version bumps → auto-opened PR

The workflow reads the current `VERSION` from `Dockerfile` and compares it to the
latest version on PyPI. If newer, it opens a PR titled `Update Radicale to X.Y.Z` on
branch `update-radicale-X.Y.Z` that already contains the mechanical change:

- `Dockerfile`: `VERSION:-<old>` → `VERSION:-<new>`
- `test_image_prod.py`: version string literal updated to match

The PR body has a review checklist (CI passing, DecSync plugin compatibility, Radicale
changelog review for breaking changes). **Working this PR means completing that
checklist, not just merging it**:

1. Let CI run (build + `test_update_config_from_env.py`); fix failures if the Radicale
   bump breaks the build or tests.
2. Check the [Radicale changelog](https://github.com/Kozea/Radicale/blob/master/CHANGELOG.md)
   for the version range for breaking changes (config format, storage format, auth,
   WSGI entrypoint) and adjust `docker-entrypoint.sh` / `config` / `update_config_from_env.py`
   if needed.
3. Sanity-check the DecSync plugin still loads against the new Radicale version.
4. Check off the boxes in the PR description as you verify them, then merge.

If a bump PR is superseded (e.g. a newer version shows up before the old PR merges),
the workflow does not close the stale one — close it manually when superseded.

Note history: PR #7 fixed a case where a version bump PR (#5) missed updating
`test_image_prod.py`, and patched `check-upstream.yaml` so future bump PRs update that
file automatically. If you find another file with a hardcoded version string, add it to
the `sed` step in `check-upstream.yaml` the same way, rather than fixing it by hand each
time.

## 2. Upstream repo drift → auto-opened issue

Separately, the workflow polls `tomsquest/docker-radicale`'s `master` branch. If its
HEAD SHA differs from the SHA recorded in the most recently *closed* `upstream`-labeled
issue, it opens a new issue titled "Upstream docker-radicale has new changes" with a
compare link (`last_sha...new_sha`) and an `<!-- upstream-sha: <sha> -->` marker hidden
in the body. That marker is the only state the workflow uses to track "what's already
been reviewed" — it doesn't diff files itself.

It skips opening a new issue if an `upstream`-labeled issue is already open, so there is
never more than one of these in flight.

**Working one of these issues:**

1. Open the compare link in the issue body — it's a real GitHub diff between the last
   reviewed upstream commit and the new upstream HEAD.
2. Review the diff for anything relevant to this fork: `docker-entrypoint.sh`, `config`,
   Dockerfile base image/build steps, test coverage. Most upstream changes are
   irrelevant (docs, CI tweaks); only cherry-pick what actually matters here.
3. Cherry-pick or re-implement relevant changes as normal commits/PRs against this repo.
4. Close the issue once done. Closing is what lets the workflow record this SHA as the
   new "last checked" baseline — **do not leave it open longer than necessary**, since
   the next scheduled run won't open a new drift issue while one is open, and
   closing it is the only way to move the baseline forward.

## General notes for agents working in this repo

- Don't hand-edit the version-bump or drift-tracking logic lightly — both PRs/issues are
  machine-generated on a schedule, and the `<!-- upstream-sha: ... -->` HTML comment in
  issue bodies is parsed by the workflow, so don't reformat or remove it when editing an
  issue body.
- `uv` manages Python deps (see `pyproject.toml`, `uv.lock`); use `uv run <cmd>`, not a
  bare venv/pip.
- Tests: `uv run pytest` (pre-commit also runs `ruff check --fix`, `ruff format`, and
  pytest on Python files — see `.pre-commit-config.yaml`).
- `build.yaml` runs on PRs (test + multi-arch build, no push). `push_latest.yaml` runs on
  push to `master` (build + push `:latest`). `release.yaml` runs on tag push (build +
  push `:<tag>` and `:latest`). Don't add a manual version bump to any of these — version
  is driven solely by `Dockerfile`'s `VERSION` build arg and git tags.
