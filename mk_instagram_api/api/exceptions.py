__author__ = 'Michael'


class ResponseError(Exception):
    def __init__(self, response):
        self.status_code = response.status_code
        self.response = response
        super().__init__(self._text())

    def _text(self):
        if self.status_code == 404:
            return '404: The item you are requesting does not exist'
        return 'Request failed with code {}'.format(self.status_code)

    def should_retry(self):
        if 400 <= self.status_code < 500:
            return False
        return True


class SentryBlockError(ResponseError):
    def __init__(self, response, message):
        self.message = message
        super().__init__(response)

    def _text(self):
        return self.message

    def should_retry(self):
        return False


class RequireLogin(Exception):
    def __init__(self):
        super().__init__('Not logged in!')


class UploadFailed(Exception):
    pass


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
