from ._base import *

__author__ = 'Michael'


class MiscAPI(BaseAPI):
    @post('/qe/sync/')
    def sync_features(self):
        return None, {
            'id': self.user_id,
            'experiments': constant.EXPERIMENTS,
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
