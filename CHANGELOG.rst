Changelog
=========

2.0.0 (2026-11-24)
------------------

The ``qrng.anu.edu.au`` service that every earlier release talked to has been
shut down, which means that those releases no longer work. This release moves
to its replacement, `ANU Quantum Numbers <https://quantumnumbers.anu.edu.au>`_.

Things to know when upgrading
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **An API key is now required.** Create one at
  https://quantumnumbers.anu.edu.au and provide it with the
  ``QUANTUMRANDOM_API_KEY`` environment variable, ``set_api_key()``, or the
  new ``api_key`` argument. Requests are metered: the free plan currently
  allows 100 a month.
* **Python 3.9 or newer is required.** Support for Python 2 is gone, and
  ``six`` is no longer a dependency.
* **randint(min, max) can now return max**, to match ``random.randint``.
  Before, ``randint(0, 1)`` could only ever return 0.
  (`#25 <https://github.com/lmacken/quantumrandom/pull/25>`_ by
  Brian Ó Donnell)
* ``randint`` returns an ``int`` again. On Python 3 it was returning a
  ``float``, which also made its results very slightly uneven once rounded
  down.
  (`#16 <https://github.com/lmacken/quantumrandom/issues/16>`_,
  `#20 <https://github.com/lmacken/quantumrandom/issues/20>`_,
  `#24 <https://github.com/lmacken/quantumrandom/pull/24>`_ by
  Brian Ó Donnell)
* ``block_size`` can be no larger than 10, down from 1024. This is a limit of
  the new API, as is ``block_size`` now counting 16 bit values rather than
  bytes for ``hex16``. ``binary()`` and ``hex()`` now default to the most that
  one request can return: 20480 bytes, up from 10000.
* Invalid arguments raise ``ValueError``, and problems talking to the API
  raise ``QuantumRandomError`` or one of its subclasses. Before, these were a
  mix of ``Exception``, ``AssertionError`` and ``urllib`` errors.
* ``qrandom`` outputs one block and then exits, rather than making API
  requests until it is killed. Pass ``--count 0`` for the old behaviour.
* ``qrandom -h`` shows help, as you would expect, rather than being short for
  ``--hex``, which is now ``-x``.
* ``qrandom-dev`` and its ``/dev/qrandom`` device have been removed. The
  library that they depend upon is Python 2 only, and has not been
  installable for years.
  (`#5 <https://github.com/lmacken/quantumrandom/issues/5>`_,
  `#18 <https://github.com/lmacken/quantumrandom/issues/18>`_)

New
~~~

* ``QuantumRandom``, a subclass of ``random.Random``, brings everything in
  the ``random`` module to quantum random numbers: ``choice()``,
  ``shuffle()``, ``sample()``, ``uniform()``, and so on. Based on
  `#22 <https://github.com/lmacken/quantumrandom/pull/22>`_ by Caleb Johnson.
* ``randint`` and ``QuantumRandom`` buffer the random data that they have not
  used yet, so that thousands of numbers can come out of a single API
  request. ``randint`` used to make a request every time it was called.
  (`#21 <https://github.com/lmacken/quantumrandom/issues/21>`_)
* The ``uint8`` and ``hex8`` data types are supported by ``get_data``.
* Requests time out after 30 seconds, which can be changed with the new
  ``timeout`` argument. They used to wait forever.
  (`#22 <https://github.com/lmacken/quantumrandom/pull/22>`_,
  `#33 <https://github.com/lmacken/quantumrandom/issues/33>`_)
* Requests that are rate limited are retried automatically.
* ``qrandom --count`` works with ``--int``, and there are new ``--api-key``
  and ``--version`` options.

Fixed
~~~~~

* ``qrandom --binary`` writes raw bytes on Python 3, instead of their
  ``repr()``.
* ``qrandom`` reports errors, instead of silently exiting.
