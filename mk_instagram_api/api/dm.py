import os

from ._base import *

__author__ = 'Michael'


class MessagingAPI(BaseAPI):
    @get('direct_v2/inbox/')
    def dm_get_inbox(self):
        pass

    @get('direct_v2/threads/{thread}')
    def dm_get_thread(self, thread, cursor=None):
        return {
                   'thread': thread,
               }, {
                   'cursor': cursor,
               }

    @get('direct_share/inbox/')
    def dm_get_share(self):
        pass

    @staticmethod
    def __build_body(bodies, boundary):
        body = u''
        for b in bodies:
            body += u'--{boundary}\r\n'.format(boundary=boundary)
            body += u'Content-Disposition: {b_type}; name="{b_name}"'.format(b_type=b['type'], b_name=b['name'])
            _filename = b.get('filename', None)
            _headers = b.get('headers', None)
            if _filename:
                _filename, ext = os.path.splitext(_filename)
                body += u'; filename="pending_media_{uid}.{ext}"'.format(uid=util.generate_upload_id(), ext=ext)
            if _headers and isinstance(_headers, list):
                for h in _headers:
                    body += u'\r\n{header}'.format(header=h)
            body += u'\r\n\r\n{data}\r\n'.format(data=b['data'])
        body += u'--{boundary}--'.format(boundary=boundary)
        return body

    @endpoint('direct_v2/threads/broadcast/text/')
    def dm_send_text(self, text, recipients):
        uri = 'direct_v2/threads/broadcast/text/'

        if not isinstance(recipients, list):
            recipients = [str(recipients)]
        recipient_users = '"",""'.join(str(r) for r in recipients)
        boundary = self.uuid
        bodies = [
            {
                'type': 'form-data',
                'name': 'recipient_users',
                'data': '[["{}"]]'.format(recipient_users),
            },
            {
                'type': 'form-data',
                'name': 'client_context',
                'data': self.uuid,
            },
            {
                'type': 'form-data',
                'name': 'thread',
                'data': '["0"]',
            },
            {
                'type': 'form-data',
                'name': 'text',
                'data': text or '',
            },
        ]
        data = self.__build_body(bodies, boundary)
        with self._update_headers({
            'Connection': 'keep-alive',
            'Content-Type': 'multipart/form-data; boundary={}'.format(boundary),
            'Proxy-Connection': 'keep-alive',
        }):
            # self.SendRequest(endpoint,post=data) #overwrites 'Content-type' header and boundary is missed
            response = self.session.post(
                constant.API_URL + uri,
                data=data
            )

        return self._handle_response(response)

    @endpoint('direct_v2/threads/broadcast/media_share/?media_type=photo')
    def dm_send_share(self, media_id, recipients, text=None):
        uri = 'direct_v2/threads/broadcast/media_share/?media_type=photo'

        if not isinstance(recipients, list):
            recipients = [str(recipients)]
        recipient_users = '"",""'.join(str(r) for r in recipients)
        boundary = self.uuid
        bodies = [
            {
                'type': 'form-data',
                'name': 'media_id',
                'data': media_id,
            },
            {
                'type': 'form-data',
                'name': 'recipient_users',
                'data': '[["{}"]]'.format(recipient_users),
            },
            {
                'type': 'form-data',
                'name': 'client_context',
                'data': self.uuid,
            },
            {
                'type': 'form-data',
                'name': 'thread',
                'data': '["0"]',
            },
            {
                'type': 'form-data',
                'name': 'text',
                'data': text or '',
            },
        ]
        data = self.__build_body(bodies, boundary)
        with self._update_headers({
            'User-Agent': constant.USER_AGENT,
            'Proxy-Connection': 'keep-alive',
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'Content-Type': 'multipart/form-data; boundary={}'.format(boundary),
            'Accept-Language': 'en-en',
        }):
            # self.SendRequest(endpoint,post=data) #overwrites 'Content-type' header and boundary is missed
            response = self.session.post(
                constant.API_URL + uri,
                data=data
            )

        return self._handle_response(response)
