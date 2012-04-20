Tools for utilizing the ANU Quantum Random Numbers Server
=========================================================

This module provides tools for interacting with the `The ANU Quantum Random
Number Generator <http://physics0054.anu.edu.au>`_. It communicates with their
JSON API and provides a ``qrandom`` command-line tool, a Python API, and a
/dev/qrandom character device.

:warning: Due to the lack of an SSL/TLS interface at the moment, all data is sent over the wire in clear text.

Installing
----------

::

    $ virtualenv env
    $ source env/bin/activate
    $ pip install quantumrandom

Command-line tool
-----------------

::

    $ qrandom --binary
    ���I�%��e(�1��c��Ee�4�������j�Կ��=�^H�c�u
    oq��G��Z�^���fK�0_��h��s�b��AE=�rR~���(�^Q�)4��{c�������X{f��a�Bk�N%#W
    +a�a̙�IB�,S�!ꀔd�2H~�X�Z����R��.f
    ...

    $ qrandom --hex
    1dc59fde43b5045120453186d45653dd455bd8e6fc7d8c591f0018fa9261ab2835eb210e8
    e267cf35a54c02ce2a93b3ec448c4c7aa84fdedb61c7b0d87c9e7acf8e9fdadc8d68bcaa5a
    ...

    $ qrandom --binary | dd of=data
    ^C1752+0 records in
    1752+0 records out
    897024 bytes (897 kB) copied, 77.7588 s, 11.5 kB/s


Python API
--------

There are a few high-level functions that let you fetch large chunks of
``binary``, ``hex``, and ``uint16`` data. Without any arguments, it will fetch
the largest amount of data possible with a single API call.

::

    >>> quantumrandom.binary()[0]
    '\xa5'
    >>> len(quantumrandom.binary())
    10000
    >>> quantumrandom.hex()[:10]
    '8272613343'
    >>> quantumrandom.uint16(1)
    numpy.array([48141], dtype=numpy.uint16)
    >>> quantumrandom.uint16(1).data[:]
    '\xcd\x93'

There is also a lower-level ``get_data`` function that gives you more control
over what and how much data you want.

::

    >>> quantumrandom.get_data()
    [26646]
    >>> quantumrandom.get_data(data_type='uint16', array_length=5)
    [42796, 32457, 9242, 11316, 21078]
    >>> quantumrandom.get_data(data_type='hex16', array_length=5, block_size=2)
    ['f1d5', '0eb3', '1119', '7cfd', '64ce']

Valid ``data_type`` values are ``uint16`` and ``hex16``, and the
``array_length`` and ``block_size`` cannot be larger than ``100``. If for some
reason the API call is not successful, or the incorrect amount of data is
returned from the server, this function will raise an exception.

Creating /dev/qrandom
---------------------

quantumrandom provides a multi-threaded userspace character-device that can be
used to provide random data similar to /dev/random. You can also use it to
provide entropy to your system rng.

::

    pip install ctypeslib hg+https://cusepy.googlecode.com/hg
    sudo modprobe cuse
    sudo env/bin/python quantumrandom/dev.py qrandom
    sudo chmod 666 /dev/qrandom

Adding entropy into the Linux random number generator
-----------------------------------------------------

::

    sudo rngd --rng-device=/dev/qrandom -random-device=/dev/urandom --foreground

Monitoring your available entropy levels
----------------------------------------

::

    watch -n 1 cat /proc/sys/kernel/random/entropy_avail

Check the randomness against `FIPS 140-2 <https://en.wikipedia.org/wiki/FIPS_140-2>`_ tests
---------------------------------------------

::

    $ cat /dev/qrandom | rngtest --blockcount=1000
    rngtest: bits received from input: 20000032
    rngtest: FIPS 140-2 successes: 1000
    rngtest: FIPS 140-2 failures: 0
    rngtest: FIPS 140-2(2001-10-10) Monobit: 0
    rngtest: FIPS 140-2(2001-10-10) Poker: 0
    rngtest: FIPS 140-2(2001-10-10) Runs: 0
    rngtest: FIPS 140-2(2001-10-10) Long run: 0
    rngtest: FIPS 140-2(2001-10-10) Continuous run: 0
    rngtest: input channel speed: (min=17.696; avg=386.711; max=4882812.500)Kibits/s
    rngtest: FIPS tests speed: (min=10.949; avg=94.538; max=161.640)Mibits/s
    rngtest: Program run time: 50708319 microseconds
