# Copyright (c) 2012-2013 Luke Macken <lmacken@redhat.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
A Python interface to the ANU Quantum Numbers (AQN) API.

https://quantumnumbers.anu.edu.au

Every request needs an API key, which is free to create. Provide it with the
``QUANTUMRANDOM_API_KEY`` environment variable, :func:`set_api_key`, or the
``api_key`` argument that the functions here accept.
"""

import binascii
import json
import os
import random as _random
import threading
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

VERSION = __version__ = '2.0.0'
URL = 'https://api.quantumnumbers.anu.edu.au/'
API_KEY_ENV = 'QUANTUMRANDOM_API_KEY'
DATA_TYPES = ['uint8', 'uint16', 'hex8', 'hex16']
MAX_LEN = 1024
MAX_BLOCK_SIZE = 10
INT_BITS = 16
TIMEOUT = 30  # seconds to wait on the API when no timeout is given
MAX_RETRIES = 3  # times to retry a request that was rate limited

_api_key = None


class QuantumRandomError(Exception):
    """Something went wrong fetching data from the ANU Quantum Numbers API"""


class APIKeyError(QuantumRandomError):
    """No API key was provided, or the API rejected it"""


class RateLimitError(QuantumRandomError):
    """Requests were made faster than the API key's plan allows"""


class QuotaExceededError(QuantumRandomError):
    """The API key has used up its request quota"""


def set_api_key(api_key):
    """Set the API key to use when one is not passed in explicitly.

    This takes precedence over the QUANTUMRANDOM_API_KEY environment variable.
    """
    global _api_key
    _api_key = api_key


def _resolve_api_key(api_key=None):
    key = api_key or _api_key or os.environ.get(API_KEY_ENV)
    if not key or not key.strip():
        raise APIKeyError(
            "No API key found. Create a free one at "
            "https://quantumnumbers.anu.edu.au and then set the %s "
            "environment variable, call quantumrandom.set_api_key(), or "
            "pass api_key=" % API_KEY_ENV)
    key = key.strip()
    if not (key.isascii() and key.isprintable()) or ' ' in key:
        # Catch this here, as the errors that an unusable HTTP header leads
        # to further down would have the key itself in them.
        raise APIKeyError(
            "The API key is malformed. It should be a single line, without "
            "any spaces.")
    return key


def _describe(http_error):
    """Return the (error type, message) that the API sent with an error"""
    kind = ''
    if http_error.headers:
        kind = http_error.headers.get('x-amzn-errortype') or ''
    try:
        message = json.loads(http_error.read().decode('utf-8'))['message']
    except Exception:
        message = http_error.reason
    return kind, str(message)


def _retry_delay(http_error, attempt):
    """Seconds to wait before retrying a rate limited request"""
    try:
        return float(http_error.headers.get('Retry-After'))
    except (AttributeError, TypeError, ValueError):
        return float(2 ** (attempt - 1))


def _fetch(params, api_key, timeout):
    """Query the API, returning its decoded JSON response"""
    request = Request(URL + '?' + urlencode(params), headers={
        'x-api-key': api_key,
        'Accept': 'application/json',
        'User-Agent': 'quantumrandom/%s' % VERSION,
    })
    retries = 0
    while True:
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        except HTTPError as e:
            kind, message = _describe(e)
            if e.code == 403:
                raise APIKeyError(
                    "The API rejected the API key (HTTP 403: %s). Check it "
                    "at https://quantumnumbers.anu.edu.au" % message) from e
            if e.code == 429:
                # The API sits behind AWS API Gateway, which answers 429 both
                # when the monthly quota runs out ("Limit Exceeded") and when
                # requests arrive too quickly ("Too Many Requests"). Only the
                # latter is worth waiting out.
                if 'limitexceeded' in (kind + message).replace(' ', '').lower():
                    raise QuotaExceededError(
                        "The API key has used up its request quota "
                        "(HTTP 429: %s)" % message) from e
                if retries < MAX_RETRIES:
                    retries += 1
                    time.sleep(_retry_delay(e, retries))
                    continue
                raise RateLimitError(
                    "Still rate limited after %d retries (HTTP 429: %s)"
                    % (retries, message)) from e
            raise QuantumRandomError(
                "The API returned HTTP %s: %s" % (e.code, message)) from e
        except (OSError, ValueError) as e:
            raise QuantumRandomError(
                "Unable to fetch data from %s: %s" % (URL, e)) from e


def get_data(data_type='uint16', array_length=1, block_size=1, api_key=None,
             timeout=None):
    """Fetch data from the ANU Quantum Numbers JSON API.

    Each call makes one API request and returns a list of ``array_length``
    items. ``block_size`` only applies to the hex data types, where it sets
    how many 8 or 16 bit values make up each item.
    """
    if data_type not in DATA_TYPES:
        raise ValueError("data_type must be one of %s" % DATA_TYPES)
    if not 1 <= array_length <= MAX_LEN:
        raise ValueError("array_length must be between 1 and %s" % MAX_LEN)
    params = {'length': array_length, 'type': data_type}
    if data_type.startswith('hex'):
        if not 1 <= block_size <= MAX_BLOCK_SIZE:
            raise ValueError(
                "block_size must be between 1 and %s" % MAX_BLOCK_SIZE)
        params['size'] = block_size
    response = _fetch(params, _resolve_api_key(api_key),
                      TIMEOUT if timeout is None else timeout)
    if not isinstance(response, dict) or response.get('success') is not True:
        message = None
        if isinstance(response, dict):
            message = response.get('message')
        raise QuantumRandomError(
            "The API request failed: %s" % (message or response))
    data = response.get('data')
    if not isinstance(data, list) or len(data) != array_length:
        raise QuantumRandomError(
            "Asked the API for %d items but got: %r" % (array_length, data))
    return data


