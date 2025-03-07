import os
import string
from enum import Enum, IntEnum

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class BrandReportType(IntEnum):
    DUPLICATE = 1
    FALSE_INFO = 2
    MANAGER_BEHAVIOR = 3
    NONEXISTENT = 4
    OWNERSHIP_CLAIM = 5


class ClientDeviceType(IntEnum):
    UNDEFINED = 0
    DESKTOP = 1
    PHONE = 2
    TABLET = 3


class Configuration:
    ALIAS_MIN_LEN = 1
    ALIAS_MAX_LEN = 64
    ALLOWED_AVATAR_FILE_EXTENSIONS = frozenset(["gif", "jpeg", "jpg", "png"])
    ALLOWED_PRODUCT_MEDIA_FILE_EXTENSIONS = frozenset(["gif", "jpeg", "jpg", "png"])
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    ATTRIBUTION_MAX_LEN = 512
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_EC2_PROD_DATABASE_HOST = os.getenv("AWS_EC2_PROD_DATABASE_HOST")
    AWS_EC2_PROD_PASSWORD = os.getenv("AWS_EC2_PROD_PASSWORD")
    AWS_S3_MEDIA_BUCKET_NAME = os.getenv("AWS_S3_MEDIA_BUCKET_NAME")
    AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "971town")
    DATABASE_USER = os.getenv("DATABASE_USER", "postgres")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    DESCRIPTION_MAX_LEN = 512
    NAME_MAX_LEN = 128
    PRODUCT_MEDIA_MAX_COUNT = 6
    SERVICE_NAME = "971town"
    TAG_ILLEGAL_CHARACTERS = frozenset(string.punctuation)
    TAG_MAX_COUNT = 64  # Tags in total
    TAG_MAX_LEN = 64    # Characters per tag
    TESTING_OTP = os.getenv("TESTING_OTP")  # Only used in development
    TESTING_PHONE_NUMBER = os.getenv("TESTING_PHONE_NUMBER")  # Only used in development
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    URL_MAX_LEN = 512
    USER_ACCOUNT_MAX_COUNT = 10
    USER_VERIFICATION_CODE_ATTEMPT_LIMIT = 3
    USER_VERIFICATION_CODE_LEN = 6
    USER_VERIFICATION_CODE_PURGE_INTERVAL = 60  # Seconds
    USER_VERIFICATION_CODE_TTL = 1800  # Seconds
    # --
    STATIC_DIR = os.path.join(APP_ROOT, "static")
    MEDIA_DIR = os.path.join(STATIC_DIR, "media")
    BRAND_MEDIA_DIR = os.path.join(MEDIA_DIR, "brand")
    PRODUCT_MEDIA_DIR = os.path.join(MEDIA_DIR, "product")


class ContentVisibility(IntEnum):
    PUBLICLY_VISIBLE = 1
    DELETED = 2    # Removed by content creator
    GHOSTED = 3    # Hidden by manager/admin from regular users
    REMOVED = 4    # Removed by manager/admin


