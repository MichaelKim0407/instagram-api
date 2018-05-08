from ._base import *

__author__ = 'Michael'


class LocationAPI(BaseAPI):
    @get('feed/location/{location_id}/', ranked=True)
    def location_feed(self, location_id, max_id=None):
        return {
                   'location_id': location_id,
               }, {
                   'max_id': max_id
               }

    @get('maps/user/{user_id}/')
    def location_of_user(self, user_id):
        return {
            'user_id': user_id,
        }

    @get('fbsearch/places/', ranked=True)
    def location_search(self, query):
        return None, {
            'query': query,
        }
