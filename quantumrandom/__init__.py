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
A Python interface to the ANU Quantum Random Numbers Server.

http://physics0054.anu.edu.au
"""

import json
import urllib
import urllib2
import warnings

from BeautifulSoup import BeautifulSoup

IP = '150.203.48.55'
JSON_API = 'http://%s/API/jsonI.php' % IP
DATA_TYPES = ['uint16', 'hex16']
MAX_LEN = 100


def get_data(data_type='uint16', array_length=1, block_size=1):
    """Fetch data from the ANU Quantum Random Numbers JSON API"""
    if data_type not in DATA_TYPES:
        raise Exception("data_type must be one of %s" % DATA_TYPES)
    if array_length > MAX_LEN:
        raise Exception("array_length cannot be larger than %s" % MAX_LEN)
    req = JSON_API + '?' + urllib.urlencode({
        'type': data_type,
        'length': array_length,
        'size': block_size,
        })
    return json.loads(urllib2.urlopen(req).read())


##
## Deprecated scraper functions.
##

def _get_block(kind='RawChar'):
    warnings.warn('The quantumrandom.{binary,hex,char} functions are '
                  'deprecated. Please use quantumrandom.get_data instead.')
    url = 'http://%s/%s.php' % (IP, kind)
    html = BeautifulSoup(urllib2.urlopen(url).read())
    return html.find('table', {'class': 'rng'}).td.text.encode('ascii')


def binary():
    """ Return a string of 1024 random bits """
    block = _get_block('RawBin')
    assert len(block) == 1024, len(block)
    for b in block:
        assert b in ('0', '1'), b
    return block


def char():
    """ Return 1024 random alphanumeric (and underscore) characters """
    block = _get_block('RawChar')
    assert len(block) == 1024, len(block)
    for c in block:
        assert c.lower() in 'abcdefghijklmnopqrstuvwxyz0123456789_', c
    return block


def hex():
    """ Return a string of 1024 bytes of randomness in hexadecimal form """
    block = _get_block('RawHex')
    assert len(block) == 2048, len(block)
    for h in block:
        assert h in '0123456789abcdef', h
    return block
