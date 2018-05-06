import calendar
import hashlib
import hmac
import urllib
import urllib.parse
import uuid
from datetime import datetime

from . import constant

__author__ = 'Michael'


def md5_hash(obj):
    m = hashlib.md5()
    m.update(obj)
    return m.hexdigest()


def generate_signature(data, skip_quote=False):
    if skip_quote:
        parsed_data = data
    else:
        parsed_data = urllib.parse.quote(data)
    signed_body = hmac.new(
        constant.IG_SIG_KEY.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest() + '.' + parsed_data
    return "ig_sig_key_version={}&&signed_body={}".format(
        constant.SIG_KEY_VERSION,
        signed_body
    )


def generate_device_id(seed):
    volatile_seed = "12345"
    return 'android-' + md5_hash(seed.encode('utf-8') + volatile_seed.encode('utf-8'))[:16]


def generate_uuid(hyphens=True):
    generated_uuid = str(uuid.uuid4())
    if hyphens:
        return generated_uuid
    else:
        return generated_uuid.replace('-', '')


def generate_upload_id():
    return str(calendar.timegm(datetime.utcnow().utctimetuple()))
