import os

from ._base import *

__author__ = 'Michael'


class MessagingAPI(BaseAPI):
    @get('direct_v2/inbox/')
    def get_v2_inbox(self):
        pass

    @get('direct_v2/threads/{thread}')
    def get_v2_threads(self, thread, cursor=None):
        return {
                   'thread': thread,
               }, {
                   'cursor': cursor,
               }

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
    def direct_message(self, text, recipients):
        if not isinstance(recipients, list):
            recipients = [str(recipients)]
        recipient_users = '"",""'.join(str(r) for r in recipients)
        endpoint = 'direct_v2/threads/broadcast/text/'
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
        self.session.headers.update({
            'User-Agent': constant.USER_AGENT,
            'Proxy-Connection': 'keep-alive',
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'Content-Type': 'multipart/form-data; boundary={}'.format(boundary),
            'Accept-Language': 'en-en',
        })
        # self.SendRequest(endpoint,post=data) #overwrites 'Content-type' header and boundary is missed
        response = self.session.post(
            constant.API_URL + endpoint,
            data=data
        )

        if response.status_code == 200:
            self.last_response = response
            return json.loads(response.text)

        raise ResponseError(response.status_code, response)

    @endpoint('direct_v2/threads/broadcast/media_share/?media_type=photo')
    def direct_share(self, media_id, recipients, text=None):
        if not isinstance(recipients, list):
            recipients = [str(recipients)]
        recipient_users = '"",""'.join(str(r) for r in recipients)
        endpoint = 'direct_v2/threads/broadcast/media_share/?media_type=photo'
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
        self.session.headers.update({
            'User-Agent': constant.USER_AGENT,
            'Proxy-Connection': 'keep-alive',
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'Content-Type': 'multipart/form-data; boundary={}'.format(boundary),
            'Accept-Language': 'en-en',
        })
        # self.SendRequest(endpoint,post=data) #overwrites 'Content-type' header and boundary is missed
        response = self.session.post(
            constant.API_URL + endpoint,
            data=data
        )

        return self.__handle_response(response)
