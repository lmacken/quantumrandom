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

import urllib
import urllib2
try:
    import json
except ImportError:
    import simplejson as json

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
    if block_size > MAX_LEN:
        raise Exception("block_size cannot be larger than %s" % MAX_LEN)
    req = JSON_API + '?' + urllib.urlencode({
        'type': data_type,
        'length': array_length,
        'size': block_size,
        })
    data = json.loads(urllib2.urlopen(req).read(), object_hook=_object_hook)
    assert data['success'] is True, data
    assert data['length'] == array_length, data
    return data['data']


def _object_hook(obj):
    """We are only dealing with ASCII characters"""
    if obj.get('type') == 'string':
        obj['data'] = [s.encode('ascii') for s in obj['data']]
    return obj


__all__ = ['get_data']
