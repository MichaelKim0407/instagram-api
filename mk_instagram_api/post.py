from ._base import BaseObject
from .api import InstagramAPI

__author__ = 'Michael'


class Post(BaseObject):
    def __init__(self, id: str, api: InstagramAPI = None, **kwargs):
        User.cast_kwargs(kwargs, 'user', api=api)
        User.cast_kwargs(kwargs, 'caption', 'user', api=api)

        super().__init__(api, **kwargs)

        self.id = id

    def __repr__(self):
        result = super().__repr__() + " [{}]".format(self.id)
        if 'user' in self:
            result += " by '{}'".format(self['user'].username)
        return result

    def caption(self):
        if self['caption'] is None:
            return None
        return self['caption']['text']


from .user import User
