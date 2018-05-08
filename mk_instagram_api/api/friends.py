from ._base import *

__author__ = 'Michael'


class FriendsAPI(BaseAPI):
    @get('friendships/autocomplete_user_list/')
    def friends_autocomplete(self):
        pass

    @post('friendships/show/{user_id}/')
    def friends_get_user_relationships(self, user_id):
        return {
            'user_id': user_id,
        }

    # --- follow ---

    @get('friendships/{user_id}/following/', ranked=True)
    def friends_get_followings(self, user_id, max_id=None):
        return {
                   'user_id': user_id,
               }, {
                   'ig_sig_key_version': constant.SIG_KEY_VERSION,
                   'max_id': max_id,
               }

    @get('friendships/{user_id}/followers/', ranked=True)
    def friends_get_followers(self, user_id, max_id=None):
        return {
                   'user_id': user_id,
               }, {
                   'max_id': max_id,
               }

    @post('friendships/create/{user_id}/')
    def friends_follow(self, user_id):
        return {
            'user_id': user_id,
        }

    @post('friendships/destroy/{user_id}/')
    def friends_unfollow(self, user_id):
        return {
            'user_id': user_id,
        }

    # --- requests ---

    @get('friendships/pending')
    def friend_get_requests(self, max_id=None):
        return None, {
            'max_id': max_id,
        }

    @post('friendships/approve/{user_id}/')
    def friends_approve_request(self, user_id):
        return {
            'user_id': user_id,
        }

    @post('friendships/ignore/{user_id}/')
    def friends_ignore_request(self, user_id):
        return {
            'user_id': user_id,
        }

    # --- block ---

    @post('friendships/block/{user_id}/')
    def friends_block(self, user_id):
        return {
            'user_id': user_id,
        }

    @post('friendships/unblock/{user_id}/')
    def friends_unblock(self, user_id):
        return {
            'user_id': user_id,
        }