def binary(array_length=MAX_LEN, block_size=MAX_BLOCK_SIZE, api_key=None,
           timeout=None):
    """Return a chunk of binary data.

    The chunk is ``array_length * block_size * 2`` bytes long, which by
    default is 20480 bytes: the most that a single API request can return.
    """
    return binascii.unhexlify(hex(array_length, block_size, api_key, timeout))


def hex(array_length=MAX_LEN, block_size=MAX_BLOCK_SIZE, api_key=None,
        timeout=None):
    """Return a chunk of hex, twice as long as the equivalent binary()"""
    return ''.join(
        get_data('hex16', array_length, block_size, api_key, timeout))


def randint(min=0, max=10, generator=None):
    """Return a random int N such that min <= N <= max.

    Both ends are included, just like random.randint().

    Numbers are drawn from a shared buffer that is refilled with one API
    request whenever it runs dry, so that calling this repeatedly does not
    spend a request each time. If a generator of uint16 values is given, such
    as a cached_generator() instance, numbers are taken from that instead.
    """
    span = max - min + 1
    if span < 1:
        raise ValueError("max (%r) cannot be less than min (%r)" % (max, min))
    if span == 1:
        return min  # no need to spend random data on this
    if generator is None:
        return _shared.randint(min, max)
    # Draw just enough bits to cover the range and throw away any value that
    # lands outside of it. This keeps the result uniform, which taking a
    # modulus would not.
    bits = (span - 1).bit_length()
    words = (bits + INT_BITS - 1) // INT_BITS
    while True:
        num = 0
        for _ in range(words):
            num = (num << INT_BITS) | next(generator)
        num >>= words * INT_BITS - bits
        if num < span:
            return min + num


def uint16(array_length=100, api_key=None, timeout=None):
    """Return a numpy array of uint16 numbers"""
    import numpy
    return numpy.array(
        get_data('uint16', array_length, api_key=api_key, timeout=timeout),
        dtype=numpy.uint16)


def cached_generator(data_type='uint16', cache_size=1024, block_size=1,
                     api_key=None, timeout=None):
    """Returns numbers. Caches numbers to avoid latency.

    One API request is made for every ``cache_size`` numbers.
    """
    while 1:
        for n in get_data(data_type, cache_size, block_size, api_key, timeout):
            yield n


class QuantumRandom(_random.Random):
    """A drop-in for random.Random that is backed by quantum random numbers.

    All of the usual methods are available: random(), randint(), randrange(),
    choice(), shuffle(), sample(), uniform(), gauss(), and so on.

    Random data is fetched 20480 bytes at a time, the most that one API
    request can return, and handed out from a local buffer. A new request is
    only made once the buffer runs dry, and no byte is ever used twice.

    Like random.SystemRandom, this does not rely on software state, so
    sequences are not reproducible: seed() does nothing, and getstate() and
    setstate() are not implemented.
    """

    def __init__(self, *, api_key=None, timeout=None):
        self._api_key = api_key
        self._timeout = timeout
        self._buffer = b''
        self._pos = 0
        self._pid = os.getpid()
        self._lock = threading.Lock()
        super().__init__()

    def _read(self, n):
        """Take n bytes from the buffer, refilling it as needed"""
        chunks = []
        with self._lock:
            if self._pid != os.getpid():
                # A forked child must not hand out the same bytes as its
                # parent, so drop what was inherited.
                self._buffer, self._pos, self._pid = b'', 0, os.getpid()
            while n > 0:
                if self._pos >= len(self._buffer):
                    self._buffer = binary(api_key=self._api_key,
                                          timeout=self._timeout)
                    self._pos = 0
                chunk = self._buffer[self._pos:self._pos + n]
                self._pos += len(chunk)
                n -= len(chunk)
                chunks.append(chunk)
        return b''.join(chunks)

    def random(self):
        """Get the next random number in the range 0.0 <= X < 1.0"""
        return (int.from_bytes(self._read(7), 'big') >> 3) * 2.0 ** -53

    def getrandbits(self, k):
        """getrandbits(k) -> x. Generates an int with k random bits."""
        if k < 0:
            raise ValueError('number of bits must be non-negative')
        numbytes = (k + 7) // 8
        x = int.from_bytes(self._read(numbytes), 'big')
        return x >> (numbytes * 8 - k)

    def randbytes(self, n):
        """Generate n random bytes"""
        return self._read(n)

    def seed(self, *args, **kwds):
        """Does nothing: there is no state to seed"""
        return None

    def _notimplemented(self, *args, **kwds):
        """Method should not be called for a quantum random number generator"""
        raise NotImplementedError('Quantum entropy source does not have state.')

    getstate = setstate = _notimplemented


_shared = QuantumRandom()


__all__ = ['get_data', 'binary', 'hex', 'uint16', 'cached_generator',
           'randint', 'set_api_key', 'QuantumRandom', 'QuantumRandomError',
           'APIKeyError', 'RateLimitError', 'QuotaExceededError']
