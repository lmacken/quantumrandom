A Python interface to the ANU Quantum Random Numbers Server
===========================================================

http://physics0054.anu.edu.au

Usage
-----

::

   import quantumrandom
   
   # Get a string 1024 random bits, bytes in hex, or characters
   quantumrandom.binary()
   quantumrandom.hex()
   quantumrandom.char()

:warning: This module performs absolutely no error checking, exception handling, or validation. Also, due to the lack of an SSL/TLS interface at the moment, all data is sent over the wire in clear text.
