Tools for utilizing the ANU Quantum Random Numbers Server
=========================================================

.. image:: https://pypip.in/v/quantumrandom/badge.png
   :target: https://crate.io/packages/quantumrandom
.. image:: https://pypip.in/d/quantumrandom/badge.png
   :target: https://crate.io/packages/quantumrandom

This project provides tools for interacting with The ANU Quantum Random
Number Generator (`qrng.anu.edu.au <http://qrng.anu.edu.au>`_). It
communicates with their JSON API and provides a ``qrandom`` command-line
tool, a Python API, and a Linux ``/dev/qrandom`` character device.

quantumrandom works on Python 2 and 3.

.. note:: As of version 1.7, quantumrandom now uses SSL/TLS by default.

Installing
----------

::

    pip install quantumrandom

Command-line tool
-----------------

::

    $ qrandom --int --min 5 --max 15
    7
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


Creating /dev/qrandom
---------------------

quantumrandom comes equipped with a multi-threaded character device in
userspace. When read from, this device fires up a bunch of threads to
fetch data. Not only can you utilize this as a rng, but you can also feed
this data back into your system's entropy pool.

In order to build it's dependencies, you'll need the following packages
installed: svn gcc-c++ fuse-devel gccxml libattr-devel. On Fedora 17 and
newer, you'll also need the kernel-modules-extra package installed for the
cuse module.

.. note:: The /dev/qrandom character device currently only supports Python2

::

    pip install ctypeslib hg+https://cusepy.googlecode.com/hg
    sudo modprobe cuse
    sudo chmod 666 /dev/cuse
    qrandom-dev
    sudo chmod 666 /dev/qrandom

By default it will use 3 threads, which can be changed by passing '-t #' into the qrandom-dev.

Testing the randomness for `FIPS 140-2 <https://en.wikipedia.org/wiki/FIPS_140-2>`_ compliance
----------------------------------------------------------------------------------------------

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

Adding entropy to the Linux random number generator
---------------------------------------------------

::

    sudo rngd --rng-device=/dev/qrandom --random-device=/dev/random --timeout=5 --foreground

Monitoring your available entropy levels
----------------------------------------

::

    watch -n 1 cat /proc/sys/kernel/random/entropy_avail

Python API
----------

The quantumrandom Python module contains a low-level ``get_data``
function, which is modelled after the ANU Quantum Random Number
Generator's JSON API. It returns variable-length lists of either
``uint16`` or ``hex16`` data.

::

    >>> quantumrandom.get_data()
    [26646]
    >>> quantumrandom.get_data(data_type='uint16', array_length=5)
    [42796, 32457, 9242, 11316, 21078]
    >>> quantumrandom.get_data(data_type='hex16', array_length=5, block_size=2)
    ['f1d5', '0eb3', '1119', '7cfd', '64ce']

Valid ``data_type`` values are ``uint16`` and ``hex16``, and the
``array_length`` and ``block_size`` cannot be larger than ``1024``. If for some
reason the API call is not successful, or the incorrect amount of data is
returned from the server, this function will raise an exception.

Based on this ``get_data`` function, quantumrandom also provides a bunch
of higher-level helper functions that make easy to perform a variety of
tasks.

::

    >>> quantumrandom.randint(0, 20)
    5
    >>> quantumrandom.hex()[:10]
    '8272613343'
    >>> quantumrandom.binary()[0]
    '\xa5'
    >>> len(quantumrandom.binary())
    10000
    >>> quantumrandom.uint16()
    numpy.array([24094, 13944, 22109, 22908, 34878, 33797, 47221, 21485, 37930, ...], dtype=numpy.uint16)
    >>> quantumrandom.uint16().data[:10]
    '\x87\x7fY.\xcc\xab\xea\r\x1c`'
