"""Base abstract backend class."""
import typing as t

import abc


class ABCBackend(abc.ABC):
    """Base class for backends."""

    def __init__(self, client: t.Any = None, timeout: int = None, **client_options):
        """Initialize the backend."""
        pass

    def __init_subclass__(cls, *args, **kwargs):
        """Register a backend."""
        super().__init_subclass__(*args, **kwargs)
        BACKENDS.append(cls)

    class Error(Exception):
        """Client exception."""

        pass

    async def startup(self):
        """Prepare the backend."""
        pass

    async def shutdown(self):
        """Close the backend."""
        pass

    @abc.abstractmethod
    async def request(self, method: str, url: str, *, raise_for_status: bool = True,
                      read_response_body: bool = True, parse_response_body: bool = True,
                      **options):
        """Do http request with the backend."""
        pass


BACKENDS: t.List[t.Type[ABCBackend]] = []


try:
    from ._httpx import BackendHTTPX

except ImportError:
    pass

try:
    from ._aiohttp import BackendAIOHTTP

except ImportError:
    pass

# pylama: ignore=W0611
