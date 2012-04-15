# Copyright (c) 2012 Luke Macken <lmacken@redhat.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
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
A Python interface to the ANU Quantum Random Numbers Server.

http://physics0054.anu.edu.au
"""

import urllib2
from BeautifulSoup import BeautifulSoup

url = 'http://150.203.48.55/%s.php'

def _get_block(kind='RawChar'):
    html = BeautifulSoup(urllib2.urlopen(url % kind).read())
    return html.find('table', {'class': 'rng'}).td.text.encode('ascii')

def binary():
    """ Return a string of 1024 random bits """
    return _get_block('RawBin')

def char():
    """ Return 1024 random alphanumeric (and underscore) characters """
    return _get_block('RawChar')

def hex():
    """ Return a string of 1024 bytes of randomness in hexadecimal form """
    return _get_block('RawHex')
