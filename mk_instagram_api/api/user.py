from ._base import *

__author__ = 'Michael'


class UserAPI(BaseAPI):
    @get('users/{user_id}/info/')
    def get_username_info(self, user_id):
        return {
            'user_id': user_id,
        }

    def get_self_username_info(self):
        return self.get_username_info(self.user_id)

    @get('users/search/', ranked=True)
    def search_users(self, query):
        return None, {
            'sig_key_version': constant.SIG_KEY_VERSION,
            'is_typeahead': 'true',
            'query': query,
        }

    @get('users/{username}/usernameinfo/')
    def search_username(self, username):
        return {
            'username': username,
        }