class DatabaseTable(str, Enum):
    ADMIN_USER_ACCOUNT = "admin_user_account_"
    ALIAS = "alias_"
    BADGE = "badge_"
    BRAND = "brand_"
    BRAND_EDIT_HISTORY = "brand_edit_history_"
    BRAND_MANAGER = "brand_manager_"
    BRAND_REPORT = "brand_report_"
    BRAND_TAG = "brand_tag_"
    BRAND_VIEW = "brand_view_"
    CONTINENT = "continent_"
    COUNTRY = "country_"
    COUNTRY_DIALING_CODE = "country_dialing_code_"
    CURRENCY = "currency_"
    LOCALITY = "locality_"
    PRODUCT = "product_"
    PRODUCT_COLOR = "product_color_"
    PRODUCT_EDIT_HISTORY = "product_edit_history_"
    PRODUCT_MANAGER = "product_manager_"
    PRODUCT_MATERIAL = "product_material_"
    PRODUCT_MEDIUM = "product_medium_"
    PRODUCT_REPORT = "product_report_"
    PRODUCT_TAG = "product_tag_"
    PRODUCT_VIEW = "product_view_"
    PRODUCT_VOTE = "product_vote_"
    STORE = "store_"
    STORE_EDIT_HISTORY = "store_edit_history_"
    STORE_MANAGER = "store_manager_"
    STORE_PRODUCT = "store_product_"
    STORE_PRODUCT_HISTORY = "store_product_history_"
    STORE_REPORT = "store_report_"
    STORE_SHADOW_BAN = "store_shadow_ban_"
    STORE_TAG = "store_tag_"
    STORE_VIEW = "store_view_"
    TAG = "tag_"
    USER = "user_"
    USER_ACCOUNT = "user_account_"
    USER_ACCOUNT_BADGE = "user_account_badge_"
    USER_ACCOUNT_REPORT = "user_account_report_"
    USER_ACCOUNT_SESSION = "user_account_session_"
    USER_ACCOUNT_VIEW = "user_account_view_"
    USER_CLIENT = "user_client_"
    USER_OS = "user_os_"
    USER_PHONE_NUMBER = "user_phone_number_"
    USER_SHADOW_BAN = "user_shadow_ban_"
    USER_PHONE_NUMBER_VERIFICATION_CODE = "user_phone_number_verification_code_"


class EditAccessLevel(IntEnum):
    OPEN = 1       # Anyone can make view and make edits; applies to brands, products, and stores
    ARCHIVED = 2   # Cannot be edited by anyone, including managers, unless unarchived; applies to brands, products, stores, and posts
    LOCKED = 3     # Protected from edits by anyone, can be unlocked by managers/admins; applies to posts and comments
    PUBLICLY_ACCESSIBLE = 4   # Anyone can view but only managers can make edits; applies to brands, products, and stores


class EntityType(IntEnum):
    BRAND = 1
    PRODUCT = 2
    STORE = 3
    USER_ACCOUNT = 4


class Field(IntEnum):
    UNDEFINED = 0
    ALIAS = 1
    AVATAR = 2
    BRAND = 3
    BUILDING = 4
    CONDITION = 5
    COORDINATES = 6
    DESCRIPTION = 7
    EDIT_ACCESS_LEVEL = 8
    FLOOR = 9
    LOCALITY = 10
    MAIN_COLOR = 11
    MANAGER = 12
    MATERIAL = 13
    NAME = 14
    PARENT_PRODUCT = 15
    POST_ACCESS_LEVEL = 16
    POST_CODE = 17
    PRICE = 18
    PRODUCT = 19
    RELEASE_TIMESTAMP = 20
    STATUS = 21
    STORE = 22
    STORE_PRODUCT = 23
    STREET = 24
    TAGS = 25
    UNIT = 26
    UPC = 27
    URL = 28
    USER_ACCOUNT = 29
    VISIBILITY = 30
    WEBSITE = 31
    PREORDER_TIMESTAMP = 32
    DISPLAY_NAME_OVERRIDE = 33
    PRODUCT_MEDIA = 34
    PRODUCT_MEDIA_ATTRIBUTION = 35
    PRODUCT_MEDIA_INDEX = 36


class MediaMode(IntEnum):
    DARK = 1
    LIGHT = 2


class MediaType(IntEnum):
    IMAGE = 1
    VIDEO = 2


class ProductReportType(IntEnum):
    DUPLICATE = 1
    FALSE_INFO = 2
    MANAGER_BEHAVIOR = 3
    NONEXISTENT = 4
    OWNERSHIP_CLAIM = 5


class ProductStatus(IntEnum):
    AVAILABLE = 1
    COMING_SOON = 2
    DISCONTINUED = 3
    PREORDER = 4
    UNAVAILABLE = 5


