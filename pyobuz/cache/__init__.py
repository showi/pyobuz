'''
    pyobuz.cache
    ~~~~~~~~~~~~

    Package that set our default cache

    This file is part of pyobuz

    :copyright: (c) 2012-2014 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
__all__ = ['cache']

from ttl import CacheFileTTL
cache = CacheFileTTL()
