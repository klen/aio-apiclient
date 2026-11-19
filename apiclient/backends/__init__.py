"""Base abstract backend class."""

from __future__ import annotations

import abc
from contextlib import suppress
from typing import TYPE_CHECKING, Any, ClassVar, Literal, overload

if TYPE_CHECKING:
    from apiclient.types import TResponseBody


class ABCBackend(abc.ABC):
    """Base class for backends."""

    name: ClassVar[str]
    Error: type[Exception] = Exception

    @abc.abstractmethod
    def __init__(self, client: Any = None, timeout: float | None = None, **_: Any) -> None:
        """Initialize the backend."""

    def __init_subclass__(cls, *args: Any, **kwargs: Any) -> None:
        """Register a backend."""
        super().__init_subclass__(*args, **kwargs)
        BACKENDS[cls.name] = cls

    async def startup(self) -> None:  # noqa: B027
        """Prepare the backend."""

    async def shutdown(self) -> None:  # noqa: B027
        """Close the backend."""

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
    ) -> Any: ...

    @overload
    async def request(
        self,
        method: str,
        url: str,
        *,
        read_response_body: Literal[False],
        parse_response_body: bool = True,
        **options: Any,
    ) -> Any: ...

    @abc.abstractmethod
    async def request(
        self,
        method: str,
        url: str,
        *,
        read_response_body: bool = True,
        raise_for_status: bool = True,
        parse_response_body: bool = True,
        **options: Any,
    ) -> Any:
        """Do http request with the backend.

        A response returned with ``read_response_body=False`` is already closed:
        its body cannot be read.
        """


BACKENDS: dict[str, type[ABCBackend]] = {}

with suppress(ImportError):
    from ._httpx import BackendHTTPX

with suppress(ImportError):
    from ._aiohttp import BackendAIOHTTP

# ruff: noqa: F401
