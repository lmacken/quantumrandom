"""
A test against the real ANU Quantum Numbers API.

API requests are metered (the free plan allows 100 a month), so this is
skipped unless it is asked for:

    QUANTUMRANDOM_LIVE_TEST=1 QUANTUMRANDOM_API_KEY=... pytest tests/test_live.py

It spends exactly one request.
"""

import os

import pytest

import quantumrandom


@pytest.mark.skipif(os.environ.get('QUANTUMRANDOM_LIVE_TEST') != '1',
                    reason="QUANTUMRANDOM_LIVE_TEST=1 is not set")
def test_live_api():
    qr = quantumrandom.QuantumRandom()
    data = qr.randbytes(1024)
    assert len(data) == 1024
    assert len(set(data)) > 200  # 1024 random bytes cover most byte values
    assert all(1 <= qr.randint(1, 6) <= 6 for _ in range(100))
    assert all(0.0 <= qr.random() < 1.0 for _ in range(100))
    # All of the above came out of a single request's worth of data
    assert len(qr._buffer) == 20480
