Tools for utilizing the ANU Quantum Random Numbers Server
=========================================================

.. image:: https://github.com/lmacken/quantumrandom/actions/workflows/tests.yml/badge.svg?branch=develop
   :target: https://github.com/lmacken/quantumrandom/actions/workflows/tests.yml
.. image:: https://img.shields.io/pypi/v/quantumrandom.svg
   :target: https://pypi.org/project/quantumrandom/
.. image:: https://img.shields.io/pypi/dm/quantumrandom.svg
   :target: https://pypi.org/project/quantumrandom/

This project provides tools for interacting with The ANU Quantum Random
Number Generator (`quantumnumbers.anu.edu.au
<https://quantumnumbers.anu.edu.au>`_), which generates true random numbers in
real time by measuring the quantum fluctuations of the vacuum. It communicates
with their JSON API and provides a ``qrandom`` command-line tool and a Python
API, including a drop-in replacement for Python's own ``random.Random``.

quantumrandom works on Python 3.9 and newer, and has no dependencies.

.. note:: As of version 2.0, quantumrandom uses ANU's new API, which requires
   an API key. The ``qrng.anu.edu.au`` service that earlier versions talked to
   has been shut down, so those versions no longer work. There are a few
   other changes to be aware of when upgrading, which are listed in the
   `changelog
   <https://github.com/lmacken/quantumrandom/blob/develop/CHANGELOG.rst>`_.

Installing
----------

::

    pip install quantumrandom

Getting an API key
------------------

Sign up at `quantumnumbers.anu.edu.au <https://quantumnumbers.anu.edu.au>`_ to
create an API key. At the time of writing the free plan allows 100 requests
per month, at up to 1 request per second. A paid plan, billed per request
through the AWS Marketplace, has no monthly limit and allows 100 requests per
second. See their `pricing <https://quantumnumbers.anu.edu.au/pricing>`_ for
the details. quantumrandom works the same way with a key from any plan.

The easiest way to provide your key is with an environment variable, which
both the Python API and the ``qrandom`` command will pick up::

    export QUANTUMRANDOM_API_KEY=your-api-key

You can also set it from Python, which takes precedence over the environment::

    >>> import quantumrandom
    >>> quantumrandom.set_api_key('your-api-key')

Lastly, anything that makes API requests accepts an ``api_key`` argument, for
when you need to use more than one key.

Making the most of your requests
--------------------------------

ANU counts requests, not the amount of data that they return, and a single
request can return anything up to 20480 bytes. quantumrandom is designed
around this: it asks for as much as it can at a time, and keeps what you have
not used yet in memory so that it does not need to ask again until it runs
out. For example, rolling a die a thousand times with
``quantumrandom.randint(1, 6)`` costs one request, not a thousand.

Random data is only ever handed out once, and the buffered data lasts only as
long as your Python process does.

If a request is rate limited it is retried automatically, after a short
pause, up to ``quantumrandom.MAX_RETRIES`` (3) times.

Command-line tool
-----------------

::

    $ qrandom --int --min 5 --max 15
    7
    $ qrandom --int --min 1 --max 6 --count 5
    5
    6
    4
    4
    1
    $ qrandom --hex
    1dc59fde43b5045120453186d45653dd455bd8e6fc7d8c591f0018fa9261ab2835eb210e8
    e267cf35a54c02ce2a93b3ec448c4c7aa84fdedb61c7b0d87c9e7acf8e9fdadc8d68bcaa5a
    ...
    $ qrandom --binary > data
    $ ls -l data
    -rw-r--r-- 1 user user 20480 Nov 24 12:00 data

``--hex`` and ``--binary`` output one block of 20480 bytes, at the cost of one
API request. Use ``--count`` to ask for more than one block (or more than one
integer), or ``--count 0`` to keep going until interrupted::

    $ qrandom --binary --count 0 | dd of=data

.. warning:: ``--count 0`` makes one API request after another for as long as
   it runs. On the free plan that will use up your month's requests in a
   couple of minutes.

Run ``qrandom --help`` for the full list of options.

Python API
----------

The simplest way to get going is with ``quantumrandom.QuantumRandom``, which
is a subclass of `random.Random
<https://docs.python.org/3/library/random.html>`_ that gets its randomness
from the quantum random number generator. It supports everything that the
``random`` module does.

::

    >>> import quantumrandom
    >>> qr = quantumrandom.QuantumRandom()
    >>> qr.random()
    0.794368699495203
    >>> qr.randint(1, 6)
    4
    >>> qr.choice(['heads', 'tails'])
    'tails'
    >>> qr.sample(range(1, 50), 6)
    [12, 49, 36, 43, 31, 25]
    >>> deck = list(range(52))
    >>> qr.shuffle(deck)
    >>> qr.randbytes(16).hex()
    'e686697890ac68804bd8075067edd33d'

