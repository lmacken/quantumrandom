from binascii import hexlify as _hexlify
from random import Random, RECIP_BPF
import quantumrandom
import six
import threading


_longint = int if six.PY3 else long


class _QRBackgroundFetchThread(threading.Thread):
    def __init__(self, qr):
        self.qr = qr
        self.should_fetch = threading.Event()
        self.idle = threading.Event()
        threading.Thread.__init__(self)
        self.daemon = True
        self.start()

    def run(self):
        while self.should_fetch.wait():
            self.idle.clear()
            try:
                self.qr._refresh()
            finally:
                self.idle.set()
                self.should_fetch.clear()


class QuantumRandom(Random):
    "An implementation of random.Random that uses the ANU quantum random API"
    def __init__(self, x=None, cached_bytes=1024, autofetch_at=1024-64, fetch_timeout=None):
        self._fetcher = None
        self._autofetch_at = autofetch_at
        self._fetch_timeout = fetch_timeout

        if cached_bytes:
            self._buf_idx = 1024  # start uninitialized
            self._buf_len = cached_bytes
            self._buf_lock = threading.RLock()
            self._cache_buf = bytearray(cached_bytes)

            if autofetch_at:
                self._fetcher = _QRBackgroundFetchThread(self)
                self._fetcher.should_fetch.set()
        else:
            self._autofetch_at = None
            self._cache_buf = None

        Random.__init__(self, x)

    def _fetch_qr(self, b):
        if b > 1024:
            blocks = (b + 1023) // 1024
            block_size = 1024
        else:
            blocks = 1
            block_size = b

        return quantumrandom.binary(blocks, block_size, timeout=self._fetch_timeout)

    def _refresh(self, over=0):
        refresh = self._fetch_qr(self._buf_len + over)

        with self._buf_lock:
            self._cache_buf[:] = refresh[over:]
            self._buf_idx = 0

        if over:
            return refresh[:over]

    def _qrandom(self, b):
        if self._cache_buf:
            with self._buf_lock:
                ret = self._cache_buf[self._buf_idx : self._buf_idx + b]
                over = self._buf_idx + b - self._buf_len

            if over > 0:
                if self._fetcher and self._fetcher.idle.is_set():
                    ret += self._refresh(over)
                else:
                    self._fetcher and self._fetcher.idle.wait()
                    ret += self._qrandom(over)
            else:
                self._buf_idx += b

            # notify the background thread that we need more data
            if (self._autofetch_at and self._buf_idx > self._autofetch_at
                    and not self._fetcher.should_fetch.is_set()):
                self._fetcher.should_fetch.set()

            return ret
        else:
            return self._fetch_qr(b)

    def random(self):
        intstr = _hexlify(self._qrandom(7))
        return (_longint(intstr, 16) >> 3) * RECIP_BPF

    def getrandbits(self, k):
        if k <= 0:
            raise ValueError('number of bits must be greater than zero')
        if k != int(k):
            raise TypeError('number of bits should be an integer')

        # bits / 8 and rounded up
        numbytes = (k + 7) // 8
        x = _longint(_hexlify(self._qrandom(numbytes)), 16)
        # trim excess bits
        return x >> (numbytes * 8 - k)

    def seed(self, *args, **kwds):
        return None

    def _notimplemented(self, *args, **kwds):
        raise NotImplementedError('Quantum entropy source does not have state.')

    getstate = setstate = _notimplemented


__all__ = ['QuantumRandom']
