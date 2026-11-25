"""
None of these tests touch the network. API requests are metered, so urlopen is
replaced with a stand-in that answers the way the real API does.

See test_live.py for an opt-in test against the real thing.
"""

import collections
import email.message
import io
import json
import os
import random
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

import pytest

import quantumrandom
from quantumrandom import cmd

HEX_DIGITS = set('0123456789abcdef')
BLOCK_BYTES = 20480  # what one maxed out API request returns


class FakeAPI(object):
    """A stand-in for urlopen that behaves like the ANU Quantum Numbers API"""

    def __init__(self):
        self.requests = []
        self.timeouts = []
        self.sleeps = []
        self.queue = []  # replies to give ahead of the well-behaved ones
        self.served = []  # the binary equivalent of each hex reply
        self.rng = random.Random(0)

    def __call__(self, request, timeout=None):
        self.requests.append(request)
        self.timeouts.append(timeout)
        if self.queue:
            reply = self.queue.pop(0)
            if isinstance(reply, BaseException):
                raise reply
            if not isinstance(reply, bytes):
                reply = json.dumps(reply).encode('ascii')
            return io.BytesIO(reply)
        query = self.query()
        data_type, length = query['type'], int(query['length'])
        bits = 16 if data_type.endswith('16') else 8
        if data_type.startswith('uint'):
            data = [self.rng.getrandbits(bits) for _ in range(length)]
        else:
            digits = int(query['size']) * bits // 4
            data = [''.join(self.rng.choice('0123456789abcdef')
                            for _ in range(digits))
                    for _ in range(length)]
            self.served.append(bytes.fromhex(''.join(data)))
        # Yes, the real API sends the length back as a string
        return io.BytesIO(json.dumps({
            'success': True, 'type': data_type, 'length': str(length),
            'data': data,
        }).encode('ascii'))

    def query(self, index=-1):
        """The query string parameters of a request that was made"""
        url = urlsplit(self.requests[index].full_url)
        return dict((k, v[0]) for k, v in parse_qs(url.query).items())

    def api_key(self, index=-1):
        """The API key that a request was made with"""
        return self.requests[index].get_header('X-api-key')


def http_error(code, message, kind=None, headers=None):
    """An error as returned by AWS API Gateway, which fronts the API"""
    hdrs = email.message.Message()
    if kind:
        hdrs['x-amzn-errortype'] = kind
    for name, value in (headers or {}).items():
        hdrs[name] = value
    body = io.BytesIO(json.dumps({'message': message}).encode('ascii'))
    return HTTPError(quantumrandom.URL, code, message, hdrs, body)


def throttled(**headers):
    return http_error(429, 'Too Many Requests', 'TooManyRequestsException',
                      headers)


@pytest.fixture(autouse=True)
def api(monkeypatch):
    fake = FakeAPI()
    monkeypatch.setattr(quantumrandom, 'urlopen', fake)
    monkeypatch.setattr(quantumrandom.time, 'sleep', fake.sleeps.append)
    monkeypatch.setattr(quantumrandom, '_api_key', None)
    monkeypatch.setattr(quantumrandom, '_shared', quantumrandom.QuantumRandom())
    monkeypatch.setenv(quantumrandom.API_KEY_ENV, 'env-key')
    return fake


# get_data

def test_get_data_defaults(api):
    data = quantumrandom.get_data()
    assert len(data) == 1
    assert type(data[0]) is int and 0 <= data[0] < 2 ** 16
    assert api.requests[0].full_url.startswith(
        'https://api.quantumnumbers.anu.edu.au/?')
    assert api.query() == {'type': 'uint16', 'length': '1'}
    assert api.api_key() == 'env-key'
    assert api.timeouts == [quantumrandom.TIMEOUT]


@pytest.mark.parametrize('data_type,limit', [('uint8', 2 ** 8),
                                             ('uint16', 2 ** 16)])
def test_get_data_uint(api, data_type, limit):
    data = quantumrandom.get_data(data_type, 100)
    assert len(data) == 100
    assert all(type(n) is int and 0 <= n < limit for n in data)
    assert 'size' not in api.query()


@pytest.mark.parametrize('data_type,digits', [('hex8', 2), ('hex16', 4)])
def test_get_data_hex(api, data_type, digits):
    data = quantumrandom.get_data(data_type, 5, 3)
    assert len(data) == 5
    for block in data:
        assert type(block) is str
        assert len(block) == 3 * digits
        assert set(block) <= HEX_DIGITS
    assert api.query() == {'type': data_type, 'length': '5', 'size': '3'}


def test_get_data_max_sizes(api):
    assert len(quantumrandom.get_data('uint16', 1024)) == 1024
    assert len(quantumrandom.get_data('hex16', 1024, 10)) == 1024


