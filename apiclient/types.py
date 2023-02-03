import sys
from typing import Any, Awaitable, Callable, Dict, List, Tuple, Union

# Python 3.7 compatibility
if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

TResponseBody = Union[str, Dict, List, int, float, bool, None]
TMiddleware = Callable[[str, str, Dict], Awaitable[Tuple[str, str, Dict]]]


class TRequestFn(Protocol):
    def __call__(self, method: str, url: str, **options: Any) -> Awaitable:
        ...
