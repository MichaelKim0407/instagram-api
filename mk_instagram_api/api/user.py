from ._base import *

__author__ = 'Michael'


class UserAPI(BaseAPI):
    @get('users/{user_id}/info/')
    def user_get_info(self, user_id):
        return {
            'user_id': user_id,
        }

    @get('users/{username}/usernameinfo/')
    def user_get_info_by_username(self, username):
        return {
            'username': username,
        }

    @get('users/search/', ranked=True)
    def user_search(self, query):
        return None, {
            'sig_key_version': constant.SIG_KEY_VERSION,
            'is_typeahead': 'true',
            'query': query,
        }

    @get('fbsearch/topsearch/', ranked=True)
    def user_search_fb(self, query):
        return None, {
            'context': 'blended',
            'query': query,
        }
