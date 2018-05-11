from ._base import *

__author__ = 'Michael'


class PostAPI(LoginAPI):
    @post('media/{media_id}/info/')
    def post_info(self, media_id):
        return {
            'media_id': media_id,
        }

    @get('feed/user/{user_id}/', ranked=True)
    def posts_by_user(self, user_id, max_id=None, min_timestamp=None):
        return {
                   'user_id': user_id,
               }, {
                   'max_id': max_id,
                   'min_timestamp': min_timestamp,
               }

    @get('feed/timeline/', ranked=True)
    def posts_feed(self):
        pass

    @post('media/{media_id}/edit_media/')
    def post_edit(self, media_id, caption_text=''):
        return {
                   'media_id': media_id,
               }, {
                   'caption_text': caption_text,
               }

    @post('media/{media_id}/delete/')
    def post_delete(self, media_id, media_type=1):
        return {
            'media_type': media_type,
            'media_id': media_id,
        }

    # --- like ---

    @get('media/{media_id}/likers/')
    def post_get_likes(self, media_id):
        return {
            'media_id': media_id,
        }

    @get('feed/liked/')
    def posts_liked(self, max_id=None):
        return None, {
            'max_id': max_id,
        }

    @post('media/{media_id}/like/')
    def post_like(self, media_id):
        return {
            'media_id': media_id,
        }

    @post('media/{media_id}/unlike/')
    def post_unlike(self, media_id):
        return {
            'media_id': media_id,
        }

    # --- save ---

    @get('feed/saved')
    def posts_saved(self, max_id=None):
        return None, {
            'max_id': max_id,
        }

    @post('media/{media_id}/save/')
    def post_save(self, media_id):
        return {
            'media_id': media_id,
        }

    @post('media/{media_id}/unsave/')
    def post_unsave(self, media_id):
        return {
            'media_id': media_id,
        }

    # --- comments ---

    @get('media/{media_id}/comments/')
    def post_get_comments(self, media_id, max_id=None):
        return {
                   'media_id': media_id,
               }, {
                   'max_id': max_id,
               }

    @post('media/{media_id}/comment/')
    def post_comment(self, media_id, comment_text):
        return {
                   'media_id': media_id,
               }, {
                   'comment_text': comment_text,
               }

    @post('media/{media_id}/comment/{comment_id}/delete/')
    def post_delete_comment(self, media_id, comment_id):
        return {
            'media_id': media_id,
            'comment_id': comment_id,
        }

    # --- user tagging ---

    @get('usertags/{user_id}/feed/', ranked=True)
    def posts_tagging_user(self, user_id):
        return {
            'user_id': user_id,
        }

    @post('media/{media_id}/remove/')
    def post_remove_tag_me(self, media_id):
        return {
                   'media_id': media_id,
               }, None