@pytest.mark.parametrize('args', [
    ('binary', 1, 1),
    ('uint16', 0),
    ('uint16', 1025),
    ('hex16', 1, 0),
    ('hex16', 1, 11),
])
def test_get_data_invalid_arguments(api, args):
    with pytest.raises(ValueError):
        quantumrandom.get_data(*args)
    assert not api.requests


def test_get_data_block_size_ignored_for_uint(api):
    # The API only looks at the block size for the hex types
    assert len(quantumrandom.get_data('uint16', 5, 1024)) == 5


def test_get_data_timeout(api):
    quantumrandom.get_data(timeout=3)
    assert api.timeouts == [3]


def test_get_data_unsuccessful(api):
    api.queue.append({'success': False, 'message': 'the laser is off'})
    with pytest.raises(quantumrandom.QuantumRandomError) as e:
        quantumrandom.get_data()
    assert 'the laser is off' in str(e.value)


def test_get_data_wrong_amount(api):
    api.queue.append({'success': True, 'type': 'uint16', 'length': '2',
                      'data': [1, 2]})
    with pytest.raises(quantumrandom.QuantumRandomError):
        quantumrandom.get_data('uint16', 5)


# API keys

def test_api_key_from_set_api_key(api):
    quantumrandom.set_api_key('set-key')
    quantumrandom.get_data()
    assert api.api_key() == 'set-key'


def test_api_key_from_argument(api):
    quantumrandom.set_api_key('set-key')
    quantumrandom.get_data(api_key='arg-key')
    assert api.api_key() == 'arg-key'
    quantumrandom.hex(api_key='arg-key-2')
    assert api.api_key() == 'arg-key-2'


def test_api_key_whitespace_is_stripped(api, monkeypatch):
    monkeypatch.setenv(quantumrandom.API_KEY_ENV, ' env-key\n')
    quantumrandom.get_data()
    assert api.api_key() == 'env-key'


@pytest.mark.parametrize('value', [None, '', '  '])
def test_api_key_missing(api, monkeypatch, value):
    if value is None:
        monkeypatch.delenv(quantumrandom.API_KEY_ENV)
    else:
        monkeypatch.setenv(quantumrandom.API_KEY_ENV, value)
    with pytest.raises(quantumrandom.APIKeyError) as e:
        quantumrandom.get_data()
    assert quantumrandom.API_KEY_ENV in str(e.value)
    assert not api.requests


@pytest.mark.parametrize('key', ['s3cret\nlogin: me', 's3cret key',
                                 's3cret\x00', 's3crét'])
def test_api_key_malformed(api, key):
    # e.g. a multi-line entry straight out of a password manager
    with pytest.raises(quantumrandom.APIKeyError) as e:
        quantumrandom.get_data(api_key=key)
    assert 's3cr' not in str(e.value)  # do not leak it into logs
    assert not api.requests


# Errors from the API

def test_rejected_api_key(api):
    api.queue.append(http_error(403, 'Forbidden', 'ForbiddenException'))
    with pytest.raises(quantumrandom.APIKeyError):
        quantumrandom.get_data()
    assert len(api.requests) == 1


def test_quota_exceeded_is_not_retried(api):
    api.queue.append(
        http_error(429, 'Limit Exceeded', 'LimitExceededException'))
    with pytest.raises(quantumrandom.QuotaExceededError):
        quantumrandom.get_data()
    assert len(api.requests) == 1
    assert not api.sleeps


def test_rate_limit_is_retried(api):
    api.queue.extend([throttled(), throttled()])
    assert len(quantumrandom.get_data('uint16', 3)) == 3
    assert len(api.requests) == 3
    assert api.sleeps == [1.0, 2.0]


def test_rate_limit_honours_retry_after(api):
    api.queue.append(throttled(**{'Retry-After': '7'}))
    quantumrandom.get_data()
    assert api.sleeps == [7.0]


def test_rate_limit_gives_up(api):
    api.queue.extend(throttled() for _ in range(10))
    with pytest.raises(quantumrandom.RateLimitError):
        quantumrandom.get_data()
    assert len(api.requests) == quantumrandom.MAX_RETRIES + 1


@pytest.mark.parametrize('reply', [
    http_error(500, 'Internal Server Error'),
    URLError('Name or service not known'),
    TimeoutError('timed out'),
    b'<html>definitely not json</html>',
    b'[]',
])
def test_other_failures(api, reply):
    api.queue.append(reply)
    with pytest.raises(quantumrandom.QuantumRandomError) as e:
        quantumrandom.get_data()
    assert type(e.value) is quantumrandom.QuantumRandomError
    assert len(api.requests) == 1


# Helpers

