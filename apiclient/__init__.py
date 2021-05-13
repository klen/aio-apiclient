"""APIClient Implementation."""

import typing as t
import copy
import inspect
import logging

from .api import HTTPDescriptor
from .backends import BACKENDS, ABCBackend


__version__ = "0.1.0"
__license__ = "MIT"


logger = logging.getLogger('apiclient')


class APIClient:
    """Work with any HTTP based API."""

    def __init__(
            self, root: str, *, raise_for_status: bool = True, read_response_body: bool = True,
            parse_response_body: bool = True, timeout: int = 10, backend: ABCBackend = None,
            **defaults):
        """Initialize the client."""
        self.root = root.rstrip('/')
        self.raise_for_status = raise_for_status
        self.read_response_body = read_response_body
        self.parse_response_body = parse_response_body
        self.defaults = defaults
        if backend is None:
            backend = BACKENDS[0](timeout=timeout)
        self.backend = backend
        self.middlewares: t.List[t.Callable[..., t.Awaitable]] = []
        if not self.backend:
            raise RuntimeError('httpx or aiohttp must be installed to use aio-apiclient')

    async def startup(self):
        """Startup the backend."""
        await self.backend.startup()

    async def shutdown(self):
        """Shutdown the backend."""
        await self.backend.shutdown()

    @property
    def api(self) -> HTTPDescriptor:
        """Create API Descriptor."""
        return HTTPDescriptor(self.request)

    @property
    def Error(self) -> t.Type[Exception]:
        """Create API Descriptor."""
        return self.backend.Error

    def middleware(self, corofunc: t.Callable[..., t.Awaitable]):
        """Register the given middleware. Can be used as a decorator."""
        if not inspect.iscoroutinefunction(corofunc):
            raise ValueError('Middleware "%s" must be a coroutine function.' % corofunc.__name__)

        self.middlewares.insert(0, corofunc)
        return corofunc

    async def request(self, method: str, url: str, **options):
        """Do HTTP request."""
        # Process defaults
        for opt, val in self.defaults.items():
            if opt not in options:
                options[opt] = copy.copy(val)
            elif isinstance(val, dict):
                options[opt] = dict(self.defaults[opt], **options[opt])

        # Prepare URL
        if not url.startswith('http'):
            url = f"{self.root}/{url.lstrip('/')}"

        # Process middlewares
        for middleware in self.middlewares:
            method, url, options = await middleware(method, url, options)

        res = await self.backend.request(
            method, url,
            raise_for_status=options.pop('raise_for_status', self.raise_for_status),
            read_response_body=options.pop('read_response_body', self.read_response_body),
            parse_response_body=options.pop('parse_response_body', self.parse_response_body),
            **options)

        return res
