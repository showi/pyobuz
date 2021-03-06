'''
    pyobuz.renderer.list
    ~~~~~~~~~~~~~~~~~~~~

    This file is part of pyobuz

    :copyright: (c) 2012-2014 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from base import BaseRenderer


class ListRenderer(BaseRenderer):

    def __init__(self):
        self.alive = False
        self.depth = 1
        self.whiteFlag = None
        self.blackFlag = None

    def render(self, node):
        self.clear()
        node.populating(self)
        self.end()

    def ask(self):
        pass

    def end(self):
        pass