class ProtocolKey(str, Enum):
    ACTION_ID = "action_id"
    ADDRESS = "address"
    ALIAS = "alias"
    ALPHA_2_CODE = "alpha_2_code"
    ALPHA_3_CODE = "alpha_3_code"
    ATTEMPTS = "attempts"
    ATTRIBUTION = "attribution"
    AVATAR = "avatar"
    AVATAR_DARK_MODE_FILE_PATH = "avatar_dark_path"
    AVATAR_LIGHT_MODE_FILE_PATH = "avatar_light_path"
    BIO = "bio"
    BRAND = "brand"
    BRANDS = "brands"
    BRAND_ID = "brand_id"
    BUILDING = "building"
    CLIENT = "client"
    CLIENT_ID = "client_id"
    CLIENT_VERSION = "client_version"
    CODE = "code"
    COMMENT = "comment"
    CONDITION = "condition"
    CONTINENT = "continent"
    CONTINENT_CODE = "continent_code"
    COORDINATES = "coordinates"
    COORDINATES_TEXT = "coordinates_txt"
    COUNTRIES = "countries"
    COUNTRY = "country"
    CREATION_TIMESTAMP = "creation_timestamp"
    CREATOR = "creator"
    CREATOR_ID = "creator_id"
    CURRENCY = "currency"
    CURRENCY_CODE = "currency_code"
    DIALING_CODE = "dialing_code"
    DIALING_CODE_ID = "dialing_code_id"
    DIALING_CODES = "dialing_codes"
    DESCRIPTION = "description"
    DEVICE_NAME = "device_name"
    DEVICE_TYPE = "device_type"
    EDIT_ACCESS_LEVEL = "edit_access_level"
    EDITOR_ID = "editor_id"
    ENTITY_TYPE = "entity_type"
    ERROR = "error"
    ERROR_CODE = "error_code"
    ERROR_MESSAGE = "error_message"
    FIELD_ID = "field_id"
    FIELD_VALUE = "field_value"
    FILE_PATH = "file_path"
    FLOOR = "floor"
    HEX = "hex"
    ID = "id"
    IDENTITY = "identity"
    IDENTITY_TYPE = "identity_type"
    IMPOSER_ID = "imposer_id"
    INDEX = "index"
    IP_ADDRESS = "ip_address"
    IS_ADMIN = "is_admin"
    IS_ENABLED = "is_enabled"
    IS_VERIFIED = "is_verified"
    LAST_ACTIVITY = "last_activity"
    LATITUDE = "latitude"
    LOCALITIES = "localities"
    LOCALITY = "locality"
    LOCALITY_ID = "locality_id"
    LOCATION = "location"
    LONGITUDE = "longitude"
    MAC_ADDRESS = "mac_address"
    MAIN_COLOR = "main_color"
    MAIN_COLOR_CODE = "main_color_code"
    MATERIAL = "material"
    MATERIAL_ID = "material_id"
    MEDIA = "media"
    MEDIA_MODE = "media_mode"
    MEDIA_TYPE = "media_type"
    MOBILE_CARRIER = "mobile_carrier"
    NAME = "name"
    NAME_CLEAN = "name_clean"
    NAME_LOWERCASE = "name_lc"
    NUMERIC_3_CODE = "numeric_3_code"
    FULL_NAME = "full_name"
    OFFSET = "offset"
    OS = "os"
    OS_ID = "os_id"
    OS_VERSION = "os_version"
    OVERRIDES_DISPLAY_NAME = "display_name_override"
    PARENT_PRODUCT = "parent_product"
    PARENT_PRODUCT_ID = "parent_product_id"
    PASSWORD = "password"
    PHONE_NUMBER = "phone_number"
    PHONE_NUMBER_ID = "phone_number_id"
    POST_CODE = "post_code"
    POSTGRES_SEARCH_ALIAS = "ts_alias"
    POSTGRES_SEARCH_NAME = "ts_name"
    PREORDER_TIMESTAMP = "preorder_timestamp"
    PRICE = "price"
    PRODUCT = "product"
    PRODUCT_COLORS = "product_colors"
    PRODUCT_COUNT = "product_count"
    PRODUCT_ID = "product_id"
    PRODUCT_MATERIALS = "product_materials"
    PRODUCT_VARIANT_COUNT = "product_variant_count"
    PRODUCT_VARIANTS = "product_variants"
    PRODUCTS = "products"
    QUERY = "query"
    RELEASE_TIMESTAMP = "release_timestamp"
    REP = "rep"
    REPORTER = "reporter"
    REPORTER_ID = "reporter_id"
    SCREEN_RESOLUTION = "screen_resolution"
    SESSIONS = "sessions"
    STATUS = "status"
    STORE = "store"
    STORE_ID = "store_id"
    STORE_PRODUCT = "store_product"
    STORE_PRODUCT_ID = "store_product_id"
    STORE_PRODUCTS = "store_products"
    STORES = "stores"
    STREET = "street"
    SYMBOL = "symbol"
    TAGS = "tags"
    TAG_ID = "tag_id"
    TIME_ZONE = "time_zone"
    TYPE = "type"
    UNIT = "unit"
    UPC = "upc"
    USER = "user"
    USERS = "users"
    USER_ID = "user_id"
    URL = "url"
    USER_ACCOUNT = "user_account"
    USER_ACCOUNT_ID = "user_account_id"
    USER_ACCOUNT_SESSION = "user_account_session"
    USER_ACCOUNT_SESSION_ID = "user_account_session_id"
    USER_ACCOUNTS = "user_accounts"
    VERIFICATION_CODE = "verification_code"
    VERSION = "version"
    VISIBILITY = "visibility"
    WEBSITE = "website"


