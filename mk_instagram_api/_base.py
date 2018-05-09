from typing import List

from ._global import get_api
from .api import InstagramAPI

__author__ = 'Michael'


class BaseObject(object):
    def __init__(self, api: InstagramAPI = None, **kwargs):
        self.api = get_api(api)

        self.__kwargs = kwargs
        self.__updated = False

    def __repr__(self):
        return "<{}>".format(self.__class__.__name__)

    def _update_info(self):
        new = self  # query new instance
        # update other properties here
        return new

    def update_info(self, force=False):
        if self.__updated and not force:
            return self

        new = self._update_info()
        self.__kwargs.update(new.__kwargs)
        self.__updated = True

    def __contains__(self, item):
        return item in self.__kwargs

    def __getitem__(self, item: str):
        if isinstance(item, slice):
            # self[:] returns full kwargs (for debugging)
            return self.__kwargs
        if item not in self.__kwargs:
            self.update_info()
        return self.__kwargs[item]

    def attributes_available(self) -> List[str]:
        self.update_info()
        return sorted(self.__kwargs.keys())

    @classmethod
    def cast_kwargs(cls, kwargs, *keys, api: InstagramAPI = None):
        if not keys:
            if isinstance(kwargs, dict):
                return cls(**kwargs, api=api)
            elif isinstance(kwargs, list):
                return [cls.cast_kwargs(item, api=api) for item in kwargs]
            else:
                return kwargs

        if not isinstance(kwargs, dict):
            return kwargs

        key = keys[0]
        if key not in kwargs:
            return kwargs
        kwargs[key] = cls.cast_kwargs(kwargs[key], *keys[1:], api=api)
        return kwargs
