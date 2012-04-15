A Python interface to the ANU Quantum Random Numbers Server
===========================================================

http://physics0054.anu.edu.au

:warning: This module performs absolutely no error checking. The user is currently responsible for handling any exceptions due to server outages, etc.

Usage
-----

::

   import quantumrandom
   
   # Get a string 1024 random bits, bytes in hex, or characters
   quantumrandom.binary()
   quantumrandom.hex()
   quantumrandom.char()
