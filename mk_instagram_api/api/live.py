from ._base import *

__author__ = 'Michael'


class LiveAPI(BaseAPI):
    @post('live/create/')
    def create_broadcast(self, preview_width=1080, preview_height=1920, broadcast_message=''):
        return None, {
            'preview_height': preview_height,
            'preview_width': preview_width,
            'broadcast_message': broadcast_message,
            'broadcast_type': 'RTMP',
            'internal_only': 0,
        }

    @post('live/{broadcast_id}/start')
    def start_broadcast(self, broadcast_id, send_notification=False):
        return {
                   'broadcast_id': broadcast_id,
               }, {
                   'should_send_notifications': int(send_notification),
               }

    @post('live/{broadcast_id}/end_broadcast/')
    def stop_broadcast(self, broadcast_id):
        return {
                   'broadcast_id': broadcast_id,
               }, None

    @post('live/{broadcast_id}/add_to_post_live/')
    def add_broadcast_to_live(self, broadcast_id):
        # broadcast has to be ended first!
        return {
                   'broadcast_id': broadcast_id,
               }, None
