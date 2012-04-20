# Copyright (c) 2012 Luke Macken <lmacken@redhat.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
A tool for printing random data from the ANU Quantum Random Number Generator
"""

import sys
import quantumrandom

def main():
    usage = "Usage: %s [--binary|--hex|--int --min MIN --max MAX]" % \
            sys.argv[0]
    generator = None
    # TODO -- use argparse here
    if '--binary' in sys.argv or '-b' in sys.argv:
        generator = quantumrandom.binary
    if '--hex' in sys.argv or '-h' in sys.argv:
        generator = quantumrandom.hex
    if '--int' in sys.argv or '-i' in sys.argv:
        # Special case.  Just print one.
        try:
            min = int(sys.argv[sys.argv.index('--min')+1])
            max = int(sys.argv[sys.argv.index('--max')+1])
        except ValueError:
            print usage
            sys.exit(1)

        print quantumrandom.randint(min=min, max=max)
        sys.exit(0)

    if not generator:
        print usage
        sys.exit(1)
    try:
        while True:
            print generator(),
    except:
        pass


if __name__ == '__main__':
    main()
