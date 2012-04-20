import unittest
import quantumrandom


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
            data = quantumrandom.get_data('uint16', 101, 1)
            assert False, "Invalid array length didn't cause error: %s" % data
        except:
            pass

    def test_uint16_json_api_large_blocksize(self):
        try:
            data = quantumrandom.get_data('uint16', 1, 101)
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
        assert len(ints) == 100
        assert len(ints.data) == 200

    def test_randint(self):
        val = quantumrandom.randint(0, 10)
        assert(val >= 0 and val < 10)
        val = quantumrandom.randint(0, 1)
        assert(val == 0)


if __name__ == '__main__':
    unittest.main()
