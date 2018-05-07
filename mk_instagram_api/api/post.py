from ._base import *

__author__ = 'Michael'


class PostAPI(BaseAPI):
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
