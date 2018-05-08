__author__ = 'Michael'

__version__ = '0.0.0'

from .api import InstagramAPI

__api_global: InstagramAPI = None


class NoGlobalAPI(Exception):
    pass


def login(username, password) -> InstagramAPI:
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


from .user import User, LoggedInUser
