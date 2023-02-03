"""Base abstract backend class."""
import abc
import sys
from contextlib import suppress
from typing import Any, Dict, Optional, Type, overload

from apiclient.types import TResponseBody

# Python 3.7 compatibility
if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class ABCBackend(abc.ABC):
    """Base class for backends."""

    @property
    @abc.abstractmethod
    def name(self):
        """Backend should have a name."""

    def __init__(self, client: Any = None, timeout: Optional[int] = None, **_):
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
    ) -> Any:
        ...

    @abc.abstractmethod
    async def request(
        self,
        method: str,
        url: str,
        *,
        read_response_body: bool = True,
        raise_for_status: bool = True,
        parse_response_body: bool = True,
        **options
    ):
        """Do http request with the backend."""


BACKENDS: Dict[str, Type[ABCBackend]] = {}


with suppress(ImportError):
    from ._httpx import BackendHTTPX

with suppress(ImportError):
    from ._aiohttp import BackendAIOHTTP

# pylama: ignore=W0611
