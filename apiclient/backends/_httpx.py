import httpx
import typing as t

from . import ABCBackend


class BackendHTTPX(ABCBackend):
    """Support httpx."""

    name = 'httpx'

    Error = httpx.HTTPError

    def __init__(self, client: httpx.AsyncClient = None, **options):
        """Initialize HTTPX Client."""
        self.client = client or httpx.AsyncClient(**options)

    async def shutdown(self):
        """Shutdown the client."""
        await self.client.aclose()

    async def request(self, method: str, url: str, *, raise_for_status: bool = True,
                      read_response_body: bool = True, parse_response_body: bool = True,
                      **options) -> httpx.Response:
        """Make a request."""
        async with self.client.stream(method, url, **options) as response:

            if raise_for_status:
                try:
                    response.raise_for_status()
                except self.Error:
                    if read_response_body:
                        await response.aread()

                    raise

            if read_response_body:
                body = await response.aread()
                if parse_response_body:
                    response = self.parse_response(response, body)

            return response

    def parse_response(self, response: httpx.Response, body: t.Any) -> t.Any:
        """Parse body for given response by content-type.

        :returns: parsed body
        """
        ct = response.headers.get('content-type', '')
        if ct.startswith('application/json'):
            return response.json()

        return body.decode(response.encoding)