def test_hex(api):
    hex = quantumrandom.hex()
    assert len(hex) == BLOCK_BYTES * 2
    assert set(hex) <= HEX_DIGITS
    assert api.query() == {'type': 'hex16', 'length': '1024', 'size': '10'}
    assert len(api.requests) == 1


def test_binary(api):
    binary = quantumrandom.binary()
    assert type(binary) is bytes
    assert len(binary) == BLOCK_BYTES
    assert binary == api.served[0]
    assert len(api.requests) == 1


def test_binary_smaller(api):
    assert len(quantumrandom.binary(10, 5)) == 100
    assert len(quantumrandom.hex(10, 5)) == 200


def test_uint16(api):
    numpy = pytest.importorskip('numpy')
    ints = quantumrandom.uint16()
    assert len(ints) == 100
    assert ints.dtype == numpy.uint16
    assert ints.data.nbytes == 200


def test_cached_generator(api):
    generator = quantumrandom.cached_generator()
    numbers = [next(generator) for _ in range(2500)]
    assert all(type(n) is int and 0 <= n < 2 ** 16 for n in numbers)
    assert len(api.requests) == 3
    assert api.query() == {'type': 'uint16', 'length': '1024'}


def test_cached_generator_hex(api):
    generator = quantumrandom.cached_generator('hex8', 10, block_size=4,
                                               api_key='gen-key')
    assert len(next(generator)) == 8
    assert api.query() == {'type': 'hex8', 'length': '10', 'size': '4'}
    assert api.api_key() == 'gen-key'


# randint

def test_randint_includes_both_ends(api):
    # https://github.com/lmacken/quantumrandom/pull/25
    assert set(quantumrandom.randint(0, 1) for _ in range(200)) == {0, 1}
    seen = set(quantumrandom.randint(5, 15) for _ in range(2000))
    assert seen == set(range(5, 16))


def test_randint_returns_ints(api):
    # https://github.com/lmacken/quantumrandom/issues/20
    for _ in range(100):
        assert type(quantumrandom.randint(0, 20)) is int


def test_randint_shares_one_request(api):
    for _ in range(5000):
        quantumrandom.randint(1, 6)
    assert len(api.requests) == 1


def test_randint_empty_range(api):
    assert quantumrandom.randint(0, 0) == 0
    assert quantumrandom.randint(7, 7, generator=iter([])) == 7
    assert not api.requests


def test_randint_negative_and_huge_ranges(api):
    for _ in range(100):
        assert -5 <= quantumrandom.randint(-5, 5) <= 5
        assert 0 <= quantumrandom.randint(0, 10 ** 30) <= 10 ** 30


def test_randint_backwards_range(api):
    with pytest.raises(ValueError):
        quantumrandom.randint(5, 1)
    with pytest.raises(ValueError):
        quantumrandom.randint(5, 1, generator=iter([1, 2, 3]))


def test_randint_with_generator(api):
    generator = quantumrandom.cached_generator()
    seen = set(quantumrandom.randint(1, 6, generator) for _ in range(500))
    assert seen == {1, 2, 3, 4, 5, 6}
    assert len(api.requests) == 1


def test_randint_with_generator_is_uniform(api):
    # https://github.com/lmacken/quantumrandom/issues/16
    # Feed in every possible uint16 exactly once. If no result is favoured,
    # each one will have come up exactly the same number of times.
    every_uint16 = iter(range(2 ** 16))
    counts = collections.Counter()
    with pytest.raises(StopIteration):
        while True:
            counts[quantumrandom.randint(10, 19, every_uint16)] += 1
    assert counts == dict((n, 4096) for n in range(10, 20))


def test_randint_with_generator_wide_range(api):
    # Too wide for one uint16, so three get stitched together
    words = iter([0x0001, 0x0002, 0x0003])
    assert quantumrandom.randint(0, 2 ** 48 - 1, words) == 0x000100020003
    generator = quantumrandom.cached_generator()
    for _ in range(100):
        assert 0 <= quantumrandom.randint(0, 2 ** 40, generator) <= 2 ** 40
    assert len(api.requests) == 1


# QuantumRandom

def test_quantum_random_is_a_random(api):
    qr = quantumrandom.QuantumRandom()
    assert isinstance(qr, random.Random)
    assert not api.requests  # nothing is fetched until it is needed


def test_quantum_random_random(api):
    qr = quantumrandom.QuantumRandom()
    numbers = [qr.random() for _ in range(2000)]
    assert all(0.0 <= n < 1.0 for n in numbers)
    assert 0.4 < sum(numbers) / len(numbers) < 0.6
    assert len(api.requests) == 1


def test_quantum_random_getrandbits(api):
    qr = quantumrandom.QuantumRandom()
    assert qr.getrandbits(0) == 0
    assert not api.requests
    for k in (1, 7, 8, 9, 16, 53, 64, 1000):
        for _ in range(20):
            assert 0 <= qr.getrandbits(k) < 2 ** k
    assert max(qr.getrandbits(3) for _ in range(200)) == 7
    with pytest.raises(ValueError):
        qr.getrandbits(-1)


