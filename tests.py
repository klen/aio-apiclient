from __future__ import annotations  # noqa: INP001

import copy
from collections.abc import Iterator
from unittest import mock

import httpx
import pytest

REPO = {"id": 1, "full_name": "klen/aio-apiclient"}


def fake_github(request: httpx.Request) -> httpx.Response:
    """Answer like GitHub API does."""
    if request.url.path.endswith("/raise404"):
        return httpx.Response(404, json={"message": "Not Found"})
    return httpx.Response(200, json=REPO)


@pytest.fixture()
def mock_httpx() -> Iterator[mock.MagicMock]:
    with mock.patch("httpx.AsyncClient.send") as mocked:
        mocked.return_value = httpx.Response(200, request=httpx.Request("GET", "/"), text="httpx")
        yield mocked


def test_descriptor() -> None:
    from apiclient.api import HTTPDescriptor

    request = mock.MagicMock()
    api = HTTPDescriptor(request)
    assert api
    assert api.users != api.users

    assert str(api) == "GET /"
    assert str(api.groups[1].users.post) == "POST /groups/1/users"
    assert str(api.users[1].post.post) == "POST /users/1/post"

    api.users[42].put(data={"login": "updated"})
    request.assert_called_with("PUT", "/users/42", data={"login": "updated"})

    api.users[42].put(method="POST", data={"login": "updated"})
    request.assert_called_with("POST", "/users/42/put", data={"login": "updated"})

    api.users[42].post({"test": "ok"})
    request.assert_called_with("POST", "/users/42", data={"test": "ok"})

    api.users[42]["/custom/path"]()
    request.assert_called_with("GET", "/users/42/custom/path")

    # An empty body is still a body
    api.users[42].post({})
    request.assert_called_with("POST", "/users/42", data={})

    # A path segment named like a method needs an explicit method
    api.files.delete(method="DELETE")
    request.assert_called_with("DELETE", "/files/delete")

    # Rendering and repeating a call must not change it
    endpoint = api.users.post
    assert str(endpoint) == "POST /users"
    endpoint()
    endpoint()
    request.assert_called_with("POST", "/users")


def test_descriptor_copies() -> None:
    from apiclient.api import HTTPDescriptor

    api = HTTPDescriptor(mock.MagicMock())

    # Dunder lookups stay normal, so copy/pickle keep working
    assert not hasattr(api, "__wrapped__")
    assert str(copy.deepcopy(api.users)) == "GET /users"


def test_no_backends_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    import apiclient

    monkeypatch.setattr(apiclient, "BACKENDS", [])
    with pytest.raises(RuntimeError):
        apiclient.APIClient("https://api.github.com")


def test_sync_initialization() -> None:
    from apiclient import APIClient
    from apiclient.backends import BackendAIOHTTP, BackendHTTPX

    client = APIClient("https://api.github.com")
    assert isinstance(client.backend, BackendHTTPX)

    client = APIClient("https://api.github.com", backend_type="httpx")
    assert isinstance(client.backend, BackendHTTPX)

    client = APIClient("https://api.github.com", backend_type=BackendAIOHTTP)
    assert client
    assert isinstance(client.backend, BackendAIOHTTP)


async def test_client() -> None:
    from apiclient import APIClient

    backend = mock.AsyncMock()

    client = APIClient("https://api.github.com", headers={"Authorization": "Bearer TOKEN"})
    assert client
    assert client.api
    assert client.defaults
    assert client.Error

    client.backend = backend

    ts = 12345

    @client.middleware
    async def insert_timestamp(method, url, options):
        options.setdefault("headers", {})
        options["headers"]["X-Timestamp"] = str(ts)
        return method, url, options

    res = await client.api.users.octocat.orgs()
    assert res
    backend.request.assert_awaited_with(
        "GET",
        "https://api.github.com/users/octocat/orgs",
        raise_for_status=True,
        read_response_body=True,
        parse_response_body=True,
        headers={"Authorization": "Bearer TOKEN", "X-Timestamp": str(ts)},
    )


async def test_defaults_and_middlewares() -> None:
    from apiclient import APIClient

    backend = mock.AsyncMock()
    client = APIClient("https://api.github.com", params={"page": "1"}, headers={"X-Token": "1"})
    client.backend = backend
    order = []

    @client.middleware
    async def first(method, url, options):
        order.append("first")
        return method, url, options

    @client.middleware
    async def second(method, url, options):
        order.append("second")
        return method, url, options

    # A non-dict override is passed through instead of crashing the merge
    await client.api.users.get(params=[("page", "2")])
    assert order == ["first", "second"]
    backend.request.assert_awaited_with(
        "GET",
        "https://api.github.com/users",
        params=[("page", "2")],
        raise_for_status=True,
        read_response_body=True,
        parse_response_body=True,
        headers={"X-Token": "1"},
    )

    # Defaults are not changed by requests
    assert client.defaults == {"params": {"page": "1"}, "headers": {"X-Token": "1"}}


@pytest.mark.parametrize("aiolib", ["asyncio"])
async def test_aiohttp_startup() -> None:
    from apiclient.backends import BackendAIOHTTP

    backend = BackendAIOHTTP()
    assert backend._client is None
    await backend.startup()
    assert backend._client is not None
    await backend.shutdown()


async def test_uds_httpx(mock_httpx: mock.MagicMock) -> None:
    from apiclient import APIClient

    client = APIClient("uds:///var/run/docker.sock")
    res = await client.api.containers.json()
    assert res


@pytest.mark.parametrize("aiolib", ["asyncio", "trio"])
async def test_httpx() -> None:
    from apiclient import APIClient
    from apiclient.backends import BackendHTTPX

    client = APIClient(
        "https://api.github.com",
        backend_options={"client": httpx.AsyncClient(transport=httpx.MockTransport(fake_github))},
    )
    assert isinstance(client.backend, BackendHTTPX)

    with pytest.raises(client.Error):
        await client.api.users.klen.raise404()

    res = await client.api.repos.klen["aio-apiclient"](
        raise_for_status=False, parse_response_body=False
    )
    assert res.status_code == 200
    assert res.json()

    res = await client.api.repos.klen["aio-apiclient"]()
    assert res == REPO

    await client.shutdown()


@pytest.mark.parametrize("aiolib", ["asyncio"])
async def test_aiohttp() -> None:
    from aiohttp import web
    from aiohttp.test_utils import TestServer

    from apiclient import APIClient
    from apiclient.backends import BackendAIOHTTP

    async def handler(request: web.Request) -> web.Response:
        if request.path.endswith("/raise404"):
            return web.json_response({"message": "Not Found"}, status=404)
        return web.json_response(REPO)

    app = web.Application()
    app.router.add_route("*", "/{tail:.*}", handler)
    server = TestServer(app)
    await server.start_server()

    client = APIClient(str(server.make_url("/")), backend_type=BackendAIOHTTP)

    with pytest.raises(client.Error):
        await client.api.users.klen.raise404()

    res = await client.api.repos.klen["aio-apiclient"](parse_response_body=False)
    assert res.status == 200
    assert "aio-apiclient" in await res.text()

    res = await client.api.repos.klen["aio-apiclient"]()
    assert res == REPO

    await client.shutdown()
    await server.close()
