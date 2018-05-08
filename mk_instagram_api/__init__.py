__author__ = 'Michael'

__version__ = '0.0.0'

from .api import InstagramAPI

__api_global: InstagramAPI = None


class NoGlobalAPI(Exception):
    pass


def login(username: str, password: str) -> InstagramAPI:
    global __api_global
    __api_global = InstagramAPI(username, password)
    __api_global.login()
    return __api_global


def get_api(api: InstagramAPI = None) -> InstagramAPI:
    if api is not None:
        return api
    if __api_global is None:
        raise NoGlobalAPI()
    return __api_global


class big_list(object):
    def __init__(self, big_key='big_list', next_key='next_max_id'):
        self.big_key = big_key
        self.next_key = next_key

    def __call__(self, method):
        def __new_method(_self, **kwargs):
            max_id = None
            while True:
                for i in method(_self, **kwargs, max_id=max_id):
                    yield i
                if not _self.api.last_json[self.big_key]:
                    break
                max_id = _self.api.last_json[self.next_key]

        return __new_method


from .user import User, LoggedInUser
