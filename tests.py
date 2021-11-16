
import httpx
import pytest

# Support Python < 3.8
try:
    import mock  # type: ignore
except ImportError:
    import unittest.mock as mock  # type: ignore


@pytest.fixture
def mock_httpx():
    with mock.patch('httpx.AsyncClient.send') as mocked:
        mocked.return_value = httpx.Response(200, request=httpx.Request('GET', '/'), text='httpx')
        yield mocked


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

    api.users[42].post({'test': 'ok'})
    request.assert_called_with('POST', '/users/42', data={'test': 'ok'})

    api.users[42]['/custom/path']()
    request.assert_called_with('GET', '/users/42/custom/path')


def test_no_backends_installed(monkeypatch):
    import apiclient

    monkeypatch.setattr(apiclient, 'BACKENDS', [])
    with pytest.raises(RuntimeError):
        apiclient.APIClient('https://api.github.com')


def test_sync_initialization():
    from apiclient import APIClient
    from apiclient.backends import BackendAIOHTTP, BackendHTTPX

    client = APIClient('https://api.github.com')
    assert isinstance(client.backend, BackendHTTPX)

    client = APIClient('https://api.github.com', backend_type='httpx')
    assert isinstance(client.backend, BackendHTTPX)

    client = APIClient('https://api.github.com', backend_type=BackendAIOHTTP)
    assert client
    assert isinstance(client.backend, BackendAIOHTTP)


async def test_client():
    from apiclient import APIClient

    backend = mock.AsyncMock()

    client = APIClient('https://api.github.com', headers={
        'Authorization': 'Bearer TOKEN'
    })
    assert client
    assert client.api
    assert client.defaults
    assert client.Error

    client.backend = backend

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
    assert res.json()

    res = await client.api.repos.klen['aio-apiclient']()
    assert res
    assert res['id'] == 278361832
    assert res['full_name'] == 'klen/aio-apiclient'

    await client.shutdown()


async def test_uds_httpx(mock_httpx):
    from apiclient import APIClient

    client = APIClient('uds:///var/run/docker.sock')
    res = await client.api.containers.json()
    assert res


@pytest.mark.parametrize('aiolib', ['asyncio'])
async def test_aiohttp():
    """FIXME: makes real requests to Github API."""
    from apiclient import APIClient
    from apiclient.backends import BackendAIOHTTP

    client = APIClient('https://api.github.com', backend_type=BackendAIOHTTP)

    with pytest.raises(client.Error):
        await client.api.users.klen.raise404()

    res = await client.api.repos.klen['aio-apiclient'](parse_response_body=False)
    assert res.status == 200

    res = await client.api.repos.klen['aio-apiclient']()
    assert res
    assert res['id'] == 278361832
    assert res['full_name'] == 'klen/aio-apiclient'

    await client.shutdown()
