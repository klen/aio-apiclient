import unittest.mock as mock

import pytest


def test_descriptor():
    from apiclient.api import HTTPDescriptor

    request = mock.MagicMock()
    api = HTTPDescriptor(request)
    assert api
    assert api.users != api.users

    assert str(api) == "GET /"
    assert str(api.groups[1].users.post) == "POST /groups/1/users"
    assert str(api.users[1].post.post) == "POST /users/1/post"

    api.users[42].put(data={'login': 'updated'})
    request.assert_called_with('PUT', '/users/42', data={'login': 'updated'})

    api.users[42].put(method="POST", data={'login': 'updated'})
    request.assert_called_with('POST', '/users/42/put', data={'login': 'updated'})


def test_sync_initialization():
    from apiclient import APIClient
    from apiclient.backends import BackendAIOHTTP

    client = APIClient('https://api.github.com')
    assert client

    client = APIClient('https://api.github.com', backend=BackendAIOHTTP())
    assert client


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

    ts = 12345

    @client.middleware
    async def insert_timestamp(method, url, options):
        options.setdefault('headers', {})
        options['headers']['X-Timestamp'] = str(ts)
        return method, url, options

    res = await client.api.users.octocat.orgs()
    assert res
    backend.request.assert_awaited_with(
        'GET', 'https://api.github.com/users/octocat/orgs',
        raise_for_status=True, read_response_body=True, parse_response_body=True,
        headers={'Authorization': 'Bearer TOKEN', 'X-Timestamp': str(ts)}
    )


async def test_httpx():
    """FIXME: makes real requests to Github API."""
    from apiclient import APIClient
    from apiclient.backends import BackendHTTPX

    client = APIClient('https://api.github.com')
    assert isinstance(client.backend, BackendHTTPX)

    with pytest.raises(client.Error):
        await client.api.users.klen.raise404()

    res = await client.api.repos.klen['aio-apiclient'](
        raise_for_status=False, parse_response_body=False)
    assert res.status_code == 200

    res = await client.api.repos.klen['aio-apiclient']()
    assert res
    assert res['id'] == 278361832
    assert res['full_name'] == 'klen/aio-apiclient'

    await client.shutdown()


@pytest.mark.parametrize('aiolib', ['asyncio'])
async def test_aiohttp():
    """FIXME: makes real requests to Github API."""
    from apiclient import APIClient
    from apiclient.backends import BackendAIOHTTP

    client = APIClient('https://api.github.com', backend=BackendAIOHTTP(timeout=10))

    with pytest.raises(client.Error):
        await client.api.users.klen.raise404()

    res = await client.api.repos.klen['aio-apiclient'](parse_response_body=False)
    assert res.status == 200

    res = await client.api.repos.klen['aio-apiclient']()
    assert res
    assert res['id'] == 278361832
    assert res['full_name'] == 'klen/aio-apiclient'

    await client.shutdown()
