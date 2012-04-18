A Python interface to the ANU Quantum Random Numbers Server
===========================================================

This module provides a Python interface to `The ANU Quantum Random Number
Generator <http://physics0054.anu.edu.au>`_ JSON API.

Usage
-----

::

    >>> import quantumrandom
    >>> quantumrandom.get_data()
    [26646]
    >>> quantumrandom.get_data(data_type='uint16', array_length=5)
    [42796, 32457, 9242, 11316, 21078]
    >>> quantumrandom.get_data(data_type='hex16', array_length=5, block_size=2)
    ['f1d5', '0eb3', '1119', '7cfd', '64ce']

Valid ``data_type`` values are ``uint16`` and ``hex16``, and the
``array_length`` cannot be larger than ``100``. If for some reason the API
call is not successful, or the incorrect amount of data is returned, this
function will raise an exception.

:warning: Due to the lack of an SSL/TLS interface at the moment, all data is sent over the wire in clear text.
