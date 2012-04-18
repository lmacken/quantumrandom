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

    def test_uint16_json_api_invalid_type(self):
        try:
            data = quantumrandom.get_data('binary', 1, 1)
            assert False, "Invalid type didn't throw exception: %s" % data
        except:
            pass

    def test_ensure_bytestrings(self):
        data = quantumrandom.get_data('hex16', 1, 1)
        assert type(data[0]) is str, data

if __name__ == '__main__':
    unittest.main()
