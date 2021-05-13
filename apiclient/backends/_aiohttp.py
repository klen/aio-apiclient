import aiohttp

from . import ABCBackend


class BackendAIOHTTP(ABCBackend):
    """Support aiohttp."""

    Error = aiohttp.client_exceptions.ClientError

    def __init__(self, client: aiohttp.ClientSession = None, timeout: int = None, **options):
        """Initialize the client."""
        if timeout:
            options['timeout'] = aiohttp.ClientTimeout(total=timeout)

        self._client = client
        self._options = options

    @property
    def client(self):
        """Deferred client initialization."""
        if self._client is None:
            self._client = aiohttp.ClientSession(**self._options)
        return self._client

    async def shutdown(self):
        """Close the client."""
        return await self.client.close()

    async def request(self, method: str, url: str, *, raise_for_status: bool = True,
                      read_response_body: bool = True, parse_response_body: bool = True,
                      **options):
        """Make a request."""
        async with self.client.request(method, url, **options) as response:

            if raise_for_status:
                response.raise_for_status()

            if read_response_body:
                if parse_response_body:
                    response = await self.parse_response(response)

            else:
                response.close()

            return response

    def parse_response(cls, response):
        """Parse body for given response by content-type.

        :returns: a coroutine
        """
        ct = response.headers.get('content-type', '')
        if ct.startswith('application/json'):
            try:
                return response.json()
            except ValueError:
                return response.text()

        if ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart'):
            return response.post()

        return response.text()
