from ._base import *

__author__ = 'Michael'


class MiscAPI(BaseAPI):
    @post('/qe/sync/')
    def sync_features(self):
        return None, {
            'id': self.user_id,
            'experiments': constant.EXPERIMENTS,
        }

    @get('megaphone/log/')
    def megaphone_log(self):
        pass

    @get('discover/explore/')
    def explore(self):
        pass

    @get('feed/popular/', ranked=True)
    def popular(self):
        return None, {
            'people_teaser_supported': 1,
        }

    @endpoint('address_book/link/?include=extra_display_name,thumbnails')
    def sync_from_address_book(self, contacts):
        uri = 'address_book/link/?include=extra_display_name,thumbnails'

        return self.send_request(
            uri,
            "contacts={}".format(
                json.dumps(contacts)
            )
        )

    def backup(self):
        # TODO Instagram.php 1470-1485
        raise NotImplementedError()
