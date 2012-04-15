import unittest
import quantumrandom

class TestQuantumRandom(unittest.TestCase):

    def test_binary(self):
        binary = quantumrandom.binary()
        assert type(binary) is str

    def test_hex(self):
        hex = quantumrandom.hex()
        assert type(hex) is str

    def test_char(self):
        char = quantumrandom.char()
        assert type(char) is str

if __name__ == '__main__':
    unittest.main()
