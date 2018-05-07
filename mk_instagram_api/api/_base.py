import time

import json
import logging
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from . import constant
from . import util
from .exceptions import *

__author__ = 'Michael'

# Turn off InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger('mk_instagram_api.api')


class endpoint(object):
    def __init__(self, uri):
        self.uri = uri

    def __call__(self, method):
        return method


class get(endpoint):
    def __init__(self, uri, require_login=True, ranked=False):
        super().__init__(uri)
        self.require_login = require_login
        self.ranked = ranked

    def __call__(self, method):
        def __new_method(_self: 'BaseAPI', *args, **kwargs):
            result = method(_self, *args, **kwargs)
            if not isinstance(result, tuple):
                uri_params, params = result, None
            else:
                uri_params, params = result

            uri = self.uri
            if uri_params:
                uri = self.uri.format(**uri_params)

            if not params:
                params = {}
            if self.ranked:
                params.update({
                    'ranked_content': 'true',
                    'rank_token': _self.rank_token,
                })

            if params:
                uri += '?'
                for key, val in params.items():
                    if val is None:
                        continue
                    uri += '{}={}&'.format(key, val)

            return _self.send_request(
                uri,
                require_login=self.require_login
            )

        return __new_method


class post(endpoint):
    def __init__(self, uri, require_login=True):
        super().__init__(uri)
        self.require_login = require_login

    def __call__(self, method):
        def __new_method(_self: 'BaseAPI', *args, **kwargs):
            result = method(_self, *args, **kwargs)
            if not isinstance(result, tuple):
                uri_params = data = result
            else:
                uri_params, data = result

            uri = self.uri
            if uri_params:
                uri = self.uri.format(**uri_params)

            if not data:
                data = {}
            data.update({
                '_uuid': _self.uuid,
                '_uid': _self.user_id,
                '_csrftoken': _self.token,
            })

            return _self.send_request(
                uri,
                data=util.generate_signature(json.dumps(data)),
                require_login=self.require_login
            )

        return __new_method


class BaseAPI(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.device_id = self.__generate_device_id()
        self.uuid = util.generate_uuid()

        self.is_logged_in = False
        self.user_id = None

        self.session = requests.Session()
        self.last_response = None
        self.rank_token = None
        self.token = None

        self.retry = True
        self.retry_times = 3
        self.retry_interval = 5  # seconds

    def __generate_device_id(self):
        return util.generate_device_id(
            util.md5_hash(self.username.encode('utf-8') + self.password.encode('utf-8'))
        )

    def __generate_rank_token(self):
        return "{}_{}".format(
            self.user_id,
            self.uuid
        )

    def __handle_response(self, response):
        if response.status_code == 200:
            self.last_response = response
            return json.loads(response.text)

        try:
            # check for sentry block
            result = json.loads(response.text)
            if 'error_type' in result and result['error_type'] == 'sentry_block':
                raise SentryBlockError(result['message'])
        except SentryBlockError:
            raise
        except Exception:
            pass

        raise ResponseError(response.status_code, response)

    def configure_retry(self, retry=None, retry_times=None, retry_interval=None):
        if retry is not None:
            self.retry = bool(retry)
        if retry_times is not None:
            self.retry_times = retry_times
        if retry_interval is not None:
            self.retry_interval = retry_interval

    def set_proxy(self, proxy=None):
        """
        Set proxy for all requests::

        Proxy format - user:password@ip:port
        """
        if proxy is not None:
            logger.info('Set proxy!')
            proxies = {
                'http': proxy,
                'https': proxy,
            }
            self.session.proxies.update(proxies)

    def send_request(self, uri, data=None, require_login=True):
        verify = False  # don't show request warning

        if not self.is_logged_in and require_login:
            raise RequireLogin()

        self.session.headers.update({
            'Connection': 'close',
            'Accept': '*/*',
            'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie2': '$Version=1',
            'Accept-Language': 'en-US',
            'User-Agent': constant.USER_AGENT,
        })

        retry_times = 0
        while True:
            try:
                retry_times += 1

                if data is not None:
                    response = self.session.post(
                        constant.API_URL + uri,
                        data=data,
                        verify=verify
                    )
                else:
                    response = self.session.get(
                        constant.API_URL + uri,
                        verify=verify
                    )

                return self.__handle_response(response)
            except ResponseError as e:
                if not self.retry:
                    raise
                if retry_times >= self.retry_times:
                    raise
                logger.warning('Endpoint: {}; Response code: {}; retrying #{}...'.format(
                    uri,
                    e.status_code,
                    retry_times
                ))
                time.sleep(self.retry_interval)

    def __get_csrftoken(self):
        return self.last_response.cookies['csrftoken']

    @get('si/fetch_headers/', require_login=False)
    def __fetch_headers(self, guid=None):
        if guid is None:
            guid = util.generate_uuid(False)
        return None, {
            'challenge_type': 'signup',
            'guid': guid,
        }

    @post('accounts/login/', require_login=False)
    def __login(self, phone_id=None, csrftoken=None):
        if phone_id is None:
            phone_id = util.generate_uuid()
        if csrftoken is None:
            csrftoken = self.__get_csrftoken()
        return None, {
            'phone_id': phone_id,
            '_csrftoken': csrftoken,
            'username': self.username,
            'guid': self.uuid,
            'device_id': self.device_id,
            'password': self.password,
            'login_attempt_count': '0',
        }

    def login(self, force=False):
        if self.is_logged_in and not force:
            return

        self.__fetch_headers()

        result = self.__login()

        self.is_logged_in = True
        self.user_id = result["logged_in_user"]["pk"]
        self.rank_token = self.__generate_rank_token()
        self.token = self.last_response.cookies["csrftoken"]
        logger.info("Logged in as [{}] {}".format(self.user_id, self.username))

        return result

    @get('accounts/logout/')
    def __logout(self):
        pass

    def logout(self):
        result = self.__logout()
        self.is_logged_in = False
        logger.info("Logged out")
        return result
