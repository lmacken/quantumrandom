import unittest
import quantumrandom

class TestQuantumRandom(unittest.TestCase):

    def test_uint16_json_api(self):
        data = quantumrandom.get_data('uint16', 1, 1)
        assert data['success']
        assert int(data['length']) == 1
        assert data['type'] == 'uint16'
        assert len(data['data']) == 1

    def test_hex16_json_api(self):
        data = quantumrandom.get_data('hex16', 1, 1)
        assert data['success']
        assert int(data['length']) == 1
        assert data['type'] == 'string'
        assert len(data['data']) == 1
        assert int(data['size']) == 1


if __name__ == '__main__':
    unittest.main()
