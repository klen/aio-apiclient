# Changelog

All notable changes to this project are documented here, newest first.
Each entry is headed by the release date and the version it was released as.
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 2026-11-19 · Unreleased
### Changed
- Packaging moved to `uv` and `pyproject.toml` (`setup.py`, `setup.cfg` and
  `requirements/` are gone, use `uv sync` / `uv run pytest`)
- CI runs on `uv` across python 3.11–3.15; Slack notify jobs removed
- `mypy` replaced with `pyrefly` for type checking; 100% type coverage is enforced
- `pre-commit` with ruff (lint + format), pyrefly, pytest and basic hygiene hooks
- Type annotations use python 3.11 syntax (`X | None`, builtin generics, `Self`)
- Tests no longer call the GitHub API: httpx is mocked, aiohttp runs against a
  local `TestServer`, so the suite needs no network and no token
- `HTTPDescriptor` and `APIClient` are generic over the response type: annotating
  `APIClient[httpx.Response]` makes `await client.api.path.method()` return a typed response

### Fixed
- `str()`/`repr()` on an endpoint no longer changes the next request, and an endpoint can
  be awaited more than once
- An empty body (`{}`, `[]`, `0`, `""`) is sent instead of being dropped
- Overriding a dict default with a non-dict value (e.g. `params=[("a", "1")]`) no longer
  raises `TypeError`; defaults are deep-copied so requests cannot change them
- Middlewares now run in registration order
- aiohttp session is created in `startup()`, so a client used in a second event loop no
  longer hangs until timeout
- `copy`/`deepcopy` and `hasattr` work on endpoints (dunder names are no longer treated as
  path segments)
- Release workflow publishes on tag push instead of every green `main` build
- Endpoints whose last path segment is an HTTP method are documented and covered by a test
- `parse_response_body=False` now returns a response with the body already read on the
  aiohttp backend too, as it already did for httpx

### Removed
- Support for python < 3.11

### Docs
- README rewritten in Markdown and covers endpoints, response modes, errors, defaults,
  middlewares, backends, lifespan and typing, with a table of what each call returns
- Docstrings explain the descriptor chain, the defaults merge and middleware order

## 2023-02-03 · 1.7.0
### Added
- Support for python 3.11

## 2021-10-20 · 1.6.0
### Added
- Support for python 3.10

## 2021-06-29 · 1.5.1
