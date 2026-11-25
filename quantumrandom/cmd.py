# Copyright (c) 2012-2013 Luke Macken <lmacken@redhat.com>
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

import argparse
import itertools
import os
import sys

import quantumrandom


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog='qrandom',
        description="Print random data from the ANU Quantum Random Number "
                    "Generator.",
        epilog="An API key is required. Create a free one at "
               "https://quantumnumbers.anu.edu.au and export it as %s. "
               "Each block of --hex or --binary output costs one API request, "
               "while --int gets thousands of numbers out of each request."
               % quantumrandom.API_KEY_ENV)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('-i', '--int', action='store_true',
                      help="print an integer between --min and --max, "
                           "inclusive")
    mode.add_argument('-x', '--hex', action='store_true',
                      help="print blocks of 40960 hex characters")
    mode.add_argument('-b', '--binary', action='store_true',
                      help="write blocks of 20480 raw bytes")
    parser.add_argument('--min', type=int, default=0,
                        help="smallest integer to print with --int "
                             "(default: %(default)s)")
    parser.add_argument('--max', type=int, default=10,
                        help="largest integer to print with --int "
                             "(default: %(default)s)")
    parser.add_argument('-c', '--count', type=int, default=1, metavar='N',
                        help="how many integers or blocks to output, or 0 to "
                             "keep going until interrupted "
                             "(default: %(default)s)")
    parser.add_argument('-k', '--api-key', metavar='KEY',
                        help="API key to use instead of $%s. Note that other "
                             "users on this machine can see command-line "
                             "arguments." % quantumrandom.API_KEY_ENV)
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + quantumrandom.VERSION)
    args = parser.parse_args(argv)
    if args.count < 0:
        parser.error("--count cannot be negative")
    if args.max < args.min:
        parser.error("--max cannot be less than --min")
    return args


def main(argv=None):
    args = parse_args(argv)
    if args.api_key:
        quantumrandom.set_api_key(args.api_key)
    try:
        for _ in range(args.count) if args.count else itertools.count():
            if args.int:
                print(quantumrandom.randint(args.min, args.max))
            elif args.hex:
                print(quantumrandom.hex())
            else:
                sys.stdout.buffer.write(quantumrandom.binary())
            sys.stdout.flush()
    except quantumrandom.QuantumRandomError as e:
        sys.stderr.write("qrandom: %s\n" % e)
        return 1
    except KeyboardInterrupt:
        return 130
    except BrokenPipeError:
        # Whatever we were piped into stopped reading. Point stdout at
        # /dev/null so that the interpreter does not complain about not being
        # able to flush it on the way out.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
