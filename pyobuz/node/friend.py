'''
    pyobuz.node.friend
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This file is part of pyobuz

    :copyright: (c) 2012-2014 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''

import json

from inode import INode
from pyobuz.debug import warn
from pyobuz.api import api
from pyobuz.cache import cache
from pyobuz.node import Flag, getNode


class Node_friend(INode):
    '''
    @class Node_friend:
    '''

    def __init__(self, parameters={}):
        super(Node_friend, self).__init__(parameters)
        self.kind = Flag.FRIEND
        self.image = ''
        self.name = self.get_parameter('query', delete=True)

    def set_label(self, label):
        self.label = label

    @property
    def name(self):
        return self._name

    @name.getter
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name or ''
        self.label = self.name

    def url(self, **ka):
        ka['query'] = self.name
        return super(Node_friend, self).url(**ka)

    def create(self, name=None):
        username = api.username
        password = api.password
        friendpl = api.get('/playlist/getUserPlaylists', username=name)
        if not friendpl:
            return False
        user = api.get('/user/login', username=username, password=password)
        if user['user']['login'] == name:
            return False
        if not user:
            return False
        friends = user['user']['player_settings']
        if not 'friends' in friends:
            friends = []
        else:
            friends = friends['friends']
        if name in friends:
            return False
        friends.append(name)
        newdata = {'friends': friends}
        if not api.user_update(player_settings=json.dumps(newdata)):
            return False
        return True

    def delete_cache(self):
        key = cache.make_key('/user/login', username=api.username,
                             password=api.password)
        cache.delete(key)

    def populate(self, renderer=None):
        data = api.get('/playlist/getUserPlaylists', username=self.name)
        if not data:
            warn(self, "No friend data")
            return False
#         if depth != -1:
#             self.append(getNode(Flag.FRIEND_LIST, self.parameters))
        for pl in data['playlists']['items']:
            node = getNode(Flag.PLAYLIST, self.parameters)
            node.data = pl
            if node.get_owner() == self.label:
                self.nid = node.get_owner_id()
            self.append(node)
        return True
