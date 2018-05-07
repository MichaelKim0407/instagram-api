from .dm import MessagingAPI
from .feed import FeedAPI
from .friends import FriendsAPI
from .live import LiveAPI
from .misc import MiscAPI
from .post import PostAPI
from .profile import ProfileAPI
from .upload import UploadAPI
from .user import UserAPI


class InstagramAPI(
    ProfileAPI,
    FriendsAPI,
    UserAPI,
    FeedAPI,
    PostAPI,
    UploadAPI,
    MessagingAPI,
    LiveAPI,
    MiscAPI
):
    pass
