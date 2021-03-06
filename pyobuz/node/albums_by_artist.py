'''
    pyobuz.node.albums_by_artist
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This file is part of pyobuz

    :copyright: (c) 2012-2014 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from inode import INode
from pyobuz.debug import warn
import weakref
from pyobuz.api import api
from pyobuz.node import getNode, Flag


class Node_albums_by_artist(INode):
    '''
        @class Node_product_by_artist:
    '''

    def __init__(self, parameters={}):
        super(Node_albums_by_artist, self).__init__(parameters)
        self.kind = Flag.ALBUMS_BY_ARTIST
        self.content_type = 'albums'
        self.items_path = 'albums'

    def get_label(self):
        '''
        Getter
        '''
        return self.get_artist()

    def get_image(self):
        image = self.get_property('picture')
        # get max size image from lastfm, Qobuz default is a crappy 126p large
        # one perhaps we need a setting for low bw users
        image = image.replace('126s', '_')
        return image

    def get_artist(self):
        return self.get_property('name')

    def get_slug(self):
        return self.get_property('slug')

    def get_artist_id(self):
        return self.nid

    def fetch(self, renderer=None):
        data = api.get('/artist/get', artist_id=self.nid,
                       limit=api.pagination_limit, offset=self.offset,
                       extra='albums')
        print "DATA %s" % data
        if not data:
            warn(self, "Cannot fetch albums for artist: " + self.get_label())
            return False
        self.data = data
        return True

    def populating(self, renderer=None):
        count = 0
        items = self.data[self.items_path]['items']
        for album in items:
            print "Album %s" % album
            keys = ['artist', 'interpreter', 'composer', 'performer']
            for k in keys:
                try:
                    if k in self.data['artist']:
                        album[k] = weakref.proxy(self.data['artist'][k])
                except:
                    warn(self, "Strange thing happen")
                    pass
            node = getNode(Flag.ALBUM, {})
            node.data = album
            count += 1
            self.append(node)
        return True
