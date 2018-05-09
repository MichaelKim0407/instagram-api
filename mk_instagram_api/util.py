__author__ = 'Michael'


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
