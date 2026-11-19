"""HTTP descriptor."""

from collections.abc import Awaitable
from typing import Any, ClassVar, Generic, Self

from apiclient.types import TRequestFn, TResponse


class HTTPDescriptor(Generic[TResponse]):
    """Allows `desc.path.path.path.post(data)`.

    Every attribute and every ``[piece]`` adds one URL segment; the last segment is the
    HTTP method when it names one and no method is given. Rendering the descriptor never
    changes it.
    """

    __api_methods: ClassVar[tuple[str, ...]] = (
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "HEAD",
        "OPTIONS",
    )

    def __init__(self, request: TRequestFn[TResponse], path_parts: list[str] | None = None) -> None:
        """Initialization."""
        self.__request: TRequestFn[TResponse] = request
        self.__path_parts: list[str] = path_parts or []

    def __getitem__(self, piece: Any) -> Self:
        """Clone self with new params."""
        return type(self)(self.__request, [*self.__path_parts, str(piece).strip("/")])

    def __getattr__(self, piece: str) -> Self:
        """Clone self with new params."""
        if piece.startswith("__"):
            raise AttributeError(piece)
        return self[piece]

    def __render__(self, method: str | None = None) -> tuple[str, str]:
        """Compile HTTP URL and Method from current params."""
        parts = self.__path_parts
        if not method and parts and parts[-1].upper() in self.__api_methods:
            # No mutation: str()/repr() and repeated calls must not change the request
            method, parts = parts[-1], parts[:-1]

        return (method or "GET").upper(), "/" + "/".join(parts)

    def __str__(self) -> str:
        """String representation."""
        method, url = self.__render__()
        return f"{method} {url}"

    def __repr__(self) -> str:
        """Internal representation."""
        return f"URL: {self}"

    def __call__(
        self, body: Any = None, *, method: str | None = None, **options: Any
    ) -> Awaitable[TResponse]:
        """Prepare a request.

        A positional ``body`` is sent as ``data``; other keywords go to the backend as is.
        """
        method, url = self.__render__(method)

        if body is not None:
            options.setdefault("data", body)

        return self.__request(method, url, **options)
