__author__ = 'Michael'


class big_list(object):
    def __init__(self, big_key='big_list', next_key='next_max_id'):
        self.big_key = big_key
        self.next_key = next_key

    def __call__(self, method):
        def __new_method(api, limit=None, **kwargs):
            count = 0
            max_id = None
            while True:
                for i in method(api, **kwargs, max_id=max_id):
                    yield i
                    count += 1
                if limit is not None and count >= limit:
                    # we do not want to leave out part of the response
                    # so the actual count can go over limit
                    break
                if not api.last_json[self.big_key]:
                    break
                max_id = api.last_json[self.next_key]

        return __new_method
