import unittest
import quantumrandom

class TestQuantumRandom(unittest.TestCase):

    def test_binary(self):
        binary = quantumrandom.binary()
        assert len(binary) == 1024
        for b in binary:
            assert b in ('0', '1'), b

    def test_hex(self):
        hex = quantumrandom.hex()
        assert len(hex) == 2048
        for h in hex:
            assert h in '0123456789abcdef', h

    def test_char(self):
        char = quantumrandom.char()
        assert len(char) == 1024
        for c in char:
            assert c.lower() in 'abcdefghijklmnopqrstuvwxyz0123456789_', c


if __name__ == '__main__':
    unittest.main()
