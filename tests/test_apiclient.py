import unittest.mock as mock

import pytest


def test_descriptor():
    from apiclient.api import APIDescriptor

    request = mock.MagicMock()
    api = APIDescriptor(request)
    assert api
    assert api.users != api.users

    assert str(api) == "GET /"
    assert str(api.groups[1].users.post) == "POST /groups/1/users"
    assert str(api.users[1].post.post) == "POST /users/1/post"

    api.users[42].put(data={'login': 'updated'})
    request.assert_called_with('PUT', '/users/42', data={'login': 'updated'})

    api.users[42].put(method="POST", data={'login': 'updated'})
    request.assert_called_with('POST', '/users/42/put', data={'login': 'updated'})


async def test_client():
    from apiclient import APIClient

    backend = mock.AsyncMock()

    client = APIClient('https://api.github.com', backend=backend, headers={
        'Authorization': 'Bearer TOKEN'
    })
    assert client
    assert client.api
    assert client.defaults
    assert client.Error

    res = await client.api.users.octocat.orgs()
    assert res
    backend.request.assert_awaited()


def test_sync_initialization():
    from apiclient import APIClient
    from apiclient.backends import BackendAIOHTTP

    client = APIClient('https://api.github.com')
    assert client

    client = APIClient('https://api.github.com', backend=BackendAIOHTTP())
    assert client


async def test_httpx():
    """FIXME: makes real requests to Github API."""
    from apiclient import APIClient
    from apiclient.backends import BackendHTTPX

    client = APIClient('https://api.github.com')
    assert isinstance(client.backend, BackendHTTPX)

    with pytest.raises(client.Error):
        await client.api.users.klen.raise404()

    res = await client.api.repos.klen.modconfig(raise_for_status=False, parse_response_body=False)
    assert res.status_code == 200

    res = await client.api.repos.klen.modconfig()
    assert res
    assert res['id']
    assert res['full_name'] == 'klen/modconfig'


async def test_aiohttp():
    """FIXME: makes real requests to Github API."""
    from apiclient import APIClient
    from apiclient.backends import BackendAIOHTTP

    client = APIClient('https://api.github.com', backend=BackendAIOHTTP(timeout=10))

    with pytest.raises(client.Error):
        await client.api.users.klen.raise404()

    res = await client.api.repos.klen.modconfig(parse_response_body=False)
    assert res.status == 200

    res = await client.api.repos.klen.modconfig()
    assert res
    assert res['id']
    assert res['full_name'] == 'klen/modconfig'
