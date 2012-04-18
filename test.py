import unittest
import quantumrandom

class TestQuantumRandom(unittest.TestCase):

    def test_uint16_json_api(self):
        data = quantumrandom.get_data('uint16', 1, 1)
        assert data['success']
        assert data['length'] == 1
        assert data['type'] == 'uint16'
        assert len(data['data']) == 1

    def test_uint16_json_api_max_array(self):
        data = quantumrandom.get_data('uint16', 100, 100)
        assert data['success']
        assert data['length'] == 100
        assert data['type'] == 'uint16'
        assert len(data['data']) == 100

    def test_hex16_json_api(self):
        data = quantumrandom.get_data('hex16', 1, 1)
        assert data['success']
        assert data['length'] == 1
        assert data['type'] == 'string'
        assert len(data['data']) == 1
        assert data['size'] == 1

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


if __name__ == '__main__':
    unittest.main()
