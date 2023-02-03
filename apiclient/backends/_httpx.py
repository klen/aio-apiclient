import sys
from typing import Optional, overload

import httpx

from apiclient.types import TResponseBody

from . import ABCBackend

# Python 3.7 compatibility
if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class BackendHTTPX(ABCBackend):
    """Support httpx."""

    name = "httpx"

    Error = httpx.HTTPError

    def __init__(
        self,
        client: Optional[httpx.AsyncClient] = None,
        uds: Optional[str] = None,
        **options
    ):
        """Initialize HTTPX Client."""
        if uds:
            options["transport"] = httpx.AsyncHTTPTransport(uds=uds)

        self.client = client or httpx.AsyncClient(**options)

    async def shutdown(self):
        """Shutdown the client."""
        await self.client.aclose()

    @overload
    async def request(
        self,
        method: str,
        url: str,
        *,
        read_response_body: Literal[True] = True,
        **options
    ) -> TResponseBody:
        ...

    @overload
    async def request(
        self, method: str, url: str, *, read_response_body: Literal[False], **options
    ) -> httpx.Response:
        ...

    async def request(
        self,
        method: str,
        url: str,
        *,
        raise_for_status: bool = True,
        read_response_body: bool = True,
        parse_response_body: bool = True,
        **options
    ):
        """Make a request."""
        client = self.client
        async with client.stream(method, url, **options) as response:
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
                    return self.parse_response(response, body)

            return response

    def parse_response(self, response: httpx.Response, body: bytes) -> TResponseBody:
        """Parse body for given response by content-type.

        :returns: parsed body
        """
        ct = response.headers.get("content-type", "")
        if ct.startswith("application/json"):
            return response.json()

        return body.decode(response.encoding or "utf-8")
