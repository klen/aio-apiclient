# aio-apiclient

[![Tests Status](https://github.com/klen/aio-apiclient/workflows/tests/badge.svg)](https://github.com/klen/aio-apiclient/actions)
[![PyPI Version](https://img.shields.io/pypi/v/aio-apiclient)](https://pypi.org/project/aio-apiclient/)
[![Python Versions](https://img.shields.io/pypi/pyversions/aio-apiclient)](https://pypi.org/project/aio-apiclient/)

Most HTTP APIs are a URL, a method and a JSON body. This library lets you spell that
as an attribute chain:

```python
repo = await client.api.repos.klen["aio-apiclient"].get()
```

`GET https://api.github.com/repos/klen/aio-apiclient` is built from the chain, the body
comes back already parsed, and the same client keeps your auth headers, params and
middlewares for every call. It runs on either `httpx` or `aiohttp`, and the client is
generic over the response type you ask for.

## Install

```bash
pip install aio-apiclient[httpx]      # or aio-apiclient[aiohttp]
uv add aio-apiclient[httpx]
```

Python 3.11 or newer. One of the two backends is required; installing both is fine, and
the client picks the first one available unless you name one.

## Quick start

```python
from apiclient import APIClient

client = APIClient(
    "https://api.github.com",
    headers={"Authorization": "token OAUTH-TOKEN"},
)

repo = await client.api.repos.klen["aio-apiclient"].get()
print(repo["full_name"])
```

Paths with dots or an unusual shape are addressed with `[...]` instead of a dot, so
Slack's RPC-style methods work too:

```python
await client.api["users.profile.set"].post(
    json={"profile": {"status_text": "working", "status_emoji": ":computer:"}},
    read_response_body=False,
)
```

## Endpoints

Every attribute adds a path segment, every `[...]` adds one segment too (its value is
stringified, surrounding slashes stripped). Calling the chain sends the request:

```python
await client.api.users()  # GET  /users
await client.api.users.post()  # POST /users
await client.api.users[42].get()  # GET  /users/42
await client.api.users[42].put({"a": "b"})  # PUT  /users/42, body -> data=
```

The last segment is the HTTP method when it is `get`, `post`, `put`, `patch`, `delete`,
`head` or `options`, and no method is passed explicitly. Endpoints whose own path ends
with one of those words need the method spelled out:

```python
await client.api.files.delete(method="DELETE")  # DELETE /files/delete
```

A positional argument becomes the request body, `data=` form-encoded, `json=` for JSON;
everything else is passed to the backend unchanged. Rendering an endpoint (`str()`,
`repr()`, logging) never changes it, and the same endpoint object can be awaited as many
times as you like.

## Responses

`read_response_body` and `parse_response_body` decide what a call returns.

| `read_response_body` | `parse_response_body` | You get |
| --- | --- | --- |
| `True` (default) | `True` (default) | JSON/`dict` for JSON responses, `str` for everything else |
| `True` | `False` | The backend response object, body already read (`httpx.Response` or `aiohttp.ClientResponse`) |
| `False` | any | The response object with the body **not** read; it is closed already, and sending is all you get |

Both flags can be set per client (the default) or per call. The raw object is backend
specific: `httpx.Response` has `.status_code` and `.json()`, `aiohttp.ClientResponse` has
`.status` and `.text()`.

## Errors

`raise_for_status=True` is the default: any 4xx or 5xx response raises. The exception
class is the backend's own (`httpx.HTTPStatusError`, `aiohttp.ClientResponseError`), so
catch `client.Error`, which points at whichever backend is in use:

```python
from apiclient import APIClient

client = APIClient("https://api.github.com")

try:
    await client.api.users.doesnotexist()
except client.Error as exc:
    print("API said no:", exc)
```

Turn it off per call (`raise_for_status=False`) when a 404 is an expected answer and you
want to look at the body yourself.

## Defaults

Keyword arguments other than the reserved ones (`backend_type`, `backend_options`,
`raise_for_status`, `read_response_body`, `parse_response_body`, `timeout`, `uds`) are
remembered as request defaults:

```python
client = APIClient("https://api.example.com", headers={"X-Api-Key": "…"}, params={"lang": "en"})

# the dict default is merged: lang=en and q=notes are both sent
await client.api.search.get(params={"q": "notes"})
```

A dict passed to a call is merged into the same-named default (`headers` override one
header, they do not replace the dict); any other type replaces the default. Defaults are
copied for every request, so a middleware that edits `options` cannot corrupt the client.

## Middlewares

A middleware sees and may change the method, the URL and the options before the request
leaves. Registration order is execution order.

```python
import time


@client.middleware
async def insert_timestamp(method, url, options):
    options.setdefault("headers", {})["X-Timestamp"] = str(time.time())
    return method, url, options
```

## Backends

```python
from apiclient.backends import BackendAIOHTTP, BackendHTTPX

client = APIClient("https://api.example.com", backend_type=BackendAIOHTTP)
client = APIClient("https://api.example.com", backend_type="httpx")
```

`backend_options` are forwarded to the backend constructor. Pass your own client to keep
a connection pool, retries or a transport you configured yourself:

```python
import httpx

transport = httpx.MockTransport(handler)
client = APIClient(
    "https://api.example.com",
    backend_options={"client": httpx.AsyncClient(transport=transport)},
)
```

Unix sockets use a `uds://` root, and the path is passed to the backend as a socket path:

```python
client = APIClient("uds:///var/run/docker.sock")
await client.api.containers.json()
```

## Lifespan

`await client.startup()` and `await client.shutdown()` are the hooks app frameworks call
on boot and on exit. Calling them is optional, with one caveat: the `aiohttp` backend
creates its session on the first request if `startup()` was not called, and that session
belongs to the event loop it was created in. Reuse a client inside one loop, or call
`startup()` from the loop that will use it.

## Typing

The client, the descriptor and the backend responses are generic:

```python
import httpx

client: APIClient[httpx.Response] = APIClient("https://api.github.com")

raw = await client.api.users.me(parse_response_body=False)
raw.status_code  # typed: httpx.Response
```

Parsed bodies are typed as `TResponseBody` (`dict | list | str | int | float | bool |
None`), because the content type is only known at runtime. The package ships `py.typed`
and the test suite keeps type coverage at 100 percent.

## Development

```bash
make install    # uv sync + git hooks
make test       # pytest, hermetic: no network, no tokens
make types      # pyrefly check + type coverage
```

Tests use `httpx.MockTransport` and a local `aiohttp` `TestServer`; add new cases the same
way instead of calling a real API.

## Issues and license

Bugs and ideas go to https://github.com/klen/aio-apiclient/issues. Code is under the
[MIT license](https://opensource.org/licenses/MIT).
