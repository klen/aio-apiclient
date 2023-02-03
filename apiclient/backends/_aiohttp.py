import sys
from contextlib import suppress
from typing import Optional, overload

import aiohttp

from ..types import TResponseBody
from . import ABCBackend

# Python 3.7 compatibility
if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class BackendAIOHTTP(ABCBackend):
    """Support aiohttp."""

    name = "aiohttp"

    Error = aiohttp.client_exceptions.ClientError

    def __init__(
        self,
        client: Optional[aiohttp.ClientSession] = None,
        timeout: Optional[int] = None,
        uds: Optional[str] = None,
        **options
    ):
        """Initialize the client."""
        if timeout:
            options["timeout"] = aiohttp.ClientTimeout(total=timeout)

        if uds:
            options["connector"] = aiohttp.UnixConnector(path=uds)

        self._client = client
        self._options = options

    @property
    def client(self) -> aiohttp.ClientSession:
        """Deferred client initialization."""
        if self._client is None:
            self._client = aiohttp.ClientSession(**self._options)
        return self._client

    async def shutdown(self):
        """Close the client."""
        await self.client.close()

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
    ) -> aiohttp.ClientResponse:
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
        async with self.client.request(method, url, **options) as response:

            if raise_for_status:
                response.raise_for_status()

            if read_response_body:
                if parse_response_body:
                    return await self.parse_response(response)

            else:
                response.close()

            return response

    async def parse_response(cls, response: aiohttp.ClientResponse) -> TResponseBody:
        """Parse body for given response by content-type.

        :returns: a coroutine
        """
        ct = response.headers.get("content-type", "")
        if ct.startswith("application/json"):
            with suppress(ValueError):
                return await response.json()

        return await response.text()
