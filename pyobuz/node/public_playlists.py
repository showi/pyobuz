'''
    pyobuz.node.public_playlists
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This file is part of pyobuz

    :copyright: (c) 2012-2014 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from inode import INode
from pyobuz.node import Flag, getNode
from pyobuz.api import api
from pyobuz.i8n import _


class Node_public_playlists(INode):

    def __init__(self, parameters={}):
        super(Node_public_playlists, self).__init__(parameters)
        self.kind = Flag.PUBLIC_PLAYLISTS
        self.label = _('Public playlists')
        self.items_path = 'playlists'

    def fetch(self, renderer=None):
        data = api.get('/playlist/getPublicPlaylists', offset=self.offset,
                       limit=api.pagination_limit, type='last-created')
        if not data:
            return False
        # @bug: we use pagination_limit as limit for the search so we don't
        # need offset... (Fixed if qobuz fix it :p)
        if not 'total' in data[self.items_path]:
            data[self.items_path]['total'] = data[self.items_path]['limit']
        self.data = data
        return True

    def populate(self, renderer=None):
        for item in self.data[self.items_path]['items']:
            node = getNode(Flag.PLAYLIST, self.parameters)
            node.data = item
            self.append(node)
        return True
