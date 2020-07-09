aio-apiclient
#############

.. _description:

aio-apiclient -- Simple Asyncio Client for any HTTP APIs

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

- Convenient work with any HTTP API
- Supports `httpx` and `aiohttp` as backends to make requests
- Very configurable

.. _contents:

.. contents::

.. _requirements:

Requirements
=============

- python >= 3.4

.. _installation:

Installation
=============

**aio-apiclient** should be installed using pip: ::

    pip install aio-apiclient

.. _usage:

QuickStart
==========

Github API (https://developer.github.com/v4/):

.. _code: python

    from apiclient import APIClient

    client = APIClient('https://api.github.com', headers={
            'Authorization': 'token OAUTH-TOKEN'
    })

    # Read information about the current repository
    repo = await client.api.repos.klen['aio-apiclient'].get()
    print repo


Slack API (https://api.slack.com/web):

.. _code: python

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

