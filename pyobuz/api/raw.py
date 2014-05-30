'''
    pyobuz.api.raw
    ~~~~~~~~~~~~~~~~~~

    Our base api, all method are mapped like <endpoint>_<method>
    see Qobuz API on GitHub (https://github.com/Qobuz/api-documentation)

    :copyright: (c) 2012-2014 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
import sys
from time import time
import math
import hashlib
import socket

import requests

from pyobuz.exception import InvalidParameter, MissingParameter
from pyobuz.debug import warn, log

socket.timeout = 5


class QobuzApiRaw(object):

    def __init__(self):
        self.appid = "285473059"  # XBMC
        # self.appid = "214748364" # :]
        self.version = '0.2'
        self.baseUrl = 'http://www.pyobuz.com/api.json/'

        self.user_auth_token = None
        self.user_id = None
        self.error = None
        self.status_code = None
        self._baseUrl = self.baseUrl + self.version
        self.session = requests.Session()
        self.statContentSizeTotal = 0
        self.statTotalRequest = 0
        self.error = None
        self.__set_s4()

    def _serror(self, msg="", url="", params={}, json=""):
        import copy
        _copy_params = copy.deepcopy(params)
        if 'password' in _copy_params:
            _copy_params['password'] = '***'
        s = 'Something went wrong with request\n' + \
            '\t::message: %s\n' + \
            '\t::url    : %s\n' + \
            '\t::params : %s\n' + \
            '\t::json   : %s\n' + \
            "\t::error  : %s\n"
        s = s % (msg, url, _copy_params, json, self.error)
        return s

    def _check_ka(self, ka, mandatory, allowed=[]):
        """
        Checking parameters before sending our request
        - if mandatory parameter is missing raise error
        - if a given parameter is neither in mandatory or allowed
        raise error (Creating exception class like MissingParameter
        may be a good idea)
        """
        for label in mandatory:
            if not label in ka:
                raise MissingParameter(label)
        for label in ka:
            if label not in mandatory and label not in allowed:
                raise InvalidParameter(label)

    def __set_s4(self):
        """appid and associated secret is for this app usage only
        Any use of the API implies your full acceptance of the
        General Terms and Conditions
        (http://www.pyobuz.com/apps/api/QobuzAPI-TermsofUse.pdf)
        """
        import binascii
        from itertools import izip, cycle
        s3b = "Bg8HAA5XAFBYV15UAlVVBAZYCw0MVwcKUVRaVlpWUQ8="
        s3s = binascii.a2b_base64(s3b)
        self.s4 = ''.join(chr(ord(x) ^ ord(y))
                          for (x, y) in izip(s3s,
                                             cycle(self.appid)))

    def _api_request(self, params, uri, **opt):
        """Qobuz API HTTP get request
            Arguments:
            params:    parameters dictionary
            uri   :    service/method
            opt   :    Optionnal named parameters
                        - noToken=True/False

            Return None if something went wrong
            Return raw data from qobuz on success as dictionary

            * on error you can check error and status_code

            Example:

                ret = api._api_request({'username':'foo',
                                  'password':'bar'},
                                 'user/login', noToken=True)
                print 'Error: %s [%s]' % (api.error, api.status_code)

            This should produce something like:
            Error: [200]
            Error: Bad Request [400]
        """
        self.statTotalRequest += 1
        self.error = ''
        self.status_code = None
        url = self._baseUrl + uri
        useToken = False if (opt and 'noToken' in opt) else True
        headers = {}
        if useToken and self.user_auth_token:
            headers["x-user-auth-token"] = self.user_auth_token
        headers["x-app-id"] = self.appid
        r = None
        try:
            r = self.session.post(url, data=params, headers=headers)
        except:
            self.error = self._serror('Post error', url, params, None)
            return None
        self.status_code = r.status_code
        if int(r.status_code) != 200:
            if r.status_code == 400:
                self.error = "Bad request"
            elif r.status_code == 401:
                self.error = "Unauthorized"
            elif r.status_code == 402:
                self.error = "Request Failed"
            elif r.status_code == 404:
                self.error = "Not Found"
            else:
                self.error = "Server error"
            self.error = self._serror(self.error, url, params)
            return None
        if not r.content:
            self.error = self._serror("Request return no content", url, params)
            return None
        self.statContentSizeTotal += sys.getsizeof(r.content)
        """ Retry get if connexion fail """
        try:
            response_json = r.json()
        except Exception as e:
            warn(self, "Json loads failed to load... retrying!\n%s"
                 % (repr(e)))
            try:
                response_json = r.json()
            except:
                self.error = "Failed to load json two times...abort"
                warn(self, self.error)
                return 0
        status = None
        try:
            status = response_json['status']
        except:
            pass
        if status == 'error':
            self.error = self._serror(self.error, url, params, response_json)
            return None
        return response_json

    """
        This method is used when you are caching token and want to skip
        login
    """
    def set_user_data(self, user_id, user_auth_token):
        if not (user_id or user_auth_token):
            raise MissingParameter('uid|token')
        self.user_auth_token = user_auth_token
        self.user_id = user_id
        self.logged_on = time()

    """
        Erase user specific data
    """
    def logout(self):
        self.user_auth_token = None
        self.user_id = None
        self.logged_on = None

    def user_login(self, **ka):
        data = self._user_login(**ka)
        if data:
            self.set_user_data(data['user_auth_token'],
                               data['user']['id'])
            return data
        self.logout()
        return None

    '''
    User
    '''
    def _user_login(self, **ka):
        self._check_ka(ka, ['username', 'password'], ['email'])
        data = self._api_request(ka, '/user/login', noToken=True)
        if not data:
            return None
        if not 'user' in data:
            return None
        if not 'id' in data['user']:
            return None
        if not data['user']['id']:
            return None
        data['user']['email'] = ''
        data['user']['firstname'] = ''
        data['user']['lastname'] = ''
        return data

    def user_update(self, **ka):
        self._check_ka(ka, [], ['player_settings'])
        data = self._api_request(ka, '/user/update')
        return data

    '''
    Track
    '''
    def track_get(self, **ka):
        self._check_ka(ka, ['track_id'])
        data = self._api_request(ka, '/track/get')
        return data

    def track_getFileUrl(self, **ka):
        self._check_ka(ka, ['format_id', 'track_id'])
        ka['request_ts'] = time()
        params = {'format_id': str(ka['format_id']),
                  'intent': 'stream',
                  'request_ts': ka['request_ts'],
                  'request_sig': str(hashlib.md5("trackgetFileUrlformat_id"
                                                 + str(ka['format_id'])
                                                 + "intentstream"
                                                 + "track_id"
                                                 + str(ka['track_id'])
                                                 + str(ka['request_ts'])
                                                 + self.s4).hexdigest()),
                  'track_id': str(ka['track_id'])
                  }
        return self._api_request(params, '/track/getFileUrl')

    # MAPI UNTESTED
    def track_search(self, **ka):
        self._check_ka(ka, ['query'], ['limit'])
        data = self._api_request(ka, '/track/search')
        return data

    def track_resportStreamingStart(self, track_id):
        # Any use of the API implies your full acceptance
        # of the General Terms and Conditions
        # (http://www.pyobuz.com/apps/api/QobuzAPI-TermsofUse.pdf)
        params = {'user_id': self.user_id, 'track_id': track_id}
        return self._api_request(params, '/track/reportStreamingStart')

    def track_resportStreamingEnd(self, track_id, duration):
        duration = math.floor(int(duration))
        if duration < 5:
            log(self, 'Duration lesser than 5s, abort reporting')
            return None
        # @todo ???
#         user_auth_token = ''
        try:
            _user_auth_token = self.user_auth_token
        except:
            warn(self, 'No authentification token')
            return None
        params = {'user_id': self.user_id,
                  'track_id': track_id,
                  'duration': duration
                  }
        return self._api_request(params, '/track/reportStreamingEnd')

    '''
    Album
    '''
    def album_get(self, **ka):
        self._check_ka(ka, ['album_id'])
        return self._api_request(ka, '/album/get')

    def album_getFeatured(self, **ka):
        self._check_ka(ka, [], ['type', 'genre_id', 'limit', 'offset'])
        return self._api_request(ka, '/album/getFeatured')

    '''
    Purchase
    '''
    def purchase_getUserPurchases(self, **ka):
        self._check_ka(ka, [], ['order_id', 'order_line_id', 'flat', 'limit',
                                'offset'])
        return self._api_request(ka, "/purchase/getUserPurchases")

    # SEARCH #
    def search_getResults(self, **ka):
        self._check_ka(ka, ['query'], ['type', 'limit', 'offset'])
        mandatory = ['query', 'type']
        for label in mandatory:
            if not label in ka:
                raise MissingParameter(label)
        return self._api_request(ka, '/search/getResults')

    """
        Favorite
    """
    def favorite_getUserFavorites(self, **ka):
        self._check_ka(ka, [], ['user_id', 'type', 'limit', 'offset'])
        return self._api_request(ka, '/favorite/getUserFavorites')

    def favorite_create(self, **ka):
        mandatory = ['artist_ids', 'album_ids', 'track_ids']
        found = None
        for label in mandatory:
            if label in ka:
                found = label
        if not found:
            raise MissingParameter('artist_ids|albums_ids|track_ids')
        return self._api_request(ka, '/favorite/create')

    def favorite_delete(self, **ka):
        mandatory = ['artist_ids', 'album_ids', 'track_ids']
        found = None
        for label in mandatory:
            if label in ka:
                found = label
        if not found:
            raise MissingParameter('artist_ids|albums_ids|track_ids')
        return self._api_request(ka, '/favorite/delete')

    """
    Playlist
    """
    def playlist_get(self, **ka):
        self._check_ka(ka, ['playlist_id'], ['extra', 'limit', 'offset'])
        return self._api_request(ka, '/playlist/get')

    def playlist_getUserPlaylists(self, **ka):
        self._check_ka(ka, [], ['user_id', 'username', 'offset', 'limit'])
        if not 'user_id' in ka and not 'username' in ka:
            ka['user_id'] = self.user_id
        data = self._api_request(ka, '/playlist/getUserPlaylists')
        return data

    def playlist_addTracks(self, **ka):
        self._check_ka(ka, ['playlist_id', 'track_ids'])
        return self._api_request(ka, '/playlist/addTracks')

    def playlist_deleteTracks(self, **ka):
        self._check_ka(ka, ['playlist_id'], ['playlist_track_ids'])
        return self._api_request(ka, '/playlist/deleteTracks')

    def playlist_subscribe(self, **ka):
        mandatory = ['playlist_id']
        found = None
        for label in mandatory:
            if label in ka:
                found = label
        if not found:
            raise MissingParameter('playlist_id')
        return self._api_request(ka, '/playlist/subscribe')

    def playlist_unsubscribe(self, **ka):
        self._check_ka(ka, ['playlist_id'])
        return self._api_request(ka, '/playlist/unsubscribe')

    def playlist_create(self, **ka):
        self._check_ka(ka, ['name'], ['is_public',
                       'is_collaborative', 'tracks_id', 'album_id'])
        if not 'is_public' in ka:
            ka['is_public'] = True
        if not 'is_collaborative' in ka:
            ka['is_collaborative'] = False
        return self._api_request(ka, '/playlist/create')

    def playlist_delete(self, **ka):
        self._check_ka(ka, ['playlist_id'])
        if not 'playlist_id' in ka:
            raise MissingParameter('playlist_id')
        return self._api_request(ka, '/playlist/delete')

    def playlist_update(self, **ka):
        self._check_ka(ka, ['playlist_id'], ['name', 'description',
                       'is_public', 'is_collaborative', 'tracks_id'])
        res = self._api_request(ka, '/playlist/update')
        return res

    def playlist_getPublicPlaylists(self, **ka):
        self._check_ka(ka, '', ['type', 'limit', 'offset'])
        res = self._api_request(ka, '/playlist/getPublicPlaylists')
        return res
    """
        Artist
    """
    def artist_getSimilarArtists(self, **ka):
        self._check_ka(ka, ['artist_id', 'limit', 'offset'])
        return self._api_request(ka, '/artist/getSimilarArtists')

    def artist_get(self, **ka):
        self._check_ka(ka, ['artist_id'], ['extra', 'limit', 'offset'])
        data = self._api_request(ka, '/artist/get')
        return data

    """
        Genre
    """
    def genre_list(self, **ka):
        self._check_ka(ka, [], ['parent_id', 'limit', 'offset'])
        return self._api_request(ka, '/genre/list')

    """
        Label
    """
    def label_list(self, **ka):
        self._check_ka(ka, [], ['limit', 'offset'])
        return self._api_request(ka, '/label/list')

    """
        Article
    """
    def article_listRubrics(self, **ka):
        self._check_ka(ka, [], ['extra', 'limit', 'offset'])
        return self._api_request(ka, '/article/listRubrics')

    def article_listLastArticles(self, **ka):
        self._check_ka(ka, [], ['rubric_ids', 'offset', 'limit'])
        return self._api_request(ka, '/article/listLastArticles')

    def article_get(self, **ka):
        self._check_ka(ka, ['article_id'])
        return self._api_request(ka, '/article/get')

    """
        Collection
    """
    def collection_getAlbums(self, **ka):
        self._check_ka(ka, [], ['source', 'artist_id', 'query',
                                'limit', 'offset'])
        return self._api_request(ka, '/collection/getAlbums')

    def collection_getArtists(self, **ka):
        self._check_ka(ka, [], ['source', 'query',
                                'limit', 'offset'])
        return self._api_request(ka, '/collection/getArtists')

    def collection_getTracks(self, **ka):
        self._check_ka(ka, [], ['source', 'artist_id', 'album_id', 'query',
                                'limit', 'offset'])
        return self._api_request(ka, '/collection/getTracks')
