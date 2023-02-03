"""APIClient Implementation."""

import copy
from typing import Dict, List, Optional, Type, TypeVar, Union
from urllib.parse import urlparse

from apiclient.api import HTTPDescriptor
from apiclient.backends import BACKENDS, ABCBackend
from apiclient.types import TMiddleware

__version__ = "1.7.0"
__license__ = "MIT"

TVMiddleware = TypeVar("TVMiddleware", bound=TMiddleware)


class APIClient:
    """Work with any HTTP based API."""

    def __init__(
        self,
        root: str,
        *,
        # Backends
        backend_type: Optional[Union[str, Type[ABCBackend]]] = None,
        backend_options: Optional[Dict] = None,
        # Process responses
        raise_for_status: bool = True,
        read_response_body: bool = True,
        parse_response_body: bool = True,
        # Request params
        timeout: int = 10,
        uds: Optional[str] = None,
        # Default params
        **defaults,
    ):
        """Initialize the client."""
        url = urlparse(root)
        if url.scheme == "uds":
            uds = url.path
            root = "http://socket"

        self.root = root.rstrip("/")
        self.raise_for_status = raise_for_status
        self.read_response_body = read_response_body
        self.parse_response_body = parse_response_body
        self.defaults = defaults
        if backend_type is None:
            if not BACKENDS:
                raise RuntimeError(
                    "Please install any apiclient supported backend (httpx|aiohttp)"
                )
            backend_type, *_ = BACKENDS.values()

        elif isinstance(backend_type, str):
            backend_type = BACKENDS[backend_type]

        self.backend = backend_type(timeout=timeout, uds=uds, **(backend_options or {}))
        self.middlewares: List[TMiddleware] = []
        if not self.backend:
            raise RuntimeError(
                "httpx or aiohttp must be installed to use aio-apiclient"
            )

    def __repr__(self) -> str:
        """Represent the client."""
        return f"<APIClient {self.root}>"

    async def startup(self, *_):
        """Startup the backend."""
        await self.backend.startup()

    async def shutdown(self, *_):
        """Shutdown the backend."""
        await self.backend.shutdown()

    @property
    def api(self) -> HTTPDescriptor:
        """Create API Descriptor."""
        return HTTPDescriptor(self.request)

    @property
    def Error(self) -> Type[Exception]:
        """Create API Descriptor."""
        return self.backend.Error

    def middleware(self, corofunc: TVMiddleware) -> TVMiddleware:
        """Register the given middleware. Can be used as a decorator."""
        self.middlewares.insert(0, corofunc)
        return corofunc

    async def request(self, method: str, url: str, **options):
        """Prepare and do HTTP request."""
        # Process defaults
        for opt, val in self.defaults.items():
            if opt not in options:
                options[opt] = copy.copy(val)
            elif isinstance(val, dict):
                options[opt] = dict(self.defaults[opt], **options[opt])

        # Prepare URL
        if not url.startswith("http"):
            url = f"{self.root}/{url.lstrip('/')}"

        # Process middlewares
        for middleware in self.middlewares:
            method, url, options = await middleware(method, url, options)

        return await self.__request(method, url, **options)

    async def __request(
        self,
        method: str,
        url: str,
        read_response_body: Optional[bool] = None,
        raise_for_status: Optional[bool] = None,
        parse_response_body: Optional[bool] = None,
        **options,
    ):
        """Do HTTP request."""
        return await self.backend.request(  # type: ignore
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
