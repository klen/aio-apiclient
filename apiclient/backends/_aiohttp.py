from contextlib import suppress
from typing import Any, Literal, overload

import aiohttp
from aiohttp.client_exceptions import ClientError

from apiclient.types import TResponseBody

from . import ABCBackend


class BackendAIOHTTP(ABCBackend):
    """Support aiohttp."""

    name = "aiohttp"

    Error = ClientError

    def __init__(
        self,
        client: aiohttp.ClientSession | None = None,
        timeout: float | None = None,
        uds: str | None = None,
        **options: Any,
    ) -> None:
        """Initialize the client."""
        if timeout:
            options["timeout"] = aiohttp.ClientTimeout(total=timeout)

        if uds:
            options["connector"] = aiohttp.UnixConnector(path=uds)

        self._client: aiohttp.ClientSession | None = client
        self._options: dict[str, Any] = options

    @property
    def client(self) -> aiohttp.ClientSession:
        """Deferred client initialization."""
        if self._client is None:
            self._client = aiohttp.ClientSession(**self._options)
        return self._client

    async def startup(self) -> None:
        """Create the session inside the running event loop."""
        _ = self.client

    async def shutdown(self) -> None:
        """Close the client."""
        await self.client.close()

    @overload
    async def request(
        self,
        method: str,
        url: str,
        *,
        read_response_body: Literal[True] = True,
        parse_response_body: Literal[True] = True,
        **options: Any,
    ) -> TResponseBody: ...

    @overload
    async def request(
        self,
        method: str,
        url: str,
        *,
        read_response_body: Literal[True] = True,
        parse_response_body: Literal[False],
        **options: Any,
    ) -> aiohttp.ClientResponse: ...

    @overload
    async def request(
        self,
        method: str,
        url: str,
        *,
        read_response_body: Literal[False],
        parse_response_body: bool = True,
        **options: Any,
    ) -> aiohttp.ClientResponse: ...

    async def request(
        self,
        method: str,
        url: str,
        *,
        raise_for_status: bool = True,
        read_response_body: bool = True,
        parse_response_body: bool = True,
        **options: Any,
    ) -> TResponseBody | aiohttp.ClientResponse:
        """Make a request.

        The response returned with ``read_response_body=False`` is already closed,
        so its body cannot be read.
        """
        async with self.client.request(method, url, **options) as response:
            if raise_for_status:
                response.raise_for_status()

            if read_response_body:
                if parse_response_body:
                    return await self.parse_response(response)

                # Keep the body readable on the returned response, like the httpx backend does
                await response.read()

            else:
                response.close()

            return response

    async def parse_response(self, response: aiohttp.ClientResponse) -> TResponseBody:
        """Parse body for given response by content-type.

        :returns: a coroutine
        """
        ct = response.headers.get("content-type", "")
        if ct.startswith("application/json"):
            with suppress(ValueError):
                return await response.json()

        return await response.text()
