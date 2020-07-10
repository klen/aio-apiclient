import copy
import inspect
import logging

from .api import APIDescriptor
from .backends import BACKENDS


__version__ = "0.0.7"
__license__ = "MIT"


logger = logging.getLogger('apiclient')


class APIClient:

    def __init__(
            self, root, raise_for_status=True, read_response_body=True,
            parse_response_body=True, timeout=10, backend=None, **defaults):
        self.root = root.rstrip('/')
        self.middlewares = []
        self.raise_for_status = raise_for_status
        self.read_response_body = read_response_body
        self.parse_response_body = parse_response_body
        self.defaults = defaults
        self.backend = backend or (BACKENDS and BACKENDS[0](timeout=timeout))
        if not self.backend:
            raise RuntimeError('httpx or aiohttp must be installed to use aio-apiclient')

    def startup(self):
        return self.backend.startup()

    def shutdown(self):
        return self.backend.shutdown()

    @property
    def api(self):
        """Create API Descriptor."""
        return APIDescriptor(self.request)

    @property
    def Error(self):
        """Create API Descriptor."""
        return self.backend.Error

    def middleware(self, corofunc):
        """Register the given middleware."""
        if not inspect.iscoroutinefunction(corofunc):
            raise ValueError('Middleware "%s" must be a coroutine function.' % corofunc.__name__)

        self.middlewares.insert(0, corofunc)
        return corofunc

    async def request(self, method, url, **options):
        """Do HTTP request."""

        # Process defaults
        for opt, val in self.defaults.items():
            if opt not in options:
                options[opt] = copy.copy(val)
            elif isinstance(val, dict):
                options[opt] = dict(self.defaults[opt], **options[opt])

        # Prepare URL
        if not url.startswith('http'):
            url = "%s/%s" % (self.root, url.lstrip('/'))

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