Just like ``random.SystemRandom``, it has no state to seed or save, so
sequences cannot be reproduced. Each instance keeps its own buffer of random
data, and can be given its own ``api_key``.

There is also a ``randint`` function at the top level, for convenience. It
draws from a buffer that is shared by the whole process.

::

    >>> quantumrandom.randint(0, 20)
    5

.. note:: As of version 2.0, ``randint(min, max)`` can return ``max``, just
   like ``random.randint`` does. Earlier versions never did.

The low-level ``get_data`` function is modelled after the ANU Quantum Random
Number Generator's JSON API. It makes one request, and returns a list of
``uint8`` or ``uint16`` integers, or ``hex8`` or ``hex16`` strings.

::

    >>> quantumrandom.get_data()
    [26646]
    >>> quantumrandom.get_data(data_type='uint16', array_length=5)
    [22546, 58383, 55100, 9936, 55159]
    >>> quantumrandom.get_data(data_type='hex8', array_length=3, block_size=2)
    ['8350', 'df68', 'ae1f']
    >>> quantumrandom.get_data(data_type='hex16', array_length=2, block_size=3)
    ['8ba57d8c7d1e', 'bc54a2eb5a07']

The ``array_length`` cannot be larger than ``1024``. The ``block_size`` only
applies to the hex data types, where it is the number of 8 or 16 bit values
in each string, and cannot be larger than ``10``.

Based on this ``get_data`` function, quantumrandom also provides a few
higher-level helper functions. Each of these makes one request when called.

::

    >>> quantumrandom.hex()[:10]
    '8272613343'
    >>> len(quantumrandom.binary())
    20480
    >>> quantumrandom.binary(array_length=8, block_size=1)
    b'\x07kE\xbb\x7f\xf8\x12\x83\xd5\xc6\xa2\xd17\x8e\x03\x17'
    >>> quantumrandom.uint16()
    array([24094, 13944, 22109, 22908, 34878, 33797, 47221, 21485, 37930, ...], dtype=uint16)

``uint16`` requires `NumPy <https://numpy.org>`_, which you can install along
with quantumrandom by running ``pip install quantumrandom[numpy]``.

``cached_generator`` returns a generator that yields numbers forever, making
a request for 1024 more each time it runs out. One can be passed to
``randint`` to have it take its numbers from there instead.

::

    >>> generator = quantumrandom.cached_generator()
    >>> next(generator)
    48013
    >>> quantumrandom.randint(1, 6, generator)
    2

Handling errors
---------------

Everything that can go wrong while talking to the API raises a subclass of
``quantumrandom.QuantumRandomError``:

* ``APIKeyError`` if no API key was found, or the API rejected it.
* ``QuotaExceededError`` if your API key has used up its requests.
* ``RateLimitError`` if a request was still being rate limited after being
  retried.
* ``QuantumRandomError`` itself for anything else, such as the API being
  unreachable, timing out (after ``quantumrandom.TIMEOUT`` seconds, 30 by
  default, or the ``timeout`` that you passed in), or returning something
  unexpected.

Invalid arguments raise a ``ValueError`` without making a request.

What happened to /dev/qrandom?
------------------------------

Earlier versions came with ``qrandom-dev``, which created a ``/dev/qrandom``
character device that could be used to feed the Linux entropy pool. It was
removed in version 2.0. The library that it was built upon (cusepy) only ever
supported Python 2 and is no longer available, and a device that makes API
requests in the background for as long as something reads from it is a poor
fit for an API that is metered by the request. If all you need is a stream of
bytes, ``qrandom --binary`` can be piped into whatever needs it.

Development
-----------

::

    pip install -e .[test,numpy]
    pytest

The tests do not use the network or need an API key. One additional test
makes a single request to the real API, and only runs if you ask it to::

    QUANTUMRANDOM_LIVE_TEST=1 QUANTUMRANDOM_API_KEY=your-api-key pytest tests/test_live.py

Releasing
---------

1. Update ``VERSION`` in ``quantumrandom/__init__.py``, and add the release to
   ``CHANGELOG.rst``.
2. Commit, tag, and push the release. Pushing a tag that starts with a digit
   runs ``.github/workflows/publish.yml``, which builds the distributions and
   publishes them to PyPI::

       git tag -a 2.0.0 -m "quantumrandom 2.0.0"
       git push origin develop 2.0.0

The workflow publishes through PyPI's `trusted publishing
<https://docs.pypi.org/trusted-publishers/>`_, so there is no API token to
manage. PyPI trusts the ``publish.yml`` workflow in the
``lmacken/quantumrandom`` repository, running in its ``pypi`` environment, and
each file that it uploads comes with an attestation of where it was built.

The **Publish** workflow can also be run manually to publish to TestPyPI,
which has its own trusted publishers, and expects the ``testpypi``
environment.
