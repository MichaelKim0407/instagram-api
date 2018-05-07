import urllib.parse

from ._base import *

__author__ = 'Michael'


class FriendsAPI(BaseAPI):
    @get('friendships/autocomplete_user_list/')
    def auto_complete_user_list(self):
        pass

    @endpoint('friendships/{}/following/')
    def get_user_followings(self, user_id, max_id=''):
        url = 'friendships/{}/following/?'.format(user_id)
        query_string = {
            'ig_sig_key_version': constant.SIG_KEY_VERSION,
            'rank_token': self.rank_token,
        }
        if max_id:
            query_string['max_id'] = max_id
        url += urllib.parse.urlencode(query_string)
        return self.send_request(url)

    def get_self_user_followings(self):
        return self.get_user_followings(self.user_id)

    def get_total_followings(self, user_id):
        followers = []
        next_max_id = ''
        while True:
            temp = self.get_user_followings(user_id, next_max_id)

            for item in temp["users"]:
                followers.append(item)

            if temp["big_list"] is False:
                return followers
            next_max_id = temp["next_max_id"]

    def get_total_self_followings(self):
        return self.get_total_followings(self.user_id)

    @get('friendships/{user_id}/followers/', ranked=True)
    def get_user_followers(self, user_id, max_id=None):
        return {
                   'user_id': user_id,
               }, {
                   'max_id': max_id,
               }

    def get_self_user_followers(self):
        return self.get_user_followers(self.user_id)

    def get_total_followers(self, user_id):
        followers = []
        next_max_id = ''
        while True:
            temp = self.get_user_followers(user_id, next_max_id)

            for item in temp["users"]:
                followers.append(item)

            if temp["big_list"] is False:
                return followers
            next_max_id = temp["next_max_id"]

    def get_total_self_followers(self):
        return self.get_total_followers(self.user_id)

    @get('friendships/pending')
    def get_pending_follow_requests(self):
        pass

    @post('friendships/approve/{user_id}/')
    def approve(self, user_id):
        return {
            'user_id': user_id,
        }

    @post('friendships/ignore/{user_id}/')
    def ignore(self, user_id):
        return {
            'user_id': user_id,
        }

    @post('friendships/create/{user_id}/')
    def follow(self, user_id):
        return {
            'user_id': user_id,
        }

    @post('friendships/destroy/{user_id}/')
    def unfollow(self, user_id):
        return {
            'user_id': user_id,
        }

    @post('friendships/block/{user_id}/')
    def block(self, user_id):
        return {
            'user_id': user_id,
        }

    @post('friendships/unblock/{user_id}/')
    def unblock(self, user_id):
        return {
            'user_id': user_id,
        }

    @post('friendships/show/{user_id}/')
    def user_friendship(self, user_id):
        return {
            'user_id': user_id,
        }
