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


class InstagramAPI(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.device_id = self.__generate_device_id()
        self.uuid = util.generate_uuid()

        self.is_logged_in = False
        self.session = requests.Session()

        self.last_response = None
        self.user_id = None
        self.rank_token = None
        self.token = None

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

        # check for sentry block
        result = json.loads(response.text)
        if 'error_type' in result and result['error_type'] == 'sentry_block':
            raise SentryBlockException(result['message'])

        raise ResponseError(response.status_code, response)

    def __send_request(self, endpoint, data=None, login=False):
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

    def login(self, force=False):
        if self.is_logged_in and not force:
            return

        guid = util.generate_uuid(False)
        self.__send_request(
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

        result = self.__send_request(
            'accounts/login/',
            util.generate_signature(json.dumps(data)),
            True
        )
        self.is_logged_in = True
        self.user_id = result["logged_in_user"]["pk"]
        self.rank_token = self.__generate_rank_token()
        self.token = self.last_response.cookies["csrftoken"]

        self.sync_features()
        self.auto_complete_user_list()
        self.timeline_feed()
        self.get_v2_inbox()
        self.get_recent_activity()
        logger.info("Login success!")

    def sync_features(self):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            'id': self.user_id,
            '_csrftoken': self.token,
            'experiments': constant.EXPERIMENTS,
        })
        return self.__send_request(
            'qe/sync/',
            util.generate_signature(data)
        )

    def auto_complete_user_list(self):
        return self.__send_request(
            'friendships/autocomplete_user_list/'
        )

    def timeline_feed(self):
        return self.__send_request(
            'feed/timeline/'
        )

    def megaphone_log(self):
        return self.__send_request(
            'megaphone/log/'
        )

    def expose(self):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            'id': self.user_id,
            '_csrftoken': self.token,
            'experiment': 'ig_android_profile_contextual_feed',
        })
        return self.__send_request(
            'qe/expose/',
            util.generate_signature(data)
        )

    def logout(self):
        return self.__send_request(
            'accounts/logout/'
        )

    def upload_photo(self, photo, caption=None, upload_id=None, is_sidecar=None):
        if upload_id is None:
            upload_id = str(int(time.time() * 1000))
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

        self.configure(upload_id, photo, caption)
        self.expose()

    def upload_video(self, video, thumbnail, caption=None, upload_id=None, is_sidecar=None):
        if upload_id is None:
            upload_id = str(int(time.time() * 1000))
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

    def upload_album(self, media, caption=None, upload_id=None):
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
                self.throw_if_invalid_usertags(item['usertags'])

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
            item_internal_metadata = item['internalMetadata']
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
                self.upload_video(item['file'], item['thumbnail'], caption=caption, is_sidecar=True,
                                  upload_id=item_upload_id)
                # $itemInternalMetadata = $this->ig->internal->uploadVideo(Constants::FEED_TIMELINE_ALBUM, $item['file'], $itemInternalMetadata);
                # Attempt to upload the thumbnail, associated with our video's ID.
                # $itemInternalMetadata->setPhotoUploadResponse($this->ig->internal->uploadPhotoData(Constants::FEED_TIMELINE_ALBUM, $itemInternalMetadata));
                pass
            item['internalMetadata']['upload_id'] = item_upload_id

        album_internal_metadata = {}
        return self.configure_timeline_album(media, album_internal_metadata, caption_text=caption)

    def throw_if_invalid_usertags(self, usertags):
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

    def configure_timeline_album(self, media, album_internal_metadata, caption_text='', location=None):
        endpoint = 'media/configure_sidecar/'
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
        # Build the request...
        data = {
            '_csrftoken': self.token,
            '_uid': self.user_id,
            '_uuid': self.uuid,
            'client_sidecar_id': album_upload_id,
            'caption': caption_text,
            'children_metadata': children_metadata,
        }
        return self.__send_request(
            endpoint,
            util.generate_signature(json.dumps(data))
        )

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
        data = self.build_body(bodies, boundary)
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

    def direct_share(self, media_id, recipients, text=None):
        if not isinstance(position, list):  # FIXME
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
        data = self.build_body(bodies, boundary)
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

    def configure_video(self, upload_id, video, thumbnail, caption=''):
        clip = VideoFileClip(video)
        self.upload_photo(photo=thumbnail, caption=caption, upload_id=upload_id)
        data = json.dumps({
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
        })
        return self.__send_request(
            'media/configure/?video=1',
            util.generate_signature(data)
        )

    def configure(self, upload_id, photo, caption=''):
        (w, h) = get_image_size(photo)
        data = json.dumps({
            '_csrftoken': self.token,
            'media_folder': 'Instagram',
            'source_type': 4,
            '_uid': self.user_id,
            '_uuid': self.uuid,
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
        })
        return self.__send_request(
            'media/configure/',
            util.generate_signature(data)
        )

    def edit_media(self, media_id, caption_text=''):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            '_csrftoken': self.token,
            'caption_text': caption_text,
        })
        return self.__send_request(
            'media/{}/edit_media/'.format(media_id),
            util.generate_signature(data)
        )

    def remove_self_tag(self, media_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            '_csrftoken': self.token,
        })
        return self.__send_request(
            'media/{}/remove/'.format(media_id),
            util.generate_signature(data)
        )

    def media_info(self, media_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            '_csrftoken': self.token,
            'media_id': media_id,
        })
        return self.__send_request(
            'media/{}/info/'.format(media_id),
            util.generate_signature(data)
        )

    def delete_media(self, media_id, media_type=1):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            '_csrftoken': self.token,
            'media_type': media_type,
            'media_id': media_id,
        })
        return self.__send_request(
            'media/{}/delete/'.format(media_id),
            util.generate_signature(data)
        )

    def change_password(self, new_password):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            '_csrftoken': self.token,
            'old_password': self.password,
            'new_password1': new_password,
            'new_password2': new_password,
        })
        return self.__send_request(
            'accounts/change_password/',
            util.generate_signature(data)
        )

    def explore(self):
        return self.__send_request(
            'discover/explore/'
        )

    def comment(self, media_id, comment_text):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            '_csrftoken': self.token,
            'comment_text': comment_text,
        })
        return self.__send_request(
            'media/{}/comment/'.format(media_id),
            util.generate_signature(data)
        )

    def delete_comment(self, media_id, comment_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            '_csrftoken': self.token,
        })
        return self.__send_request(
            'media/{}/comment/{}/delete/'.format(media_id, comment_id),
            util.generate_signature(data)
        )

    def change_profile_picture(self, photo):
        # TODO Instagram.php 705-775
        raise NotImplementedError()

    def remove_profile_picture(self):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            '_csrftoken': self.token,
        })
        return self.__send_request(
            'accounts/remove_profile_picture/',
            util.generate_signature(data)
        )

    def set_private_account(self):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            '_csrftoken': self.token,
        })
        return self.__send_request(
            'accounts/set_private/',
            util.generate_signature(data)
        )

    def set_public_account(self):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            '_csrftoken': self.token,
        })
        return self.__send_request(
            'accounts/set_public/',
            util.generate_signature(data)
        )

    def get_profile_data(self):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            '_csrftoken': self.token,
        })
        return self.__send_request(
            'accounts/current_user/?edit=true',
            util.generate_signature(data)
        )

    def edit_profile(self, url, phone, first_name, biography, email, gender):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            '_csrftoken': self.token,
            'external_url': url,
            'phone_number': phone,
            'username': self.username,
            'full_name': first_name,
            'biography': biography,
            'email': email,
            'gender': gender,
        })
        return self.__send_request(
            'accounts/edit_profile/',
            util.generate_signature(data)
        )

    def get_story(self, user_id):
        return self.__send_request(
            'feed/user/{}/reel_media/'.format(user_id)
        )

    def get_username_info(self, user_id):
        return self.__send_request(
            'users/{}/info/'.format(user_id)
        )

    def get_self_username_info(self):
        return self.get_username_info(self.user_id)

    def get_self_saved_media(self):
        return self.__send_request(
            'feed/saved'
        )

    def get_recent_activity(self):
        return self.__send_request(
            'news/inbox/'
        )

    def get_following_recent_activity(self):
        return self.__send_request(
            'news/'
        )

    def get_v2_inbox(self):
        return self.__send_request(
            'direct_v2/inbox/'
        )

    def get_v2_threads(self, thread, cursor=None):
        endpoint = 'direct_v2/threads/{0}'.format(thread)
        if cursor is not None:
            endpoint += '?cursor={0}'.format(cursor)
        return self.__send_request(endpoint)

    def get_usertags(self, user_id):
        return self.__send_request(
            'usertags/{}/feed/'
            '?rank_token={}'
            '&ranked_content=true'.format(
                user_id,
                self.rank_token
            )
        )

    def get_self_usertags(self):
        return self.get_usertags(self.user_id)

    def tag_feed(self, tag):
        return self.__send_request(
            'feed/tag/{}/'
            '?rank_token={}'
            '&ranked_content=true'.format(
                tag,
                self.rank_token
            )
        )

    def get_media_likers(self, media_id):
        return self.__send_request(
            'media/{}/likers/'.format(media_id)
        )

    def get_geo_media(self, user_id):
        return self.__send_request(
            'maps/user/{}/'.format(user_id)
        )

    def get_self_geo_media(self):
        return self.get_geo_media(self.user_id)

    def fb_user_search(self, query):
        return self.__send_request(
            'fbsearch/topsearch/'
            '?context=blended'
            '&query={}'
            '&rank_token={}'.format(
                query,
                self.rank_token
            )
        )

    def search_users(self, query):
        return self.__send_request(
            'users/search/'
            '?ig_sig_key_version={}'
            '&is_typeahead=true'
            '&query={}'
            '&rank_token={}'.format(
                constant.SIG_KEY_VERSION,
                query,
                self.rank_token
            )
        )

    def search_username(self, username):
        return self.__send_request(
            'users/{}/usernameinfo/'.format(username)
        )

    def sync_from_address_book(self, contacts):
        return self.__send_request(
            'address_book/link/?include=extra_display_name,thumbnails',
            "contacts={}".format(
                json.dumps(contacts)
            )
        )

    def search_tags(self, query):
        return self.__send_request(
            'tags/search/'
            '?is_typeahead=true'
            '&q={}'
            '&rank_token={}'.format(
                query,
                self.rank_token
            )
        )

    def get_timeline(self):
        return self.__send_request(
            'feed/timeline/'
            '?rank_token={}'
            '&ranked_content=true'.format(
                self.rank_token
            )
        )

    def get_user_feed(self, user_id, maxid='', min_timestamp=None):
        return self.__send_request(
            'feed/user/{}/'
            '?max_id={}'
            '&min_timestamp={}'
            '&rank_token={}'
            '&ranked_content=true'.format(
                user_id,
                maxid,
                min_timestamp,
                self.rank_token
            )
        )

    def get_self_user_feed(self, maxid='', min_timestamp=None):
        return self.get_user_feed(self.user_id, maxid, min_timestamp)

    def get_hashtag_feed(self, hashtag_string, maxid=''):
        return self.__send_request(
            'feed/tag/{}/'
            '?max_id={}'
            '&rank_token={}'
            '&ranked_content=true'.format(
                hashtag_string,
                maxid,
                self.rank_token
            )
        )

    def search_location(self, query):
        return self.__send_request(
            'fbsearch/places/'
            '?rank_token={}'
            '&query={}'.format(
                self.rank_token,
                query
            )
        )

    def get_location_feed(self, location_id, maxid=''):
        return self.__send_request(
            'feed/location/{}/'
            '?max_id={}'
            '&rank_token={}'
            '&ranked_content=true'.format(
                location_id,
                maxid,
                self.rank_token
            )
        )

    def get_popular_feed(self):
        return self.__send_request(
            'feed/popular/'
            '?people_teaser_supported=1'
            '&rank_token={}'
            '&ranked_content=true'.format(
                self.rank_token
            )
        )

    def get_user_followings(self, user_id, maxid=''):
        url = 'friendships/{}/following/?'.format(self.user_id)
        query_string = {
            'ig_sig_key_version': constant.SIG_KEY_VERSION,
            'rank_token': self.rank_token,
        }
        if maxid:
            query_string['max_id'] = maxid
        url += urllib.parse.urlencode(query_string)
        return self.__send_request(url)

    def get_self_user_followings(self):
        return self.get_user_followings(self.user_id)

    def get_user_followers(self, user_id, maxid=''):
        if maxid == '':
            return self.__send_request(
                'friendships/{}/followers/'
                '?rank_token={}'.format(
                    user_id,
                    self.rank_token
                )
            )
        else:
            return self.__send_request(
                'friendships/{}/followers/'
                '?rank_token={}'
                '&max_id={}'.format(
                    user_id,
                    self.rank_token,
                    maxid
                )
            )

    def get_self_user_followers(self):
        return self.get_user_followers(self.user_id)

    def get_pending_follow_requests(self):
        return self.__send_request(
            'friendships/pending'
        )

    def like(self, media_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            '_csrftoken': self.token,
            'media_id': media_id,
        })
        return self.__send_request(
            'media/{}/like/'.format(media_id),
            util.generate_signature(data)
        )

    def unlike(self, media_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            '_csrftoken': self.token,
            'media_id': media_id,
        })
        return self.__send_request(
            'media/{}/unlike/'.format(media_id),
            util.generate_signature(data)
        )

    def save(self, media_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            '_csrftoken': self.token,
            'media_id': media_id,
        })
        return self.__send_request(
            'media/{}/save/'.format(media_id),
            util.generate_signature(data)
        )

    def unsave(self, media_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            '_csrftoken': self.token,
            'media_id': media_id,
        })
        return self.__send_request(
            'media/{}/unsave/'.format(media_id),
            util.generate_signature(data)
        )

    def get_media_comments(self, media_id, max_id=''):
        return self.__send_request(
            'media/{}/comments/'
            '?max_id={}'.format(
                media_id,
                max_id
            )
        )

    def set_name_and_phone(self, name='', phone=''):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            'first_name': name,
            'phone_number': phone,
            '_csrftoken': self.token,
        })
        return self.__send_request(
            'accounts/set_phone_and_name/',
            util.generate_signature(data)
        )

    def get_direct_share(self):
        return self.__send_request(
            'direct_share/inbox/'
        )

    def backup(self):
        # TODO Instagram.php 1470-1485
        raise NotImplementedError()

    def approve(self, user_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            'user_id': user_id,
            '_csrftoken': self.token,
        })
        return self.__send_request(
            'friendships/approve/{}/'.format(user_id),
            util.generate_signature(data)
        )

    def ignore(self, user_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            'user_id': user_id,
            '_csrftoken': self.token,
        })
        return self.__send_request(
            'friendships/ignore/{}/'.format(user_id),
            util.generate_signature(data)
        )

    def follow(self, user_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            'user_id': user_id,
            '_csrftoken': self.token,
        })
        return self.__send_request(
            'friendships/create/{}/'.format(user_id),
            util.generate_signature(data)
        )

    def unfollow(self, user_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            'user_id': user_id,
            '_csrftoken': self.token,
        })
        return self.__send_request(
            'friendships/destroy/{}/'.format(user_id),
            util.generate_signature(data)
        )

    def block(self, user_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            'user_id': user_id,
            '_csrftoken': self.token,
        })
        return self.__send_request(
            'friendships/block/{}/'.format(user_id),
            util.generate_signature(data)
        )

    def unblock(self, user_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            'user_id': user_id,
            '_csrftoken': self.token,
        })
        return self.__send_request(
            'friendships/unblock/{}/'.format(user_id),
            util.generate_signature(data)
        )

    def user_friendship(self, user_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            'user_id': user_id,
            '_csrftoken': self.token,
        })
        return self.__send_request(
            'friendships/show/{}/'.format(user_id),
            util.generate_signature(data)
        )

    def get_liked_media(self, maxid=''):
        return self.__send_request(
            'feed/liked/'
            '?max_id={}'.format(
                maxid
            )
        )

    def create_broadcast(self, preview_width=1080, preview_height=1920, broadcast_message=''):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            'preview_height': preview_height,
            'preview_width': preview_width,
            'broadcast_message': broadcast_message,
            'broadcast_type': 'RTMP',
            'internal_only': 0,
            '_csrftoken': self.token,
        })
        return self.__send_request(
            'live/create/',
            util.generate_signature(data)
        )

    def start_broadcast(self, broadcast_id, send_notification=False):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            'should_send_notifications': int(send_notification),
            '_csrftoken': self.token,
        })
        return self.__send_request(
            'live/{}/start'.format(broadcast_id),
            util.generate_signature(data)
        )

    def stop_broadcast(self, broadcast_id):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            '_csrftoken': self.token,
        })
        return self.__send_request(
            'live/{}/end_broadcast/'.format(broadcast_id),
            util.generate_signature(data)
        )

    def add_broadcast_to_live(self, broadcast_id):
        # broadcast has to be ended first!
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.user_id,
            '_csrftoken': self.token,
        })
        return self.__send_request(
            'live/{}/add_to_post_live/'.format(broadcast_id),
            util.generate_signature(data)
        )

    def build_body(self, bodies, boundary):
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

    def get_total_self_followers(self):
        return self.get_total_followers(self.user_id)

    def get_total_self_followings(self):
        return self.get_total_followings(self.user_id)

    def get_total_liked_media(self, scan_rate=1):
        next_id = ''
        liked_items = []
        for x in range(0, scan_rate):
            temp = self.get_liked_media(next_id)
            try:
                next_id = temp["next_max_id"]
                for item in temp["items"]:
                    liked_items.append(item)
            except KeyError as e:
                break
        return liked_items
