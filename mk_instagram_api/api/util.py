import calendar
import hashlib
import hmac
import imghdr
import struct
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
    signed_body = '{}.{}'.format(
        hmac.new(
            constant.IG_SIG_KEY.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest(),
        parsed_data
    )
    return "ig_sig_key_version={}&&signed_body={}".format(
        constant.SIG_KEY_VERSION,
        signed_body
    )


def generate_device_id(seed):
    volatile_seed = "12345"
    return 'android-{}'.format(
        md5_hash(seed.encode('utf-8') + volatile_seed.encode('utf-8'))[:16]
    )


def generate_uuid(hyphens=True):
    generated_uuid = str(uuid.uuid4())
    if hyphens:
        return generated_uuid
    else:
        return generated_uuid.replace('-', '')


def generate_upload_id():
    return str(calendar.timegm(datetime.utcnow().utctimetuple()))


def get_image_size(fname):
    with open(fname, 'rb') as fhandle:
        head = fhandle.read(24)
        if len(head) != 24:
            raise RuntimeError("Invalid Header")
        if imghdr.what(fname) == 'png':
            check = struct.unpack('>i', head[4:8])[0]
            if check != 0x0d0a1a0a:
                raise RuntimeError("PNG: Invalid check")
            width, height = struct.unpack('>ii', head[16:24])
        elif imghdr.what(fname) == 'gif':
            width, height = struct.unpack('<HH', head[6:10])
        elif imghdr.what(fname) == 'jpeg':
            fhandle.seek(0)  # Read 0xff next
            size = 2
            ftype = 0
            while not 0xc0 <= ftype <= 0xcf:
                fhandle.seek(size, 1)
                byte = fhandle.read(1)
                while ord(byte) == 0xff:
                    byte = fhandle.read(1)
                ftype = ord(byte)
                size = struct.unpack('>H', fhandle.read(2))[0] - 2
            # We are at a SOFn block
            fhandle.seek(1, 1)  # Skip `precision' byte.
            height, width = struct.unpack('>HH', fhandle.read(4))
        else:
            raise RuntimeError("Unsupported format")
        return width, height
