from .activity import ActivityAPI
from .dm import MessagingAPI
from .friends import FriendsAPI
from .hashtag import HashtagAPI
from .live import LiveAPI
from .location import LocationAPI
from .misc import MiscAPI
from .post import PostAPI
from .profile import ProfileAPI
from .story import StoryAPI
from .upload import UploadAPI
from .user import UserAPI


class InstagramAPI(
    ActivityAPI,
    MessagingAPI,
    FriendsAPI,
    HashtagAPI,
    LiveAPI,
    LocationAPI,
    PostAPI,
    ProfileAPI,
    StoryAPI,
    UploadAPI,
    UserAPI,
    MiscAPI
):
    pass
