import aiohttp

from . import ABCBackend


class BackendAIOHTTP(ABCBackend):

    Error = aiohttp.client_exceptions.ClientError

    def __init__(self, session=None, timeout=None, **options):
        if timeout:
            timeout = aiohttp.ClientTimeout(total=timeout)

        self.session = session or aiohttp.ClientSession(**options)

    def shutdown(self):
        return self.session.close()

    async def request(self, method, url, *,
                      raise_for_status=True, read_response_body=True, parse_response_body=True,
                      **options):

        async with self.session.request(method, url, **options) as response:

            if raise_for_status:
                response.raise_for_status()

            if read_response_body:
                if parse_response_body:
                    response = await self.parse_response(response)

            else:
                response.close()

            return response

    def parse_response(cls, response):
        """Parse body for given response by content-type.

        :returns: a coroutine
        """
        ct = response.headers.get('content-type', '')
        if ct.startswith('application/json'):
            try:
                return response.json()
            except ValueError:
                return response.text()

        if ct.startswith('multipart'):
            return response.post()

        return response.text()
