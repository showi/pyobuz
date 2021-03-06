'''
    pyobuz.node.favorites
    ~~~~~~~~~~~~~~~~~~~~~

    This file is part of pyobuz

    :copyright: (c) 2012-2014 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''

from inode import INode
from pyobuz.node import getNode, Flag
from pyobuz.i8n import _


class Node_favorites(INode):

    def __init__(self, parameters={}):
        super(Node_favorites, self).__init__(parameters)
        self.kind = Flag.FAVORITES
        self.label = _('Favorites')
        self.content_type = 'files'

    def populate(self, renderer=None):
        for ftype in ['albums', 'tracks', 'artists']:
            node = getNode(Flag.FAVORITE, self.parameters)
            node.items_path = ftype
            self.append(node)
        return True
