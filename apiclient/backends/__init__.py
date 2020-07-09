class ABCBackend:

    class Error(Exception):
        pass

    async def startup(self):
        pass

    async def shutdown(self):
        pass

    async def request(self, method, url, *,
                      raise_for_status=True, read_response_body=True, parse_response_body=True,
                      **options):
        pass


BACKENDS = []

try:
    from ._httpx import BackendHTTPX

    BACKENDS.append(BackendHTTPX)

except ImportError:
    pass

try:
    from ._aiohttp import BackendAIOHTTP

    BACKENDS.append(BackendAIOHTTP)

except ImportError:
    pass
