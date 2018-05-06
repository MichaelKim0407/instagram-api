__author__ = 'Michael'


class SentryBlockException(Exception):
    pass


class RequireLogin(Exception):
    def __init__(self):
        super().__init__('Not logged in!')


class AlbumSizeError(Exception):
    def __init__(self, size):
        self.size = size
        super().__init__(
            'Instagram requires that albums contain 2-10 items. '
            'You tried to submit {}.'.format(size)
        )


class AlbumMediaContentError(Exception):
    def __init__(self, index):
        self.index = index
        super().__init__(
            'Media at index "{}" does not have the required "file" and "type" keys.'.format(index)
        )


class AlbumMediaTypeError(Exception):
    def __init__(self, type):
        self.type = type
        super().__init__(
            'Unsupported album media type "{}".'.format(type)
        )
