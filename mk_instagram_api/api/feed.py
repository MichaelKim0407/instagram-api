from ._base import *

__author__ = 'Michael'


class FeedAPI(BaseAPI):
    @get('feed/user/{user_id}/reel_media/')
    def feed_get_stories(self, user_id):
        return {
            'user_id': user_id,
        }

    @get('feed/saved')
    def feed_get_saved(self):
        pass

    @get('feed/tag/{tag}/', ranked=True)
    def feed_get_hashtag(self, hashtag, max_id=None):
        return {
                   'tag': hashtag,
               }, {
                   'max_id': max_id,
               }

    @get('feed/timeline/', ranked=True)
    def feed_get_following(self):
        pass

    @get('feed/user/{user_id}/', ranked=True)
    def feed_get_posts(self, user_id, max_id=None, min_timestamp=None):
        return {
                   'user_id': user_id,
               }, {
                   'max_id': max_id,
                   'min_timestamp': min_timestamp,
               }

    @get('feed/location/{location_id}/', ranked=True)
    def feed_get_location(self, location_id, max_id=None):
        return {
                   'location_id': location_id,
               }, {
                   'max_id': max_id
               }

    @get('feed/popular/', ranked=True)
    def feed_get_popular(self):
        return None, {
            'people_teaser_supported': 1,
        }

    @get('feed/liked/')
    def feed_get_my_likes(self, max_id=None):
        return None, {
            'max_id': max_id,
        }
