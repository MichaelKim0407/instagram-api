import math
import time

import copy
import json
import logging
import os
import requests
import urllib
import urllib.parse
from datetime import datetime
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests_toolbelt import MultipartEncoder

from . import constant
from . import util
from .ImageUtils import get_image_size
from .exceptions import *

try:
    from moviepy.editor import VideoFileClip
except ImportError:
    logging.warning("Fail to import moviepy. Need only for Video upload.")

# Turn off InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger('mk_instagram_api.api')


class endpoint(object):
    def __init__(self, uri):
        self.uri = uri

    def __call__(self, method):
        return method


class get(endpoint):
    def __init__(self, uri, ranked=False):
        super().__init__(uri)
        self.ranked = ranked

    def __call__(self, method):
        def __new_method(_self: 'InstagramAPI', *args, **kwargs):
            result = method(_self, *args, **kwargs)
            if not isinstance(result, tuple):
                uri_params, params = result, None
            else:
                uri_params, params = result

            uri = self.uri
            if uri_params:
                uri = self.uri.format(**uri_params)

            if not params:
                params = {}
            if self.ranked:
                params.update({
                    'ranked_content': 'true',
                    'rank_token': _self.rank_token,
                })

            if params:
                uri += '?'
                for key, val in params.items():
                    if val is None:
                        continue
                    uri += '{}={}&'.format(key, val)

            return _self.send_request(uri)

        return __new_method


class post(endpoint):
    def __call__(self, method):
        def __new_method(_self: 'InstagramAPI', *args, **kwargs):
            result = method(_self, *args, **kwargs)
            if not isinstance(result, tuple):
                uri_params = data = result
            else:
                uri_params, data = result

            uri = self.uri
            if uri_params:
                uri = self.uri.format(**uri_params)

            if not data:
                data = {}
            data.update({
                '_uuid': _self.uuid,
                '_uid': _self.user_id,
                '_csrftoken': _self.token,
            })

            return _self.send_request(
                uri,
                util.generate_signature(json.dumps(data))
            )

        return __new_method


