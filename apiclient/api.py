class APIDescriptor:

    __api_methods = 'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD'

    def __init__(self, request, path=None):
        self.__request = request
        self.__path = path or []

    def __getitem__(self, piece):
        return APIDescriptor(
            self.__request, self.__path + [str(piece).strip('/')]
        )

    def __getattr__(self, piece):
        return self[piece]

    def __endpoint__(self, method=None):
        url = "/"
        if not method and self.__path and self.__path[-1].upper() in self.__api_methods:
            method = self.__path.pop(-1)

        if self.__path:
            url += "/".join(self.__path)

        return (method or "GET").upper(), url

    def __str__(self):
        """String representation."""
        method, url = self.__endpoint__()
        return "%s %s" % (method, url)

    def __repr__(self):
        """Internal representation."""
        return 'URL: %s' % self

    def __call__(self, method=None, **options):
        """Prepare a request."""
        method, url = self.__endpoint__(method)

        return self.__request(method, url, **options)
