from ._base import BaseObject
from ._global import get_api
from .api import InstagramAPI

__author__ = 'Michael'


class Post(BaseObject):
    PHOTO = 1
    VIDEO = 2
    ALBUM = 8
    POST_TYPE = {
        PHOTO: 'photo',
        VIDEO: 'video',
        ALBUM: 'album',
    }

    def __init__(self, pk: int, id: str, api: InstagramAPI = None, **kwargs):
        kwargs = User.cast_kwargs(kwargs, 'user', api=api)
        kwargs = User.cast_kwargs(kwargs, 'caption', 'user', api=api)
        kwargs = Post.cast_kwargs(kwargs, 'carousel_media')

        super().__init__(api, **kwargs)

        self.pk = pk
        self.id = id  # id = {pk}_{user_id}

    def __repr__(self):
        result = super().__repr__() + " [{}]".format(self.id)
        if 'user' in self:
            result += " by '{}'".format(self['user'].username)
        return result

    @staticmethod
    def get_by_id(pk_or_id, api: InstagramAPI = None) -> 'Post':
        api = get_api(api)
        return Post(**api.post_info(pk_or_id)['items'][0], api=api)

    def _update_info(self):
        new = Post.get_by_id(self.pk, self.api)
        self.id = new.id
        return new

    def type(self):
        return self.POST_TYPE[self['media_type']]

    def album(self) -> 'Post':
        if 'carousel_parent_id' not in self:
            return self
        return Post.get_by_id(self['carousel_parent_id'])

    def caption(self):
        if self['caption'] is None:
            return None
        return self['caption']['text']


from .user import User
