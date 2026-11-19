# AGENTS.md

## Repository overview

`aio-apiclient` is a small async HTTP client library: you build URLs by attribute
access (`client.api.repos.klen["x"].get()`), it merges per-client defaults and
middlewares, then calls `httpx` or `aiohttp`. No runtime dependencies; a backend is
an optional extra (`aio-apiclient[httpx]`, `aio-apiclient[aiohttp]`). Python >= 3.11.

- `apiclient/__init__.py` — `APIClient`: URL build, defaults merge, middleware chain,
  backend dispatch (`__request` casts to `TResponse`). Version comes from
  `importlib.metadata`, never a literal.
- `apiclient/api.py` — `HTTPDescriptor`: attribute access builds the path. The **last**
  path segment is the HTTP method when it is `get`/`post`/`put`/`patch`/`delete`/`head`/
  `options`; `__render__` must never mutate state (no `pop`), and `__getattr__` must raise
  `AttributeError` for dunder names so `copy`/`pickle` keep working.
- `apiclient/backends/__init__.py` — `ABCBackend` + the `BACKENDS` registry (subclasses
  self-register in `__init_subclass__`); both backends are imported under
  `suppress(ImportError)`.
- `apiclient/backends/_httpx.py`, `_aiohttp.py` — one file per backend, same contract.
  aiohttp's session is created in `startup()` (it binds to the running event loop).
- `apiclient/types.py` — `TResponseBody`, `TMiddleware`, `TRequestFn` protocol.
- `tests.py` — the whole suite in one file (`testpaths` points at it), hermetic, no network.
- `pyproject.toml` — metadata + static version, `[dependency-groups] dev`, ruff, pyrefly
  and pytest config. `uv.lock` is committed.
- `Makefile` — `install` (`uv sync` + `pre-commit install`), `test`, `types`, `version`, `clean`.
- `.github/workflows/tests.yml` (matrix 3.11–3.15) and `release.yml` (publishes on tag push).
  Branches: `develop` for work, `main` for releases. No notifications: CI only runs checks and publishes.
- `CHANGELOG.md` — sections are `## <YYYY-MM-DD> · <version>`, newest first.
- `.tox/` is leftover from the old tox setup; ignore it, it is not part of the build.

## High-risk commands

- `make version [VERSION=…]` (shortcuts: `make minor`, `make patch`, `make major`) — bumps the version, **commits**, **tags**, checks out
  `main`, pulls, merges `develop`, then pushes both branches and all tags. A pushed tag
  triggers `release.yml`, which publishes to PyPI. Never run without explicit instruction.
- `git push`, `git push --tags`, `git tag` — same publish trigger; ask first. Never force-push.
- `make clean` — `rm -rf build/ dist/ *.egg-info` plus deletion of `*.py[co]` and
  `__pycache__`. Safe in principle, destructive in practice; confirm before running.
- `uv lock --upgrade` — re-resolves every dependency; a normal change should only run
  `uv lock` (or `uv add`) so unrelated pins do not move.
- `rm -rf .venv` — prefer `uv sync`, which repairs the environment in place.

## Safe validation

```bash
uv sync                             # idempotent, repairs .venv
uv run pytest                       # full suite (testpaths = tests.py)
uv run pytest -k descriptor         # single test by pattern
uv run ruff check .                 # lint (config in [tool.ruff])
uv run ruff format --check .        # formatting
uv run pyrefly check                # types
uv run pyrefly coverage check       # must stay at 100% — CI fails below it
uv run pre-commit run --all-files   # ruff + pyrefly + pytest in one go
uv lock --check                     # lockfile matches pyproject.toml
uv build                            # wheel/sdist sanity; dist/ is gitignored
```

`make test` and `make types` also work but depend on `install`, which runs
`pre-commit install` and rewrites `.git/hooks/pre-commit`.

## Editing guidelines

- Python 3.11+ syntax only: `X | None`, `list[str]`/`dict[str, Any]`, `Self`,
  `collections.abc` for `Awaitable`/`Callable`. Keep annotations complete — pyrefly
  coverage is a 100% gate.
- Any behavior change in a backend must land in both `_httpx.py` and `_aiohttp.py`,
  and in the `ABCBackend.request` overrides. Tests assert the same results for both.
- Do not delete `[tool.ruff]` or `[tool.pyrefly]` from `pyproject.toml`; without them
  ruff falls back to a developer's global `~/.ruff.toml` (often `select = ["ALL"]`) and
  the repo suddenly has dozens of errors.
- Tests must stay offline: httpx is faked with `httpx.MockTransport` passed via
  `backend_options={"client": …}`; aiohttp runs against `aiohttp.test_utils.TestServer`.
  pytest-aio parametrizes every async test over asyncio/trio/curio, so a test that needs
  aiohttp must be pinned with `@pytest.mark.parametrize("aiolib", ["asyncio"])`.
- When touching `HTTPDescriptor.__render__`/`__call__`, update `README.md` and the
  `test_descriptor` assertions together: bodies are sent when `body is not None` (empty
  dicts included), defaults are deep-copied per request, middlewares run in registration
  order, and `method=` is the escape hatch for paths ending in a verb-like segment.
- `read_response_body=False` returns an already-closed response; keep that documented in
  the backend docstrings and README rather than “fixing” it silently.
- Commit messages follow conventional commits (`feat:`, `fix:`, `build:`); the release
  helper writes `build(version): <new>`.
- Do not add dependencies for a few lines; the stdlib (`copy`, `importlib.metadata`,
  `urllib.parse`) is the house style.

## Files and directories to avoid

- `uv.lock` — generated; change it only through uv commands, never by hand.
- `.github/workflows/release.yml` — a mistake here publishes to PyPI.
- `apiclient/__version__` / `pyproject.toml` version — single source is `pyproject.toml`
  (static); `apiclient.__version__` reads installed metadata, do not hardcode it again.
- `CHANGELOG.md` — keep the date/version heading format; add entries under the
  top `Unreleased` section.
- `.pre-commit-config.yaml` — hook ids and revs are pinned; bump them deliberately.

## Good defaults for agents

- Run `uv run pre-commit run --all-files` before reporting a change as done; it covers
  lint, format, types and tests.
- Never commit, tag, push or bump the version unless the user asks for it explicitly.
- Prefer deleting code over adding an option; this library is intentionally tiny, and a
  new flag or backend hook has to be documented, typed and tested twice (both backends).
