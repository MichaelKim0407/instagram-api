from .api import InstagramAPI

__author__ = 'Michael'

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