class ResponseStatus(IntEnum):
    # Generic
    OK = 0
    BAD_REQUEST = 1
    FORBIDDEN = 2
    INTERNAL_SERVER_ERROR = 3
    NOT_FOUND = 4
    NOT_IMPLEMENTED = 5
    PAYLOAD_TOO_LARGE = 6
    TOO_MANY_REQUESTS = 7
    UNAUTHORIZED = 8
    # Specific
    ALIAS_EXISTS = 8
    ALIAS_INVALID = 10
    ALPHA_2_CODE_INVALID = 11
    BIO_INVALID = 12
    BRAND_NOT_FOUND = 13
    BRAND_TOO_SIMILAR = 14
    DESCRIPTION_INVALID = 15
    MEDIA_INVALID = 16
    MEDIA_UNSUPPORTED = 17
    NAME_INVALID = 18
    PASSWORD_INCORRECT = 19
    PASSWORD_INVALID = 20
    PHONE_NUMBER_NOT_FOUND = 21
    PHONE_NUMBER_INVALID = 22
    PHONE_NUMBER_UNVERIFIED = 23
    PRODUCT_NOT_FOUND = 24
    PRODUCT_TOO_SIMILAR = 25
    SESSION_INVALID = 26
    STORE_NOT_FOUND = 27
    STORE_PRODUCT_NOT_FOUND = 28
    STORE_TOO_SIMILAR = 29
    TAG_INVALID = 30
    UNSUPPORTED_CLIENT = 31
    URL_INVALID = 32
    USER_ACCOUNT_MAX_COUNT_REACHED = 33
    USER_ACCOUNT_NOT_FOUND = 34
    USER_ACCOUNT_SUSPENDED = 35
    VERIFICATION_CODE_EXPIRED = 36
    VERIFICATION_CODE_INCORRECT = 37
    VERIFICATION_CODE_NOT_FOUND = 38
    ATTRIBUTION_INVALID = 39


class StoreStatus(IntEnum):
    OPEN = 1
    OPENING_SOON = 2
    PERMANENTLY_CLOSED = 3
    TEMPORARILY_CLOSED = 4


class StoreProductStatus(IntEnum):
    AVAILABLE = 1
    DISCOUNTED = 2
    PREORDER = 3
    OUT_OF_STOCK = 4


class StoreReportType(IntEnum):
    CLOSED = 1
    DUPLICATE = 2
    FALSE_INFO = 3
    FALSE_PRICES = 4
    FALSE_PRODUCTS = 5
    MANAGER_BEHAVIOR = 6
    NONEXISTENT = 7
    OWNERSHIP_CLAIM = 8


class UserAction(IntEnum):
    UNDEFINED = 0
    ADDED = 1
    BANNED = 2
    DELETED = 3
    UNBANNED = 2
    UPDATED = 4


class UserAccountReportType(IntEnum):
    BEHAVIOR = 1
    SPAM = 2
    VANDALISM = 3
