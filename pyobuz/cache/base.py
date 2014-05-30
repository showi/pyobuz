'''
    pyobuz.storage.base
    ~~~~~~~~~~~~~~~~~~

    A class to handle caching

    ::cached decorator that will cache a function call based on his
    positional and named parameter

    :copyright: (c) 2012-2014 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from time import time
__seed__ = __name__ + '0.0.1'
__magic__ = 0
pos = 0
for i in [ord(c) for c in __seed__[:]]:
    __magic__ += i * 2 ** pos
    pos += 1
BadMagic = 1 << 1
BadKey = 1 << 2
NoData = 1 << 3
StoreError = 1 << 4
DeleteError = 1 << 5

from pyobuz.exception import QobuzException


class BadMagicError(QobuzException):
    pass


class CacheBase(object):
    ''' A base class for caching
    '''
    def __init__(self, *a, **ka):
        self.enable = False
        self.cached_function_name = __name__

    def cached(self, f, *a, **ka):
        '''Decorator
            All positional and named parameters are used to make the key
        '''
        that = self
        self.cached_function_name = f.__name__

        def wrapped_function(self, *a, **ka):
            if not that.enable:
                return f(self, *a, **ka)
            that.error = 0
            key = that.make_key(*a, **ka)
            data = that.load(key, *a, **ka)
            if data:
                if not that.check_magic(data, *a, **ka):
                    that.error &= BadMagic
                elif not that.check_key(data, key, *a, **ka):
                    that.error &= BadKey
                elif that.is_fresh(key, data, *a, **ka):
                    return data['data']
                if not that.delete(key):
                    that.error = DeleteError
            data = f(self, *a, **ka)
            if data is None:
                that.error &= NoData
                return None
            for black_key in that.black_keys:
                if black_key in ka:
                    del ka[black_key]
            entry = {
                 'updated_on': time(),
                 'data': data,
                 'ttl': int(that.get_ttl(key, *a, **ka)),
                 'pa': a,
                 'ka': ka,
                 'magic': __magic__,
                 'key': key
            }
            if not that.sync(key, entry):
                that.error &= StoreError
            return data
        return wrapped_function

    def is_fresh(self, key, data, *a, **ka):
        if not 'updated_on' in data:
            return False
        updated_on = data['updated_on']
        ttl = data['ttl']
        if ttl == 0:
            return -1
        diff = (updated_on + ttl) - time()
        if diff <= 0:
            return 0
        return diff

    def check_magic(self, data, *a, **ka):
        if not data:
            return False
        if not 'magic' in data:
            return False
        if data['magic'] != __magic__:
            return False
        return True

    def check_key(self, data, key, *a, **ka):
        if not 'key' in data:
            return False
        if data['key'] != key:
            return False
        return True

    def load(self, key, *a, **ka):
        ''' return tuple (Status, Data)
            Status: Bool
            Data: Arbitrary data
        '''
        raise NotImplemented()

    def load_from_store(self, *a, **ka):
        raise NotImplemented()

    def sync(self, key, data, *a, **ka):
        raise NotImplemented()

    def delete(self, key, *a, **ka):
        raise NotImplemented()

    def make_key(self, key, *a, **ka):
        raise NotImplemented()

    def get_ttl(self, key, *a, **ka):
        raise NotImplemented
