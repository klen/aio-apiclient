aio-apiclient
#############

.. _description:

aio-apiclient -- Async helper to work with HTTP APIs

.. _badges:

.. image:: https://github.com/klen/aio-apiclient/workflows/tests/badge.svg
    :target: https://github.com/klen/aio-apiclient/actions
    :alt: Tests Status

.. image:: https://img.shields.io/pypi/v/aio-apiclient
    :target: https://pypi.org/project/aio-apiclient/
    :alt: PYPI Version

.. _features:

Features
========

- Convenient work with any HTTP API (especially with REST)
- Supports `httpx` and `aiohttp` as backends to make requests
- Very configurable and usable
- An ability to parse responses automatically

.. _contents:

.. contents::

.. _requirements:

Requirements
=============

- python >= 3.7

.. _installation:

Installation
=============

**aio-apiclient** should be installed using pip: ::

    pip install aio-apiclient

.. _usage:

QuickStart
==========

Github API (https://developer.github.com/v4/):

.. code:: python

    from apiclient import APIClient

    client = APIClient('https://api.github.com', headers={
            'Authorization': 'token OAUTH-TOKEN'
    })

    # Read information about the current repository
    repo = await client.api.repos.klen['aio-apiclient'].get()
    print(repo)  # dict parsed from Github Response JSON


Slack API (https://api.slack.com/web):

.. code:: python

    from apiclient import APIClient

    client = APIClient('https://api.github.com', headers={
        'Authorization': 'token OAUTH-TOKEN'
    })

    # Update current user status (we don't care about this response)
    await client.api['users.profile.set'].post(json={
        'profile': {
            'status_text': 'working',
            'status_emoji': ':computer:'
            'status_expiration': 30,
        }
    }, read_response_body=False)


And etc

Usage
=====

Initialization
--------------

The Client initialization requires root URL for a required API.

.. code:: python

    from apiclient import APIClient

    client = APIClient(

        # Root URL for any API (required)
        'https://api.github.com',

        # Raise `client.Error` for any response with status code > 400
        raise_for_status=True,

        # Set to `False` if you only want to make a request and doesn't care about responses
        read_response_body=True,

        # Parse response's body content-type and return JSON/TEXT/Form data instead the response itself

        # Set total timeout in seconds
        timeout=10.0,

        # Set backend type for making requests (apiclient.backends.BackendHTTPX,
        # apiclient.backends.BackendAIOHTTP) by default first available would be
        # choosen

        backend_type=None,

        # Default backend options to use with every request (headers, params, data, ...)
        # ...

    )

App Shutdown
------------

The api client support graceful shutdown. Run `await client.shutdown()` when
you are finishing your app (not necessary).


Middlewares
-----------

You are able to dinamically change request params (method, url, other backend params) using middlewares.

.. code:: python

    import time
    from apiclient import APIClient

    client = APIClient('https://api.github.com')

    @client.middleware
    async def insert_timestamp_header(method, url, options):
        options.setdefault('headers', {})
        options['headers']['X-Timestamp'] = str(time.time())
        return method, url, options


.. _bugtracker:

Bug tracker
===========

If you have any suggestions, bug reports or
annoyances please report them to the issue tracker
at https://github.com/klen/aio-apiclient/issues

.. _contributing:

Contributing
============

Development of the project happens at: https://github.com/klen/aio-apiclient

.. _license:

License
========

Licensed under a `MIT license`_.


.. _links:


.. _klen: https://github.com/klen

.. _MIT license: http://opensource.org/licenses/MIT

