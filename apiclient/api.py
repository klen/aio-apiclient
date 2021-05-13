"""HTTP descriptor."""

from __future__ import annotations

import typing as t


class HTTPDescriptor:
    """Allows `desc.path.path.path.post(data)`."""

    __api_methods = 'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'

    def __init__(self, request: t.Callable, path_parts: t.List = None):
        """Initialization."""
        self.__request = request
        self.__path_parts = path_parts or []

    def __getitem__(self, piece: t.Any) -> HTTPDescriptor:
        """Clone self with new params."""
        return HTTPDescriptor(
            self.__request, self.__path_parts + [str(piece).strip('/')]
        )

    def __getattr__(self, piece: str) -> HTTPDescriptor:
        """Clone self with new params."""
        return self[piece]

    def __render__(self, method: str = None) -> t.Tuple[str, str]:
        """Compile HTTP URL and Method from current params."""
        url = "/"
        if (not method and self.__path_parts and
                self.__path_parts[-1].upper() in self.__api_methods):
            method = self.__path_parts.pop(-1)

        if self.__path_parts:
            url += "/".join(self.__path_parts)

        return (method or "GET").upper(), url

    def __str__(self):
        """String representation."""
        method, url = self.__render__()
        return f"{method} {url}"

    def __repr__(self):
        """Internal representation."""
        return f"URL: {self}"

    def __call__(self, method=None, **options):
        """Prepare a request."""
        method, url = self.__render__(method)

        return self.__request(method, url, **options)
