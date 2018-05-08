from . import get_api

__author__ = 'Michael'


class User(object):
    def __init__(self, pk, username, api=None, **kwargs):
        self.api = get_api(api)

        self.user_id = pk
        self.username = username
        self.__kwargs = kwargs

        self.__updated = False

    def __repr__(self):
        return "User [{}] '{}'".format(self.user_id, self.username)

    @staticmethod
    def get_by_id(user_id, api=None):
        api = get_api(api)
        return User(**api.user_get_info(user_id)['user'], api=api)

    @staticmethod
    def get_by_name(username, api=None):
        api = get_api(api)
        return User(**api.user_get_info_by_username(username)['user'], api=api)

    def update_info(self, force=False):
        if self.__updated and not force:
            return self

        user = self.get_by_id(self.user_id, self.api)
        self.username = user.username
        self.__kwargs.update(user.__kwargs)
        self.__updated = True
        return self

    def __getitem__(self, item):
        if item not in self.__kwargs:
            self.update_info()
        return self.__kwargs[item]

    def attributes_available(self):
        self.update_info()
        return sorted(self.__kwargs.keys())


class LoggedInUser(User):
    __instances = {}

    def __init__(self, api=None):
        api = get_api(api)
        super().__init__(**api.logged_in_user, api=api)
        self.__instances[api] = self

    @staticmethod
    def get(api=None):
        api = get_api(api)
        if api in LoggedInUser.__instances:
            return LoggedInUser.__instances[api]
        else:
            return LoggedInUser(api)
