from typing import List, Iterable, Dict

from . import get_api, big_list
from .api import InstagramAPI

__author__ = 'Michael'


class User(object):
    def __init__(self, pk: int, username: str, api: InstagramAPI = None, **kwargs):
        self.api: InstagramAPI = get_api(api)

        self.user_id: int = pk
        self.username: str = username
        self.__kwargs = kwargs

        self.__updated = False

    def __repr__(self):
        return "User [{}] '{}'".format(self.user_id, self.username)

    @staticmethod
    def get_by_id(user_id: int, api: InstagramAPI = None) -> 'User':
        api = get_api(api)
        return User(**api.user_get_info(user_id)['user'], api=api)

    @staticmethod
    def get_by_name(username: str, api: InstagramAPI = None) -> 'User':
        api = get_api(api)
        return User(**api.user_get_info_by_username(username)['user'], api=api)

    @staticmethod
    def search_iter(value: str, fb=False, api: InstagramAPI = None) -> Iterable['User']:
        # TODO 'has_more' in result without 'next_max_id'
        api = get_api(api)
        if fb:
            for user in api.user_search_fb(value)['users']:
                yield User(**user['user'], api=api)
        else:
            for user in api.user_search(value)['users']:
                yield User(**user, api=api)

    @staticmethod
    def search(value: str, fb=False, api: InstagramAPI = None) -> List['User']:
        return list(User.search_iter(value, fb, api))

    def update_info(self, force: bool = False) -> 'User':
        if self.__updated and not force:
            return self

        user = self.get_by_id(self.user_id, self.api)
        self.username = user.username
        self.__kwargs.update(user.__kwargs)
        self.__updated = True
        return self

    def __getitem__(self, item: str):
        if item not in self.__kwargs:
            self.update_info()
        return self.__kwargs[item]

    def attributes_available(self) -> List[str]:
        self.update_info()
        return sorted(self.__kwargs.keys())

    def relationship(self) -> Dict[str, bool]:
        result = self.api.friends_get_user_relationships(self.user_id)
        del result['status']
        return result

    @big_list()
    def followings_iter(self, max_id) -> Iterable['User']:
        for user in self.api.friends_get_followings(self.user_id, max_id)['users']:
            yield User(**user, api=self.api)

    def followings(self) -> List['User']:
        return list(self.followings_iter())

    @big_list()
    def followers_iter(self, max_id) -> Iterable['User']:
        for user in self.api.friends_get_followers(self.user_id, max_id)['users']:
            yield User(**user, api=self.api)

    def followers(self) -> List['User']:
        return list(self.followers_iter())

    def follow(self, follow=True):
        if follow:
            self.api.friends_follow(self.user_id)
        else:
            self.api.friends_unfollow(self.user_id)

    def block(self, block=True):
        if block:
            self.api.friends_block(self.user_id)
        else:
            self.api.friends_unblock(self.user_id)

    def approve(self, approve=True):
        if approve:
            self.api.friends_approve_request(self.user_id)
        else:
            self.api.friends_ignore_request(self.user_id)


class LoggedInUser(User):
    class MethodAccessError(Exception):
        def __init__(self):
            super().__init__('Access this method through User class')

    __instances: Dict[InstagramAPI, 'LoggedInUser'] = {}

    def __init__(self, api: InstagramAPI = None):
        api = get_api(api)
        super().__init__(**api.logged_in_user, api=api)
        self.__instances[api] = self

    @staticmethod
    def get(api: InstagramAPI = None) -> 'LoggedInUser':
        api = get_api(api)
        if api in LoggedInUser.__instances:
            return LoggedInUser.__instances[api]
        else:
            return LoggedInUser(api)

    @staticmethod
    def get_by_id(user_id: int, api: InstagramAPI = None):
        raise LoggedInUser.MethodAccessError()

    @staticmethod
    def get_by_name(username: str, api: InstagramAPI = None):
        raise LoggedInUser.MethodAccessError()

    @staticmethod
    def search_iter(value: str, fb=False, api: InstagramAPI = None):
        raise LoggedInUser.MethodAccessError()

    @staticmethod
    def search(value: str, fb=False, api: InstagramAPI = None):
        raise LoggedInUser.MethodAccessError()

    @big_list()
    def friend_requests_iter(self, max_id) -> Iterable[User]:
        for user in self.api.friend_get_requests(max_id)['users']:
            yield User(**user, api=self.api)

    def friend_requests(self) -> List[User]:
        return list(self.friend_requests_iter())

    def set_private(self, private=False):
        if private:
            self.api.profile_set_private()
        else:
            self.api.profile_set_public()
