A Python interface to the ANU Quantum Random Numbers Server
===========================================================

This module provides a Python interface to `The ANU Quantum Random Number
Generator <http://physics0054.anu.edu.au>`_ JSON API.

Usage
-----

::

    >>> import quantumrandom
    >>> quantumrandom.get_data(data_type='uint16', array_length=1, block_size=1)
    {u'data': [35817], u'length': u'1', u'type': u'uint16', u'success': True}

Valid ``data_types`` values are ``uint16`` and ``hex16``.
The ``array_length`` cannot be larger than ``100``.

:warning: Due to the lack of an SSL/TLS interface at the moment, all data is sent over the wire in clear text.
