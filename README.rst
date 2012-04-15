A Python interface to the ANU Quantum Random Numbers Server
===========================================================

This module is used to fetch blocks of random binary, hex, or character
data from `The ANU Quantum Random Number Generator
<http://physics0054.anu.edu.au>`_.


::

   import quantumrandom

   # Get a string of 1024 random bits
   quantumrandom.binary()

   # Get a string of 1024 bytes of randomness in hexadecimal form
   quantumrandom.hex()

   # Get 1024 random alphanumeric (and underscore) characters
   quantumrandom.char()

If for some reason it cannot obtain the correct amount of data in the
expected format, these functions will raise exceptions.

:warning: Due to the lack of an SSL/TLS interface at the moment, all data is sent over the wire in clear text.
