from typing import Any, Awaitable, Callable, Dict, List, Protocol, Tuple, TypedDict, Union

TResponseBody = Union[str, Dict, List, int, float, bool, None]
TMiddleware = Callable[[str, str, Dict], Awaitable[Tuple[str, str, Dict]]]
TRequestOptions = TypedDict(
    "TRequestOptions",
    {"raise_for_status": bool, "read_response_body": bool, "parse_response_body": bool},
    total=False,
)


class TRequestFn(Protocol):
    def __call__(self, method: str, url: str, **options: Any) -> Awaitable:
        ...
