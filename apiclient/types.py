from collections.abc import Awaitable, Callable
from typing import Any, Protocol, TypeAlias, TypeVar

TResponse = TypeVar("TResponse")
TResponse_co = TypeVar("TResponse_co", covariant=True)

# Anything a backend may return after reading/parsing a response body
TResponseBody: TypeAlias = dict[str, Any] | list[Any] | str | int | float | bool | None
TMiddleware: TypeAlias = Callable[
    [str, str, dict[str, Any]], Awaitable[tuple[str, str, dict[str, Any]]]
]


class TRequestFn(Protocol[TResponse_co]):
    def __call__(self, method: str, url: str, **options: Any) -> Awaitable[TResponse_co]: ...
