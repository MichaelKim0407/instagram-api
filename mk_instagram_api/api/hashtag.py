from ._base import *

__author__ = 'Michael'


class HashtagAPI(LoginAPI):
    @get('feed/tag/{tag}/', ranked=True)
    def hashtag_feed(self, hashtag, max_id=None):
        return {
                   'tag': hashtag,
               }, {
                   'max_id': max_id,
               }

    @get('tags/search/', ranked=True)
    def hashtag_search(self, query):
        return None, {
            'is_typeahead': 'true',
            'q': query,
        }
