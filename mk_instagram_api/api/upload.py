import math

from datetime import datetime
from requests_toolbelt import MultipartEncoder

from ._base import *

try:
    from moviepy.editor import VideoFileClip
except ImportError:
    logging.warning("Fail to import moviepy. Need only for Video upload.")

__author__ = 'Michael'


class UploadAPI(BaseAPI):
    @endpoint('upload/photo/')
    def upload_photo(self, photo, caption=None, upload_id=None, is_sidecar=None):
        uri = 'upload/photo/'

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
        with self._update_headers({
            'Accept-Encoding': 'gzip, deflate',
            'Content-type': m.content_type,
            'X-IG-Capabilities': '3Q4=',
            'X-IG-Connection-Type': 'WIFI',
        }):
            self.send_request(
                uri,
                data=m.to_string()
            )

        self.__configure_photo(upload_id, photo, caption)
        self.__expose()

    @endpoint('upload/video/')
    def upload_video(self, video, thumbnail, caption=None, upload_id=None, is_sidecar=None):
        uri = 'upload/video/'

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
        with self._update_headers({
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Content-type': m.content_type,
            'Host': 'i.instagram.com',
            'X-IG-Capabilities': '3Q4=',
            'X-IG-Connection-Type': 'WIFI',
        }):
            result = self.send_request(
                uri,
                data=m.to_string()
            )

        upload_url = result['video_upload_urls'][3]['url']
        upload_job = result['video_upload_urls'][3]['job']

        video_data = open(video, 'rb').read()
        # solve issue #85 TypeError: slice indices must be integers or None or have an __index__ method
        request_size = int(math.floor(len(video_data) / 4))
        last_request_extra = (len(video_data) - (request_size * 3))

        with self._update_headers({
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Content-Disposition': 'attachment; filename="video.mov"',
            'Content-type': 'application/octet-stream',
            'Host': 'upload.instagram.com',
            'job': upload_job,
            'Session-ID': upload_id,
            'X-IG-Capabilities': '3Q4=',
            'X-IG-Connection-Type': 'WIFI',
        }):
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

                with self._update_headers({
                    'Content-Length': str(end - start),
                    'Content-Range': content_range,
                }):
                    self.send_request(
                        upload_url,
                        data=video_data[start:start + length],
                        raw_url=True
                    )

        self.__configure_video(upload_id, video, thumbnail, caption)
        self.__expose()

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

        return self.__configure_album(media, caption_text=caption)

    # --- configure ---

    @post('media/configure/')
    def __configure_photo(self, upload_id, photo, caption=''):
        (w, h) = util.get_image_size(photo)
        return None, {
            'media_folder': 'Instagram',
            'source_type': 4,
            'caption': caption,
            'upload_id': upload_id,
            'device': constant.DEVICE_SETTINGS,
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
    def __configure_video(self, upload_id, video, thumbnail, caption=''):
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
            'device': constant.DEVICE_SETTINGS,
            '_csrftoken': self.token,
            '_uuid': self.uuid,
            '_uid': self.user_id,
            'caption': caption,
        }

    @post('media/configure_sidecar/')
    def __configure_album(self, media, caption_text=''):
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

    @post('qe/expose/')
    def __expose(self):
        return None, {
            'id': self.user_id,
            'experiment': 'ig_android_profile_contextual_feed',
        }
