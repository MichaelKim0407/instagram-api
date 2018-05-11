from ._base import *

__author__ = 'Michael'


class StoryAPI(LoginAPI):
    @get('feed/user/{user_id}/reel_media/')
    def stories_get_user(self, user_id):
        return {
            'user_id': user_id,
        }
