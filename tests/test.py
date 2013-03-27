import time
import unittest
import quantumrandom

from mock import patch
from surrogate import surrogate

return_data = None

class MockCuse(object):

    def fuse_reply_buf(self, req, data, length):
        global return_data
        return_data = data

    def fuse_reply_err(self, req, err):
        pass


class TestQuantumRandom(unittest.TestCase):

    def test_uint16_json_api(self):
        data = quantumrandom.get_data('uint16', 1, 1)
        assert len(data) == 1
        for i in str(data[0]):
            assert i in '0123456789', i

    def test_uint16_json_api_max_array(self):
        data = quantumrandom.get_data('uint16', 100, 100)
        assert len(data) == 100

    def test_hex16_json_api(self):
        data = quantumrandom.get_data('hex16', 1, 1)
        assert len(data) == 1
        for h in data[0]:
            assert h in '0123456789abcdef', h

    def test_uint16_json_api_long_array(self):
        try:
            data = quantumrandom.get_data('uint16', 1025, 1)
            assert False, "Invalid array length didn't cause error: %s" % data
        except:
            pass

    def test_uint16_json_api_large_blocksize(self):
        try:
            data = quantumrandom.get_data('uint16', 1, 1025)
            assert False, "Invalid block size didn't cause error: %s" % data
        except:
            pass

    def test_uint16_json_api_invalid_type(self):
        try:
            data = quantumrandom.get_data('binary', 1, 1)
            assert False, "Invalid type didn't throw exception: %s" % data
        except:
            pass

    def test_ensure_bytestrings(self):
        data = quantumrandom.get_data('hex16', 1, 1)
        assert type(data[0]) is str, data

    def test_binary(self):
        binary = quantumrandom.binary()
        assert binary
        assert len(binary) == 10000, len(binary)

    def test_hex(self):
        hex = quantumrandom.hex()
        assert hex
        assert len(hex) == 20000, len(hex)
        for h in hex:
            assert h in '1234567890abcdef', h

    def test_uint16(self):
        ints = quantumrandom.uint16()
        assert len(ints) == 100, len(ints)
        if hasattr(ints.data, 'nbytes'):  # python3 memoryview
            assert ints.data.nbytes == 200, ints.data.nbytes
        else:
            assert len(ints.data) == 200, len(ints.data)

    def test_randint(self):
        assert(quantumrandom.randint(0, 0) == 0)
        for i in range(5):
            for j in range(i + 1, 5):
                for k in range(3):
                    val = quantumrandom.randint(i, j)
                    assert(val >= i and val < j)

    @surrogate('cuse.cuse_api')
    @patch('cuse.cuse_api', new_callable=MockCuse)
    def test_dev(self, *args, **kw):
        global return_data
        from quantumrandom.dev import QuantumRandomDevice
        dev = QuantumRandomDevice(num_threads=3)
        dev.read(None, 10000, 0, None)
        self.assertEquals(len(return_data), 10000)
        dev.release(None, None)


if __name__ == '__main__':
    unittest.main()