class _BaseAPI(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.device_id = self.__generate_device_id()
        self.uuid = util.generate_uuid()

        self.is_logged_in = False
        self.user_id = None

        self.session = requests.Session()
        self.last_response = None
        self.rank_token = None
        self.token = None

        self.retry = True
        self.retry_times = 3
        self.retry_interval = 5  # seconds

    def __generate_device_id(self):
        return util.generate_device_id(
            util.md5_hash(self.username.encode('utf-8') + self.password.encode('utf-8'))
        )

    def __generate_rank_token(self):
        return "{}_{}".format(
            self.user_id,
            self.uuid
        )

    def __handle_response(self, response):
        if response.status_code == 200:
            self.last_response = response
            return json.loads(response.text)

        try:
            # check for sentry block
            result = json.loads(response.text)
            if 'error_type' in result and result['error_type'] == 'sentry_block':
                raise SentryBlockError(result['message'])
        except SentryBlockError:
            raise
        except Exception:
            pass

        raise ResponseError(response.status_code, response)

    def configure_retry(self, retry=None, retry_times=None, retry_interval=None):
        if retry is not None:
            self.retry = bool(retry)
        if retry_times is not None:
            self.retry_times = retry_times
        if retry_interval is not None:
            self.retry_interval = retry_interval

    def set_proxy(self, proxy=None):
        """
        Set proxy for all requests::

        Proxy format - user:password@ip:port
        """
        if proxy is not None:
            logger.info('Set proxy!')
            proxies = {
                'http': proxy,
                'https': proxy,
            }
            self.session.proxies.update(proxies)

    def send_request(self, endpoint, data=None, login=False):
        verify = False  # don't show request warning

        if not self.is_logged_in and not login:
            raise RequireLogin()

        self.session.headers.update({
            'Connection': 'close',
            'Accept': '*/*',
            'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie2': '$Version=1',
            'Accept-Language': 'en-US',
            'User-Agent': constant.USER_AGENT,
        })

        retry_times = 0
        while True:
            try:
                retry_times += 1

                if data is not None:
                    response = self.session.post(
                        constant.API_URL + endpoint,
                        data=data,
                        verify=verify
                    )
                else:
                    response = self.session.get(
                        constant.API_URL + endpoint,
                        verify=verify
                    )

                return self.__handle_response(response)
            except ResponseError as e:
                if not self.retry:
                    raise
                if retry_times >= self.retry_times:
                    raise
                logger.warning('Endpoint: {}; Response code: {}; retrying #{}...'.format(
                    endpoint,
                    e.status_code,
                    retry_times
                ))
                time.sleep(self.retry_interval)

    def login(self, force=False):
        if self.is_logged_in and not force:
            return

        guid = util.generate_uuid(False)
        self.send_request(
            'si/fetch_headers/'
            '?challenge_type=signup'
            '&guid={}'.format(
                guid
            ),
            None,
            True
        )

        data = {
            'phone_id': util.generate_uuid(),
            '_csrftoken': self.last_response.cookies['csrftoken'],
            'username': self.username,
            'guid': self.uuid,
            'device_id': self.device_id,
            'password': self.password,
            'login_attempt_count': '0',
        }

        result = self.send_request(
            'accounts/login/',
            util.generate_signature(json.dumps(data)),
            True
        )
        self.is_logged_in = True
        self.user_id = result["logged_in_user"]["pk"]
        self.rank_token = self.__generate_rank_token()
        self.token = self.last_response.cookies["csrftoken"]

        logger.info("Login success!")

    @get('accounts/logout/')
    def logout(self):
        self.is_logged_in = False


class ProfileAPI(_BaseAPI):
    @post('accounts/change_password/')
    def change_password(self, new_password):
        return None, {
            'old_password': self.password,
            'new_password1': new_password,
            'new_password2': new_password,
        }

    def change_profile_picture(self, photo):
        # TODO Instagram.php 705-775
        raise NotImplementedError()

    @post('accounts/remove_profile_picture/')
    def remove_profile_picture(self):
        pass

    @post('accounts/set_private/')
    def set_private_account(self):
        pass

    @post('accounts/set_public/')
    def set_public_account(self):
        pass

    @post('accounts/current_user/?edit=true')
    def get_profile_data(self):
        pass

    @post('accounts/edit_profile/')
    def edit_profile(self, url, phone, first_name, biography, email, gender):
        return None, {
            'external_url': url,
            'phone_number': phone,
            'username': self.username,
            'full_name': first_name,
            'biography': biography,
            'email': email,
            'gender': gender,
        }

    @post('accounts/set_phone_and_name/')
    def set_name_and_phone(self, name='', phone=''):
        return None, {
            'first_name': name,
            'phone_number': phone,
        }


class FriendsAPI(_BaseAPI):
    @get('friendships/autocomplete_user_list/')
    def auto_complete_user_list(self):
        pass

    @endpoint('friendships/{}/following/')
    def get_user_followings(self, user_id, max_id=''):
        url = 'friendships/{}/following/?'.format(user_id)
        query_string = {
            'ig_sig_key_version': constant.SIG_KEY_VERSION,
            'rank_token': self.rank_token,
        }
        if max_id:
            query_string['max_id'] = max_id
        url += urllib.parse.urlencode(query_string)
        return self.send_request(url)

    def get_self_user_followings(self):
        return self.get_user_followings(self.user_id)

    def get_total_followings(self, user_id):
        followers = []
        next_max_id = ''
        while True:
            temp = self.get_user_followings(user_id, next_max_id)

            for item in temp["users"]:
                followers.append(item)

            if temp["big_list"] is False:
                return followers
            next_max_id = temp["next_max_id"]

    def get_total_self_followings(self):
        return self.get_total_followings(self.user_id)

    @get('friendships/{user_id}/followers/', ranked=True)
    def get_user_followers(self, user_id, max_id=None):
        return {
                   'user_id': user_id,
               }, {
                   'max_id': max_id,
               }

    def get_self_user_followers(self):
        return self.get_user_followers(self.user_id)

    def get_total_followers(self, user_id):
        followers = []
        next_max_id = ''
        while True:
            temp = self.get_user_followers(user_id, next_max_id)

            for item in temp["users"]:
                followers.append(item)

            if temp["big_list"] is False:
                return followers
            next_max_id = temp["next_max_id"]

    def get_total_self_followers(self):
        return self.get_total_followers(self.user_id)

    @get('friendships/pending')
    def get_pending_follow_requests(self):
        pass

    @post('friendships/approve/{user_id}/')
    def approve(self, user_id):
        return {
            'user_id': user_id,
        }

    @post('friendships/ignore/{user_id}/')
    def ignore(self, user_id):
        return {
            'user_id': user_id,
        }

    @post('friendships/create/{user_id}/')
    def follow(self, user_id):
        return {
            'user_id': user_id,
        }

    @post('friendships/destroy/{user_id}/')
    def unfollow(self, user_id):
        return {
            'user_id': user_id,
        }

    @post('friendships/block/{user_id}/')
    def block(self, user_id):
        return {
            'user_id': user_id,
        }

    @post('friendships/unblock/{user_id}/')
    def unblock(self, user_id):
        return {
            'user_id': user_id,
        }

    @post('friendships/show/{user_id}/')
    def user_friendship(self, user_id):
        return {
            'user_id': user_id,
        }


class UserAPI(_BaseAPI):
    @get('users/{user_id}/info/')
    def get_username_info(self, user_id):
        return {
            'user_id': user_id,
        }

    def get_self_username_info(self):
        return self.get_username_info(self.user_id)

    @get('users/search/', ranked=True)
    def search_users(self, query):
        return None, {
            'sig_key_version': constant.SIG_KEY_VERSION,
            'is_typeahead': 'true',
            'query': query,
        }

    @get('users/{username}/usernameinfo/')
    def search_username(self, username):
        return {
            'username': username,
        }


class FeedAPI(_BaseAPI):
    @get('feed/user/{user_id}/reel_media/')
    def get_story(self, user_id):
        return {
            'user_id': user_id,
        }

    @get('feed/saved')
    def get_self_saved_media(self):
        pass

    @get('feed/tag/{tag}/', ranked=True)
    def tag_feed(self, tag, max_id=None):
        return {
                   'tag': tag,
               }, {
                   'max_id': max_id,
               }

    @get('feed/timeline/', ranked=True)
    def get_timeline(self):
        pass

    @get('feed/user/{user_id}/', ranked=True)
    def get_user_feed(self, user_id, max_id=None, min_timestamp=None):
        return {
                   'user_id': user_id,
               }, {
                   'max_id': max_id,
                   'min_timestamp': min_timestamp,
               }

    def get_self_user_feed(self, max_id='', min_timestamp=None):
        return self.get_user_feed(self.user_id, max_id, min_timestamp)

    def get_total_user_feed(self, user_id, min_timestamp=None):
        user_feed = []
        next_max_id = ''
        while True:
            temp = self.get_user_feed(user_id, next_max_id, min_timestamp)
            for item in temp["items"]:
                user_feed.append(item)
            if temp["more_available"] is False:
                return user_feed
            next_max_id = temp["next_max_id"]

    def get_total_self_user_feed(self, min_timestamp=None):
        return self.get_total_user_feed(self.user_id, min_timestamp)

    @get('feed/location/{location_id}/', ranked=True)
    def get_location_feed(self, location_id, max_id=None):
        return {
                   'location_id': location_id,
               }, {
                   'max_id': max_id
               }

    @get('feed/popular/', ranked=True)
    def get_popular_feed(self):
        return None, {
            'people_teaser_supported': 1,
        }

    @get('feed/liked/')
    def get_liked_media(self, max_id=None):
        return None, {
            'max_id': max_id,
        }

    def get_total_liked_media(self, scan_rate=1):
        next_id = ''
        liked_items = []
        for x in range(0, scan_rate):
            temp = self.get_liked_media(next_id)
            next_id = temp["next_max_id"]
            for item in temp["items"]:
                liked_items.append(item)
        return liked_items


class PostAPI(_BaseAPI):
    @post('media/{media_id}/edit_media/')
    def edit_media(self, media_id, caption_text=''):
        return {
                   'media_id': media_id,
               }, {
                   'caption_text': caption_text,
               }

    @post('media/{media_id}/remove/')
    def remove_self_tag(self, media_id):
        return {
                   'media_id': media_id,
               }, None

    @post('media/{media_id}/info/')
    def media_info(self, media_id):
        return {
            'media_id': media_id,
        }

    @post('media/{media_id}/delete/')
    def delete_media(self, media_id, media_type=1):
        return {
            'media_type': media_type,
            'media_id': media_id,
        }

    @get('media/{media_id}/likers/')
    def get_media_likers(self, media_id):
        return {
            'media_id': media_id,
        }

    @post('media/{media_id}/like/')
    def like(self, media_id):
        return {
            'media_id': media_id,
        }

    @post('media/{media_id}/unlike/')
    def unlike(self, media_id):
        return {
            'media_id': media_id,
        }

    @post('media/{media_id}/save/')
    def save(self, media_id):
        return {
            'media_id': media_id,
        }

    @post('media/{media_id}/unsave/')
    def unsave(self, media_id):
        return {
            'media_id': media_id,
        }

    # --- comments ---

    @post('media/{media_id}/comment/')
    def comment(self, media_id, comment_text):
        return {
                   'media_id': media_id,
               }, {
                   'comment_text': comment_text,
               }

    @post('media/{media_id}/comment/{comment_id}/delete/')
    def delete_comment(self, media_id, comment_id):
        return {
            'media_id': media_id,
            'comment_id': comment_id,
        }

    @get('media/{media_id}/comments/')
    def get_media_comments(self, media_id, max_id=None):
        return {
                   'media_id': media_id,
               }, {
                   'max_id': max_id,
               }


class UploadAPI(_BaseAPI):
    @endpoint('upload/photo/')
    def upload_photo(self, photo, caption=None, upload_id=None, is_sidecar=None):
        if upload_id is None:
            upload_id = util.generate_upload_id()
        data = {
            'upload_id': upload_id,
            '_uuid': self.uuid,
            '_csrftoken': self.token,
            'image_compression': '{"lib_name":"jt","lib_version":"1.3.0","quality":"87"}',
            'photo': (
                'pending_media_{}.jpg'.format(upload_id),
                open(photo, 'rb'),
                'application/octet-stream',
                {'Content-Transfer-Encoding': 'binary'},
            ),
        }
        if is_sidecar:
            data['is_sidecar'] = '1'
        m = MultipartEncoder(data, boundary=self.uuid)
        self.session.headers.update({
            'X-IG-Capabilities': '3Q4=',
            'X-IG-Connection-Type': 'WIFI',
            'Cookie2': '$Version=1',
            'Accept-Language': 'en-US',
            'Accept-Encoding': 'gzip, deflate',
            'Content-type': m.content_type,
            'Connection': 'close',
            'User-Agent': constant.USER_AGENT,
        })
        response = self.session.post(
            constant.API_URL + 'upload/photo/',
            data=m.to_string()
        )

        if response.status_code != 200:
            raise UploadFailed()

        self.configure_photo(upload_id, photo, caption)
        self.expose()

    @endpoint('upload/video/')
    def upload_video(self, video, thumbnail, caption=None, upload_id=None, is_sidecar=None):
        if upload_id is None:
            upload_id = util.generate_upload_id()
        data = {
            'upload_id': upload_id,
            '_csrftoken': self.token,
            'media_type': '2',
            '_uuid': self.uuid,
        }
        if is_sidecar:
            data['is_sidecar'] = '1'
        m = MultipartEncoder(data, boundary=self.uuid)
        self.session.headers.update({
            'X-IG-Capabilities': '3Q4=',
            'X-IG-Connection-Type': 'WIFI',
            'Host': 'i.instagram.com',
            'Cookie2': '$Version=1',
            'Accept-Language': 'en-US',
            'Accept-Encoding': 'gzip, deflate',
            'Content-type': m.content_type,
            'Connection': 'keep-alive',
            'User-Agent': constant.USER_AGENT,
        })
        response = self.session.post(
            constant.API_URL + 'upload/video/',
            data=m.to_string()
        )

        if response.status_code != 200:
            raise UploadFailed()

        body = json.loads(response.text)
        upload_url = body['video_upload_urls'][3]['url']
        upload_job = body['video_upload_urls'][3]['job']

        video_data = open(video, 'rb').read()
        # solve issue #85 TypeError: slice indices must be integers or None or have an __index__ method
        request_size = int(math.floor(len(video_data) / 4))
        last_request_extra = (len(video_data) - (request_size * 3))

        headers = copy.deepcopy(self.session.headers)
        self.session.headers.update({
            'X-IG-Capabilities': '3Q4=',
            'X-IG-Connection-Type': 'WIFI',
            'Cookie2': '$Version=1',
            'Accept-Language': 'en-US',
            'Accept-Encoding': 'gzip, deflate',
            'Content-type': 'application/octet-stream',
            'Session-ID': upload_id,
            'Connection': 'keep-alive',
            'Content-Disposition': 'attachment; filename="video.mov"',
            'job': upload_job,
            'Host': 'upload.instagram.com',
            'User-Agent': constant.USER_AGENT,
        })
        for i in range(0, 4):
            start = i * request_size
            if i == 3:
                end = i * request_size + last_request_extra
            else:
                end = (i + 1) * request_size
            length = last_request_extra if i == 3 else request_size
            content_range = "bytes {start}-{end}/{lenVideo}".format(
                start=start,
                end=(end - 1),
                lenVideo=len(video_data)
            ).encode('utf-8')

            self.session.headers.update({
                'Content-Length': str(end - start),
                'Content-Range': content_range,
            })
            response = self.session.post(
                upload_url,
                data=video_data[start:start + length]
            )
        self.session.headers = headers

        if response.status_code != 200:
            raise UploadFailed()

        self.configure_video(upload_id, video, thumbnail, caption)
        self.expose()

    @staticmethod
    def __throw_if_invalid_usertags(usertags):
        for user_position in usertags:
            # Verify this usertag entry, ensuring that the entry is format
            # ['position'=>[0.0,1.0],'user_id'=>'123'] and nothing else.
            correct = True
            if isinstance(user_position, dict):
                position = user_position.get('position', None)
                user_id = user_position.get('user_id', None)

                if isinstance(position, list) and len(position) == 2:
                    try:
                        x = float(position[0])
                        y = float(position[1])
                        if x < 0.0 or x > 1.0:
                            correct = False
                        if y < 0.0 or y > 1.0:
                            correct = False
                    except Exception:
                        correct = False
                try:
                    user_id = int(user_id)
                    if user_id < 0:
                        correct = False
                except Exception:
                    correct = False
            if not correct:
                raise Exception('Invalid user entry in usertags array.')

    def upload_album(self, media, caption=None):
        if not media:
            raise AlbumSizeError(0)

        if len(media) < 2 or len(media) > 10:
            raise AlbumSizeError(len(media))

        # Figure out the media file details for ALL media in the album.
        # NOTE: We do this first, since it validates whether the media files are
        # valid and lets us avoid wasting time uploading totally invalid albums!
        for idx, item in enumerate(media):
            if not (item.get('file', '') or item.get('type', '')):
                raise AlbumMediaContentError(idx)

            # $itemInternalMetadata = new InternalMetadata();
            # If usertags are provided, verify that the entries are valid.
            if item.get('usertags', []):
                self.__throw_if_invalid_usertags(item['usertags'])

            # Pre-process media details and throw if not allowed on Instagram.
            if item.get('type', '') == 'photo':
                # Determine the photo details.
                # $itemInternalMetadata->setPhotoDetails(Constants::FEED_TIMELINE_ALBUM, $item['file']);
                pass

            elif item.get('type', '') == 'video':
                # Determine the video details.
                # $itemInternalMetadata->setVideoDetails(Constants::FEED_TIMELINE_ALBUM, $item['file']);
                pass

            else:
                raise AlbumMediaTypeError(item['type'])

            item_internal_metadata = {}
            item['internalMetadata'] = item_internal_metadata

        # Perform all media file uploads.
        for idx, item in enumerate(media):
            item_upload_id = util.generate_upload_id()
            if item.get('type', '') == 'photo':
                self.upload_photo(
                    item['file'],
                    caption=caption,
                    is_sidecar=True,
                    upload_id=item_upload_id
                )
                # $itemInternalMetadata->setPhotoUploadResponse($this->ig->internal->uploadPhotoData(Constants::FEED_TIMELINE_ALBUM, $itemInternalMetadata));

            elif item.get('type', '') == 'video':
                # Attempt to upload the video data.
                self.upload_video(
                    item['file'],
                    item['thumbnail'],
                    caption=caption,
                    is_sidecar=True,
                    upload_id=item_upload_id
                )
                # $itemInternalMetadata = $this->ig->internal->uploadVideo(Constants::FEED_TIMELINE_ALBUM, $item['file'], $itemInternalMetadata);
                # Attempt to upload the thumbnail, associated with our video's ID.
                # $itemInternalMetadata->setPhotoUploadResponse($this->ig->internal->uploadPhotoData(Constants::FEED_TIMELINE_ALBUM, $itemInternalMetadata));
                pass
            item['internalMetadata']['upload_id'] = item_upload_id

        return self.configure_album(media, caption_text=caption)

    # --- configure ---

    @post('media/configure/')
    def configure_photo(self, upload_id, photo, caption=''):
        (w, h) = get_image_size(photo)
        return None, {
            'media_folder': 'Instagram',
            'source_type': 4,
            'caption': caption,
            'upload_id': upload_id,
            'device': constant.DEVICE_SETTINTS,
            'edits': {
                'crop_original_size': [w * 1.0, h * 1.0],
                'crop_center': [0.0, 0.0],
                'crop_zoom': 1.0,
            },
            'extra': {
                'source_width': w,
                'source_height': h,
            },
        }

    @post('media/configure/?video=1')
    def configure_video(self, upload_id, video, thumbnail, caption=''):
        clip = VideoFileClip(video)
        self.upload_photo(photo=thumbnail, caption=caption, upload_id=upload_id)
        return None, {
            'upload_id': upload_id,
            'source_type': 3,
            'poster_frame_index': 0,
            'length': 0.00,
            'audio_muted': False,
            'filter_type': 0,
            'video_result': 'deprecated',
            'clips': {
                'length': clip.duration,
                'source_type': '3',
                'camera_position': 'back',
            },
            'extra': {
                'source_width': clip.size[0],
                'source_height': clip.size[1],
            },
            'device': constant.DEVICE_SETTINTS,
            '_csrftoken': self.token,
            '_uuid': self.uuid,
            '_uid': self.user_id,
            'caption': caption,
        }

    @post('media/configure_sidecar/')
    def configure_album(self, media, caption_text=''):
        album_upload_id = util.generate_upload_id()

        date = datetime.utcnow().isoformat()
        children_metadata = []
        for item in media:
            item_internal_metadata = item['internalMetadata']
            upload_id = item_internal_metadata.get(
                'upload_id',
                util.generate_upload_id()
            )
            if item.get('type', '') == 'photo':
                # Build this item's configuration.
                photo_config = {
                    'date_time_original': date,
                    'scene_type': 1,
                    'disable_comments': False,
                    'upload_id': upload_id,
                    'source_type': 0,
                    'scene_capture_type': 'standard',
                    'date_time_digitized': date,
                    'geotag_enabled': False,
                    'camera_position': 'back',
                    'edits': {
                        'filter_strength': 1,
                        'filter_name': 'IGNormalFilter',
                    },
                }
                # This usertag per-file EXTERNAL metadata is only supported for PHOTOS!
                if item.get('usertags', []):
                    # NOTE: These usertags were validated in Timeline::uploadAlbum.
                    photo_config['usertags'] = json.dumps({'in': item['usertags']})

                children_metadata.append(photo_config)
            if item.get('type', '') == 'video':
                # Get all of the INTERNAL per-VIDEO metadata.
                video_details = item_internal_metadata.get('video_details', {})
                # Build this item's configuration.
                video_config = {
                    'length': video_details.get('duration', 1.0),
                    'date_time_original': date,
                    'scene_type': 1,
                    'poster_frame_index': 0,
                    'trim_type': 0,
                    'disable_comments': False,
                    'upload_id': upload_id,
                    'source_type': 'library',
                    'geotag_enabled': False,
                    'edits': {
                        'length': video_details.get('duration', 1.0),
                        'cinema': 'unsupported',
                        'original_length': video_details.get('duration', 1.0),
                        'source_type': 'library',
                        'start_time': 0,
                        'camera_position': 'unknown',
                        'trim_type': 0,
                    },
                }

                children_metadata.append(video_config)

        return None, {
            'client_sidecar_id': album_upload_id,
            'caption': caption_text,
            'children_metadata': children_metadata,
        }


class MessagingAPI(_BaseAPI):
    @get('direct_v2/inbox/')
    def get_v2_inbox(self):
        pass

    @get('direct_v2/threads/{thread}')
    def get_v2_threads(self, thread, cursor=None):
        return {
                   'thread': thread,
               }, {
                   'cursor': cursor,
               }

    @staticmethod
    def __build_body(bodies, boundary):
        body = u''
        for b in bodies:
            body += u'--{boundary}\r\n'.format(boundary=boundary)
            body += u'Content-Disposition: {b_type}; name="{b_name}"'.format(b_type=b['type'], b_name=b['name'])
            _filename = b.get('filename', None)
            _headers = b.get('headers', None)
            if _filename:
                _filename, ext = os.path.splitext(_filename)
                body += u'; filename="pending_media_{uid}.{ext}"'.format(uid=util.generate_upload_id(), ext=ext)
            if _headers and isinstance(_headers, list):
                for h in _headers:
                    body += u'\r\n{header}'.format(header=h)
            body += u'\r\n\r\n{data}\r\n'.format(data=b['data'])
        body += u'--{boundary}--'.format(boundary=boundary)
        return body

    @endpoint('direct_v2/threads/broadcast/text/')
    def direct_message(self, text, recipients):
        if not isinstance(recipients, list):
            recipients = [str(recipients)]
        recipient_users = '"",""'.join(str(r) for r in recipients)
        endpoint = 'direct_v2/threads/broadcast/text/'
        boundary = self.uuid
        bodies = [
            {
                'type': 'form-data',
                'name': 'recipient_users',
                'data': '[["{}"]]'.format(recipient_users),
            },
            {
                'type': 'form-data',
                'name': 'client_context',
                'data': self.uuid,
            },
            {
                'type': 'form-data',
                'name': 'thread',
                'data': '["0"]',
            },
            {
                'type': 'form-data',
                'name': 'text',
                'data': text or '',
            },
        ]
        data = self.__build_body(bodies, boundary)
        self.session.headers.update({
            'User-Agent': constant.USER_AGENT,
            'Proxy-Connection': 'keep-alive',
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'Content-Type': 'multipart/form-data; boundary={}'.format(boundary),
            'Accept-Language': 'en-en',
        })
        # self.SendRequest(endpoint,post=data) #overwrites 'Content-type' header and boundary is missed
        response = self.session.post(
            constant.API_URL + endpoint,
            data=data
        )

        if response.status_code == 200:
            self.last_response = response
            return json.loads(response.text)

        raise ResponseError(response.status_code, response)

    @endpoint('direct_v2/threads/broadcast/media_share/?media_type=photo')
    def direct_share(self, media_id, recipients, text=None):
        if not isinstance(recipients, list):
            recipients = [str(recipients)]
        recipient_users = '"",""'.join(str(r) for r in recipients)
        endpoint = 'direct_v2/threads/broadcast/media_share/?media_type=photo'
        boundary = self.uuid
        bodies = [
            {
                'type': 'form-data',
                'name': 'media_id',
                'data': media_id,
            },
            {
                'type': 'form-data',
                'name': 'recipient_users',
                'data': '[["{}"]]'.format(recipient_users),
            },
            {
                'type': 'form-data',
                'name': 'client_context',
                'data': self.uuid,
            },
            {
                'type': 'form-data',
                'name': 'thread',
                'data': '["0"]',
            },
            {
                'type': 'form-data',
                'name': 'text',
                'data': text or '',
            },
        ]
        data = self.__build_body(bodies, boundary)
        self.session.headers.update({
            'User-Agent': constant.USER_AGENT,
            'Proxy-Connection': 'keep-alive',
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'Content-Type': 'multipart/form-data; boundary={}'.format(boundary),
            'Accept-Language': 'en-en',
        })
        # self.SendRequest(endpoint,post=data) #overwrites 'Content-type' header and boundary is missed
        response = self.session.post(
            constant.API_URL + endpoint,
            data=data
        )

        return self.__handle_response(response)


class LiveAPI(_BaseAPI):
    @post('live/create/')
    def create_broadcast(self, preview_width=1080, preview_height=1920, broadcast_message=''):
        return None, {
            'preview_height': preview_height,
            'preview_width': preview_width,
            'broadcast_message': broadcast_message,
            'broadcast_type': 'RTMP',
            'internal_only': 0,
        }

    @post('live/{broadcast_id}/start')
    def start_broadcast(self, broadcast_id, send_notification=False):
        return {
                   'broadcast_id': broadcast_id,
               }, {
                   'should_send_notifications': int(send_notification),
               }

    @post('live/{broadcast_id}/end_broadcast/')
    def stop_broadcast(self, broadcast_id):
        return {
                   'broadcast_id': broadcast_id,
               }, None

    @post('live/{broadcast_id}/add_to_post_live/')
    def add_broadcast_to_live(self, broadcast_id):
        # broadcast has to be ended first!
        return {
                   'broadcast_id': broadcast_id,
               }, None


class MiscAPI(_BaseAPI):
    @post('/qe/sync/')
    def sync_features(self):
        return None, {
            'id': self.user_id,
            'experiments': constant.EXPERIMENTS,
        }

    @post('qe/expose/')
    def expose(self):
        return None, {
            'id': self.user_id,
            'experiment': 'ig_android_profile_contextual_feed',
        }

    @get('megaphone/log/')
    def megaphone_log(self):
        pass

    @get('discover/explore/')
    def explore(self):
        pass

    @get('news/inbox/')
    def get_recent_activity(self):
        pass

    @get('news/')
    def get_following_recent_activity(self):
        pass

    @get('usertags/{user_id}/feed/', ranked=True)
    def get_usertags(self, user_id):
        return {
            'user_id': user_id,
        }

    def get_self_usertags(self):
        return self.get_usertags(self.user_id)

    @get('maps/user/{user_id}/')
    def get_geo_media(self, user_id):
        return {
            'user_id': user_id,
        }

    def get_self_geo_media(self):
        return self.get_geo_media(self.user_id)

    @get('fbsearch/topsearch/', ranked=True)
    def fb_user_search(self, query):
        return None, {
            'context': 'blended',
            'query': query,
        }

    @get('fbsearch/places/', ranked=True)
    def search_location(self, query):
        return None, {
            'query': query,
        }

    @endpoint('address_book/link/?include=extra_display_name,thumbnails')
    def sync_from_address_book(self, contacts):
        return self.send_request(
            'address_book/link/?include=extra_display_name,thumbnails',
            "contacts={}".format(
                json.dumps(contacts)
            )
        )

    @get('tags/search/', ranked=True)
    def search_tags(self, query):
        return None, {
            'is_typeahead': 'true',
            'q': query,
        }

    @get('direct_share/inbox/')
    def get_direct_share(self):
        pass

    def backup(self):
        # TODO Instagram.php 1470-1485
        raise NotImplementedError()


class InstagramAPI(
    ProfileAPI,
    FriendsAPI,
    UserAPI,
    FeedAPI,
    PostAPI,
    UploadAPI,
    MessagingAPI,
    LiveAPI,
    MiscAPI
):
    pass
