from ._base import *

__author__ = 'Michael'


class ActivityAPI(LoginAPI):
    @get('news/inbox/')
    def activities_for_me(self):
        pass

    @get('news/')
    def activities_of_following(self):
        pass