def test_quantum_random_never_reuses_bytes(api):
    qr = quantumrandom.QuantumRandom()
    first, second = qr.randbytes(10), qr.randbytes(10)
    assert first + second == api.served[0][:20]
    rest = qr.randbytes(BLOCK_BYTES * 2)
    assert len(api.requests) == 3
    assert first + second + rest == b''.join(api.served)[:20 + BLOCK_BYTES * 2]
    assert qr.randbytes(5) == api.served[2][20:25]
    assert qr.randbytes(0) == b''
    assert len(api.requests) == 3


def test_quantum_random_inherited_methods(api):
    qr = quantumrandom.QuantumRandom()
    assert set(qr.randint(1, 6) for _ in range(500)) == {1, 2, 3, 4, 5, 6}
    assert set(qr.randrange(0, 10, 5) for _ in range(100)) == {0, 5}
    assert qr.choice('abc') in 'abc'
    deck = list(range(52))
    qr.shuffle(deck)
    assert deck != list(range(52)) and sorted(deck) == list(range(52))
    assert sorted(qr.sample(range(10), 10)) == list(range(10))
    assert 1.0 <= qr.uniform(1, 2) <= 2.0
    assert isinstance(qr.gauss(0, 1), float)
    assert len(api.requests) == 1


def test_quantum_random_has_no_state(api):
    qr = quantumrandom.QuantumRandom()
    assert qr.seed(42) is None
    with pytest.raises(NotImplementedError):
        qr.getstate()
    with pytest.raises(NotImplementedError):
        qr.setstate(None)


def test_quantum_random_api_key_and_timeout(api):
    quantumrandom.QuantumRandom(api_key='my-key', timeout=5).random()
    assert api.api_key() == 'my-key'
    assert api.timeouts == [5]


def test_quantum_random_buffer_not_shared_with_forked_child(api, monkeypatch):
    qr = quantumrandom.QuantumRandom()
    assert qr.randbytes(4) == api.served[0][:4]
    monkeypatch.setattr(os, 'getpid', lambda: -1)  # now we are "the child"
    assert qr.randbytes(4) == api.served[1][:4]
    assert qr.randbytes(4) == api.served[1][4:8]
    assert len(api.requests) == 2


# The qrandom command

def test_cmd_int(api, capsys):
    assert cmd.main(['--int', '--min', '5', '--max', '15']) == 0
    out, err = capsys.readouterr()
    assert 5 <= int(out) <= 15
    assert not err


def test_cmd_int_count(api, capsys):
    assert cmd.main(['-i', '--max', '1', '--count', '50']) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 50
    assert set(lines) == {'0', '1'}
    assert len(api.requests) == 1


def test_cmd_hex(api, capsys):
    assert cmd.main(['--hex']) == 0
    out = capsys.readouterr().out
    assert out.endswith('\n')
    assert len(out.strip()) == BLOCK_BYTES * 2
    assert set(out.strip()) <= HEX_DIGITS
    assert len(api.requests) == 1


def test_cmd_binary(api, capsysbinary):
    assert cmd.main(['--binary', '--count', '2']) == 0
    assert capsysbinary.readouterr().out == b''.join(api.served)
    assert len(api.requests) == 2


def test_cmd_count_zero_runs_until_interrupted(api, capsys):
    block = {'success': True, 'type': 'hex16', 'length': '1024',
             'data': ['ab' * 20] * 1024}
    api.queue.extend([block, block, KeyboardInterrupt()])
    assert cmd.main(['-x', '-c', '0']) == 130
    assert len(capsys.readouterr().out.splitlines()) == 2


def test_cmd_api_key(api, capsys):
    assert cmd.main(['--int', '--api-key', 'cmd-key']) == 0
    assert api.api_key() == 'cmd-key'


def test_cmd_reports_errors(api, capsys, monkeypatch):
    monkeypatch.delenv(quantumrandom.API_KEY_ENV)
    assert cmd.main(['--hex']) == 1
    out, err = capsys.readouterr()
    assert not out
    assert err.startswith('qrandom: No API key found')
    assert not api.requests


@pytest.mark.parametrize('argv,status', [
    (['-h'], 0),
    (['--help'], 0),
    (['--version'], 0),
    ([], 2),
    (['--int', '--hex'], 2),
    (['--int', '--min', '5', '--max', '1'], 2),
    (['--hex', '--count', '-1'], 2),
])
def test_cmd_usage(api, capsys, argv, status):
    with pytest.raises(SystemExit) as e:
        cmd.main(argv)
    assert e.value.code == status
    assert not api.requests  # asking for help should never cost a request
