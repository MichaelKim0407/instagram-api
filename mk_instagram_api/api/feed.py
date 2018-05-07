from ._base import *

__author__ = 'Michael'


class FeedAPI(BaseAPI):
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
