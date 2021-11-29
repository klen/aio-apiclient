"""Base abstract backend class."""
import abc
import typing as t


class ABCBackend(abc.ABC):
    """Base class for backends."""

    @property
    @abc.abstractmethod
    def name(self):
        """Backend should have a name."""

    def __init__(self, client: t.Any = None, timeout: int = None, **_):
        """Initialize the backend."""

    def __init_subclass__(cls, *args, **kwargs):
        """Register a backend."""
        super().__init_subclass__(*args, **kwargs)
        BACKENDS[str(cls.name)] = cls

    class Error(Exception):
        """Client exception."""

    async def startup(self):
        """Prepare the backend."""

    async def shutdown(self):
        """Close the backend."""

    @abc.abstractmethod
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
        """Do http request with the backend."""


BACKENDS: t.Dict[str, t.Type[ABCBackend]] = {}


try:
    from ._httpx import BackendHTTPX
    assert BackendHTTPX

except ImportError:
    pass

try:
    from ._aiohttp import BackendAIOHTTP
    assert BackendAIOHTTP

except ImportError:
    pass

# pylama: ignore=W0611
