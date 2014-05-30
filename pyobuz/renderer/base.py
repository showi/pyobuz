'''
    node.renderer.base
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This file is part of pyobuz

    :copyright: (c) 2012-2014 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from collections import deque

class BaseRenderer(deque):

    def __init__(self):
        self.alive = False
        self.depth = 1
        self.whiteFlag = None
        self.blackFlag = None

    def render(self, plugin, node):
        raise NotImplemented()

    def ask(self):
        raise NotImplemented()

    def end(self):
        raise NotImplemented()
