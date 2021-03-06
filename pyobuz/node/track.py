'''
    pyobuz.node.track
    ~~~~~~~~~~~~~~~~~

    This file is part of pyobuz

    :copyright: (c) 2012-2014 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from pyobuz.node.ibase import Mode
from pyobuz.node import Flag
from inode import INode
from pyobuz.debug import warn
from pyobuz.api import api
from pyobuz.settings import settings
from pyobuz.i8n import _
from pyobuz.exception import  ErrorNoData


class Node_track(INode):
    '''
        NODE TRACK
    '''
    def __init__(self, parameters={}):
        super(Node_track, self).__init__(parameters)
        self.kind = Flag.TRACK
        self.is_folder = False
        self.content_type = 'songs'
        self.qobuz_context_type = 'playlist'
        self.status = None
        self.add_action('list',
                        label=_('Similar artists'),
                        target=Flag.ARTIST_SIMILAR)
        self.add_action('featured',
                        label=_('Featured album'),
                        target=Flag.ALBUMS_BY_ARTIST)

    def fetch(self, renderer=None):
        data = api.get('/track/get', track_id=self.nid)
        if not data:
            return False
        self.data = data
        return True

    def populate(self, renderer=None):
        return True

    def url(self, **ka):
        if not 'mode' in ka:
            ka['mode'] = Mode.PLAY
        return super(Node_track, self).url(**ka)

    def get_label(self, sFormat="%a - %t"):
        sFormat = sFormat.replace("%a", self.get_artist())
        sFormat = sFormat.replace("%t", self.get_title())
        sFormat = sFormat.replace("%A", self.get_album())
        sFormat = sFormat.replace("%n", str(self.get_track_number()))
        sFormat = sFormat.replace("%g", self.get_genre())
        return sFormat

    def get_composer(self):
        try:
            return self.get_property('composer/name')
        except:
            return -1

    def get_interpreter(self):
        try:
            return self.get_property('performer/name')
        except:
            return -1

    def get_album(self):
        try:
            album = self.get_property('album/title')
        except:
            return -1
        if album:
            return album
        if not self.parent:
            return ''
        if self.parent.kind & Flag.ALBUM:
            return self.parent.get_title()
        return ''

    def get_album_id(self):
        aid = self.get_property('album/id')
        if not aid and self.parent:
            return self.parent.nid
        return aid

    def get_image(self):
        image = self.get_property(['album/image/large', 'image/large',
                                      'image/small',
                                      'image/thumbnail', 'image'])
        if image:
            return image.replace('_230.', '_600.')
        if not self.parent:
            return self.image
        if self.parent.nt & (Flag.ALBUM | Flag.PLAYLIST):
            return self.parent.get_image()

    def get_playlist_track_id(self):
        return self.get_property('playlist_track_id')

    def get_position(self):
        return self.get_property('position')

    def get_title(self):
        return self.get_property('title')

    def get_genre(self):
        genre = self.get_property('album/genre/name')
        if genre:
            return genre
        if not self.parent:
            return ''
        if self.parent.kind & Flag.ALBUM:
            return self.parent.get_genre()
        return ''

    def get_streaming_url(self):
        data = self.__getFileUrl()
        if not data:
            return False
        restrictions = self.get_restrictions()
        for restriction in restrictions:
            print "Restriction: %s" % (restriction)
        if not 'url' in data:
            warn(self, "streaming_url, no url returned\n"
                "API Error: %s" % (api.error))
            return None
        return data['url']

    def get_artist(self):
        return self.get_property(['artist/name',
                               'composer/name',
                               'performer/name',
                               'interpreter/name',
                               'composer/name',
                               'album/artist/name'])

    def get_artist_id(self):
        s = self.get_property(['artist/id',
                               'composer/id',
                               'performer/id',
                               'interpreter/id'])
        if s:
            return int(s)
        return None

    def get_track_number(self):
        return self.get_property('track_number')

    def get_media_number(self):
        return self.get_property('media_number')

    def get_duration(self):
        duration = self.get_property('duration')
        if duration and int(duration) != 0:
            return duration
        else:
            return -1

    def get_year(self):
        import time
        try:
            date = self.get_property('album/released_at')
            if not date and self.parent and self.parent.nt & Flag.ALBUM:
                return self.parent.get_year()
        except:
            pass
        year = 0
        try:
            year = time.strftime("%Y", time.localtime(date))
        except:
            pass
        return year

    @property
    def is_playable(self):
        return True

    @is_playable.getter
    def is_playable(self):
        url = self.get_streaming_url()
        if not url:
            return False
        restrictions = self.get_restrictions()
        if 'TrackUnavailable' in restrictions:
            return False
        if 'AlbumUnavailable' in restrictions:
            return False
        return True

    @is_playable.setter
    def is_playable(self, v):
        pass

    def get_description(self):
        return ''  # Recursion bug ...
        if self.parent:
            return self.parent.get_description()
        return ''

    def __getFileUrl(self):
        format_id = settings['stream_format']
        data = api.get('/track/getFileUrl', format_id=format_id,
                           track_id=self.nid, user_id=api.user_id)
        if not data:
            warn(self, "Cannot get stream type for track (network problem?)")
            return None
        return data

    def get_restrictions(self):
        data = self.__getFileUrl()
        if not data:
            raise ErrorNoData('Cannot get track restrictions')
        restrictions = []
        if not 'restrictions' in data:
            return restrictions
        for restriction in data['restrictions']:
            restrictions.append(restriction['code'])
        return restrictions

    def is_sample(self):
        data = self.__getFileUrl()
        if not data:
            return False
        if 'sample' in data:
            return data['sample']
        return False

    def get_mimetype(self):
        data = self.__getFileUrl()
        if not data:
            return False
        if not 'format_id' in data:
            warn(self, "Cannot get mime/type for track (restricted track?)")
            return False
        formatId = int(data['format_id'])
        mime = ''
        if formatId == 6:
            mime = 'audio/flac'
        elif formatId == 5:
            mime = 'audio/mpeg'
        else:
            warn(self, "Unknow format " + str(formatId))
            mime = 'audio/mpeg'
        return mime

    def item_add_playing_property(self, item):
        """ We add this information only when playing item because it require
            us to fetch data from Qobuz
        """
        mime = self.get_mimetype()
        if not mime:
            warn(self, "Cannot set item streaming url")
            return False
        item.setProperty('mimetype', mime)
        item.setPath(self.get_streaming_url())
        return True
