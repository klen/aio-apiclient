"""APIClient Implementation."""

from __future__ import annotations

import copy
from collections.abc import Awaitable, Callable
from importlib.metadata import version
from typing import Any, Generic, TypeVar, cast
from urllib.parse import urlparse

from apiclient.api import HTTPDescriptor
from apiclient.backends import BACKENDS, ABCBackend
from apiclient.types import TMiddleware, TResponse

__version__: str = version("aio-apiclient")
__license__ = "MIT"

TVMiddleware = TypeVar("TVMiddleware", bound=TMiddleware)


class APIClient(Generic[TResponse]):
    """Work with any HTTP based API."""

    def __init__(
        self,
        root: str,
        *,
        # Backends
        backend_type: str | type[ABCBackend] | None = None,
        backend_options: dict[str, Any] | None = None,
        # Process responses
        raise_for_status: bool = True,
        read_response_body: bool = True,
        parse_response_body: bool = True,
        # Request params
        timeout: float = 10,
        uds: str | None = None,
        # Default params
        **defaults: Any,
    ) -> None:
        """Initialize the client.

        Any keyword not listed above is kept as a request default (headers, params, ...).
        """
        url = urlparse(root)
        if url.scheme == "uds":
            uds = url.path
            root = "http://socket"

        self.root: str = root.rstrip("/")
        self.raise_for_status: bool = raise_for_status
        self.read_response_body: bool = read_response_body
        self.parse_response_body: bool = parse_response_body
        self.defaults: dict[str, Any] = defaults
        if backend_type is None:
            if not BACKENDS:
                raise RuntimeError("Please install any apiclient supported backend (httpx|aiohttp)")
            backend_type, *_ = BACKENDS.values()

        elif isinstance(backend_type, str):
            if backend_type not in BACKENDS:
                raise RuntimeError(f"Backend {backend_type} is unknown or not installed")
            backend_type = BACKENDS[backend_type]

        self.backend: ABCBackend = backend_type(timeout=timeout, uds=uds, **(backend_options or {}))
        self.middlewares: list[TMiddleware] = []
        self.Error: type[Exception] = self.backend.Error

    def __repr__(self) -> str:
        """Represent the client."""
        return f"<APIClient {self.root}>"

    async def startup(self, *_: Any) -> None:
        """Startup the backend."""
        await self.backend.startup()

    async def shutdown(self, *_: Any) -> None:
        """Shutdown the backend."""
        await self.backend.shutdown()

    @property
    def api(self) -> HTTPDescriptor[TResponse]:
        """Create API Descriptor."""
        return HTTPDescriptor(self.request)

    def middleware(self, corofunc: TVMiddleware) -> TVMiddleware:
        """Register the given middleware. Can be used as a decorator.

        Middlewares run in registration order.
        """
        self.middlewares.append(corofunc)
        return corofunc

    async def request(self, method: str, url: str, **options: Any) -> TResponse:
        """Prepare and do HTTP request.

        Defaults are copied into the options, then middlewares run in registration order,
        then the backend sends the request.
        """
        # Process defaults
        for opt, val in self.defaults.items():
            if opt not in options:
                # Defaults are copied so a request or a middleware cannot change them
                options[opt] = copy.deepcopy(val) if isinstance(val, (dict, list)) else val
            elif isinstance(val, dict) and isinstance(options[opt], dict):
                options[opt] = dict(val, **options[opt])

        # Prepare URL
        if not url.startswith("http"):
            url = f"{self.root}/{url.lstrip('/')}"

        # Process middlewares
        for middleware in self.middlewares:
            method, url, options = await middleware(method, url, options)

        return await self.__request(method, url, **options)

    async def __request(  # noqa: PLR0913
        self,
        method: str,
        url: str,
        read_response_body: bool | None = None,
        raise_for_status: bool | None = None,
        parse_response_body: bool | None = None,
        **options: Any,
    ) -> TResponse:
        """Do HTTP request."""
        # shortcut: the backend overloads are keyed on literal flags, these are runtime values
        request = cast("Callable[..., Awaitable[Any]]", self.backend.request)
        response = await request(
            method,
            url,
            read_response_body=self.read_response_body
            if read_response_body is None
            else read_response_body,
            raise_for_status=self.raise_for_status
            if raise_for_status is None
            else raise_for_status,
            parse_response_body=self.parse_response_body
            if parse_response_body is None
            else parse_response_body,
            **options,
        )
        return cast("TResponse", response)
