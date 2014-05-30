'''
    pyobuz.exception
    ~~~~~~~~~~~~~~~~

    This file is part of pyobuz

    :copyright: (c) 2012-2014 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''


class QobuzException(Exception):
    pass


class InvalidParameter(QobuzException):
    pass


class MissingParameter(QobuzException):
    pass


class InvalidType(QobuzException):
    pass


class ErrorNoData(Exception):
    pass


class InvalidQuery(Exception):
    pass
