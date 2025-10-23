"""constants"""

import re
from redis.exceptions import ConnectionError as RedisConnectionError
from django.db import DataError, DatabaseError
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from rest_framework import status
from rest_framework.response import Response
from decouple import config, UndefinedValueError
import googlemaps

COMMON_ERRORS = (
    AttributeError,
    ValueError,
    IndexError,
    DataError,
    DatabaseError,
    UndefinedValueError,
    KeyError,
    ObjectDoesNotExist,
    TypeError,
    RedisConnectionError,
)
GMAP_ERRORS = (
    googlemaps.exceptions.ApiError,
    googlemaps.exceptions.HTTPError,
    googlemaps.exceptions.Timeout,
    googlemaps.exceptions.TransportError,
    googlemaps.exceptions._OverQueryLimit,
    googlemaps.exceptions._RetriableRequest,
)
ERROR_TEMPLATE_URL = "dashboard/internal_error_template.html"
JSON_ERROR_OBJECT = JsonResponse(
    {"status": 1, "message": "Something went wrong"}
)
SOMETHING_WENT_WRONG = "Something went wrong"
OTP_SENT_SUCCESSFULLY = "OTP sent successfully"
INVALID_DATE_TIME = JsonResponse(
    {"status": 406, "message": "Please select valid date and time"}
)
API_ERROR_OBJECT = Response(
    {
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "status": False,
        "message": "Something went wrong",
    }
)
SEARCH_REGEX=r'^[a-zA-Z0-9\s-]+$'
SEARCH_AND_EMAIL_REGEX=r'^[a-zA-Z0-9\s\-_\.@]+$'
EMAIL_REGEX = "^([\\w|\\.|\\_\\-|\\+])+[@](\\w|\\_|\\-|\\.)+[.]\\w{2,63}$"
PASSWORD_REGEX = re.compile(
    "^(?=.*[a-z])(?=.*[A-Z])"
    "(?=.*\\d)(?=.*[@$!%*#?&])"
    "[A-Za-z\\d@$!#%*?&]{6,20}$"
)

REGEX={"email":"^([\\w|\\.|\\_\\-|\\+])+[@](\\w|\\_|\\-|\\.)+[.]\\w{2,63}$",
    "password":r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[\"'+,.:;<>_`|~!@#?£\-\$%\^&\*\{}\(\)\[\]\\\/])(?=.{8,})",
    "name":r"^[A-Za-z\-\'\s]+$",
    "user_name":"^[a-zA-Z0-9_.-]{3,20}$",
    "otp":r"^\d{4}$",
    # "postal_code":"^(GIR 0AA|[A-PR-UWYZ](\d{1,2}|([A-HK-Y]\d|\d[A-HJKPS-UW])|\d{1,2}[A-HJKS-UWY])) \d[A-BD-HJLNP-UW-Z]{2}$",
    "country":r"^[A-Za-z\s]+$",
    "user_token":"^[a-zA-Z0-9_.-]{3,90}$"}

YES = "Yes"
NO = "No"
ON_CONST = "on"
BLANK_SPACE_CONST = " "
TOKEN_COOKIE_MAX_AGE = 9000000
DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
ACTIVE = "Active"
COMING_SOON_CONST = "Coming soon"
ACTIVE_STATION_STATUSES = [ACTIVE, COMING_SOON_CONST]
TOKEN_EXPIRATION_TIME = 300
FLAG_TRUE = "True"
EXPORT_TRUE = "True"
EMPTY_CACHE_CHECK = "null"
GET_METHOD_ALLOWED = "GET"
POST_METHOD_ALLOWED = "POST"
CDN_SUCCESS_MESSAGE = "*********CDN cache purge request successful********"
CDN_FAIL_MESSAGE_STRING = (
    "*********CDN cache purge request failed with status code:"
)
CDN_ERROR_MESSAGE_STRING = "Error making CDN cache purge request:"
# default coordinates if failed to feth coordinates
DEFAULT_LATITUDE_FOR_PROMOTIONS_AND_STATION_FINDER = 55.378051
DEFAULT_LONGITUDE_FOR_PROMOTIONS_AND_STATION_FINDER = -3.435973
IS_EV_ID_KEY = "is_ev_id"
STATION_ID_KEY = "station_id"
NO_NEARBY_STATIONS_AVAILABLE = "No nearby stations available"
IS_EV_FLAG_TRUE = "true"
IS_EV_FLAG_FALSE = "false"

AZURE_BLOB_STORAGE_URL = config("DJANGO_APP_CDN_BASE_URL")
# constants for rendering access_types in decrators and filter_url
CONFIGURATION_CONST = "Configurations"
DASHBOARD_CONST = "Dashboard"
SITES_CONST = "Sites"
PROMOTIONS_CONST = "Promotions"
REVIEW_CONST = "Reviews"
AUDIT_TRAIL_CONST = "Audit trail"
USER_MANAGEMENT_CONST = "User Management"
RECONCILIATION_CONST = "Reconciliation"
TRANSACTIONS_CONST = "Payments"
LOYALTY_CONST = "Offers"
SESSION_PAYMENT_CONST = "Session Payments"
EWALLET = "E-Wallet"
AUDIT_TRAIL_CONST = "Audit trail"
BLOCK_APP_USERS_CONST = "Block App Users"
CONNECTORS_CONST = "Connectors"
SERVICES_CONST = "Services"
BASE_CONFIG_CONST = "Base Configurations"
OCPI_CONFIG_CONST = "OCPI Configurations"
MAP_MARKERS_CONST = "Map markers"
NOTIFICATION_CONST = "Notifications"
PUSH_NOTIFICATION_CONST = "Push Notifications"
PAYMENT_CONST = "Payment"
HOLD_PAYMENT_CONST = "Hold Payments"
THIRD_PARTY_DATA_IMPORT = "Thirdparty Data Import"
THREE_DS_CONFIG_CONST = "3DS Config"
THREE_DS_FOR_ALL_CONFIG_CONST = "3DS Config For All"
# cron job constants for charging statios
CRON_JOB_TIME_INTERVAL = 1

# time formatter constant
SINGLE_TIME_IDENTIFIER = 1

ROOT_URL = "root url"
# Baseconfiguration constants
MAPS_RADIUS = "Maps_nearby_radius"
OTP_LIMIT = "OTP_limit"
PAGINATION_COUNT = "Pagination_page_rows"
SEND_EMAIL_VALUE = "send_email_value"
SEND_EMAIL_NAME_VALUE = "send_email_name_value"
LIST_OF_ALLOWED_EXTENSION = "list_of_allowed_extensions"
EMAIL_NOTIFICATION_TOTAL_FILE_SIZE_LIMIT = (
    "email_notification_total_file_size_limit"
)
ACCEPT_EXTENSION = "accept_extension"
TEMPLATE_TYPE_LIST = "template_type_list"
USER_CATEGORY_LIST = "user_category_list"
NOTIFICATION_STATUS_LIST = "email_notification_status_list"
LIST_OF_EMAIL_PREFERENCE = "list_of_email_preference"
NOTIFICATIONS_EXPIRY_TIME_IN_HOURS = "notifications_expiry_time_in_hours"
SCREEN_NAME_FOR_PUSH_NOTIFICATION = "screen_name_for_push_notification"
LIST_OF_CATEGORY = "list_of_category"
LIST_OF_ASSIGN_TO = "list_of_assign_to"

# Default base congigurations for marketing emails
DEFAULT_LIST_OF_ALLOWED_EXTENSION = (
    '["xls","xlsx","csv","doc","docx","pdf","png","jpg","jpeg","ppt"]'
)
DEFAULT_EMAIL_NOTIFICATION_TOTAL_FILE_SIZE_LIMIT = "10"
DEFAULT_ACCEPT_EXTENSION = (
    ".xls,.xlsx,.csv,.doc ,.docx ,.pdf ,.png ,.jpg ,.jpeg ,.ppt"
)
DEFAULT_USER_CATEGORY_LIST = (
    '["All App Users","Specific Users","Postcode Specific"]'
)
DEFAULT_LIST_OF_EMAIL_PREFERENCE = (
    '["News Letter","Marketing Update","Promotions","EV Updates"]'
)
DEFAULT_NOTIFICATION_STATUS_LIST = (
    '["Scheduled", "Delivered", "Draft", "Failed"]'
)
# Default base congigurations for Push and InApp Notification
DEFAULT_LIST_OF_CATEGORY = '["Application"]'
DEFAULT_LIST_OF_ASSIGN_TO = (
    '["All App Users","Regions Specific","EV User","Domain Specific"]'
)
DEFAULT_LIST_OF_SCREENS = '["Loyalty", "Promotions"]'
DEFAULT_COUNT_SUBJECT = 60

# Baseconfiguration for Billing plan code and default value
DRIIVZ_PLAN_CODE = "Driivz_plan_code"
DEFAULT_DRIIVZ_PLAN_CODE = "MFG-Default-Plan"

# Email template constants
DELETE_ACCOUNT = "delete account"
DELETED_ACCOUNT = "account deleted"
FORGET_PASS_CONST = "forget"
LOGIN = "login"
REGISTER = "register"
BUYING_EMAIL = "Buying email"
NEW_LOGGED_IN_USER = "new user"
ADMIN_OTP = "admin otp"

class ConstantMessage:
    EMAIL_NOT_FOUND = "Email not found"
    FIRST_TIME_LOGIN = "Please set your password first"
    INVALID_PASSWORD = "Please enter valid password"
    OTP_SENT_SUCCESSFULLY = "OTP sent successfully"
    FAILED_SENDING_EMAIL = "Failed sending email"
    ACCOUNT_DEACTIVATED = "The account is deactivated"
    TRY_AGAIN = "Try once again"

    #Otp verification api
    INVALID_OTP = "Invalid OTP"
    OTP_LENGTH_INVALID = "OTP has to be exactly 4 digits"
    OTP_VERIFIED_SUCCESSFULLY = "OTP verified successfully"
    USER_NOT_FOUND = "User not found"
    SOMETHING_WENT_WRONG = "Something went wrong"
    OTP_EXPIRED = "OTP expired or invalid"

METER_TO_MILES_DIVIDER = 1.609 * 1000
MILES_TO_METER_MULTIPLIER = 1.609 * 1000
CHARGING_DEADPOINT = 15
EMERGENCY_CHARGING_GAP = 15

STATE_STATION_CHARGE = 90

STABLE_CHARGE_STATE = 15
PROMOTIONS_ARRAY_LIMIT = 4
PROMOTIONS_MAX_ARRAY_LIMIT = 4
DESTINATION_SOC = 20

DEFAULT_CONNECTOR_IMAGE = (
    "https://mfgevqastorage.blob.core.windows.net/static/images/mfg_logo22.png"
)
# Admin constants
SUPER_ADMIN = "Super admin"

# Markers names constants

MFG_RAPID = "MFG Ultra-Rapid"
MFG_NORMAL = "MFG Rapid"
OTHER_RAPID = "Other Ultra-Rapid"
OTHER_NORMAL = "Other Rapid"

LOADING = "Loading"
AVAILABLE = "Available"
OCCUPIED = "Occupied"
UNKNOWN = "Unknown"
# Trip constants
NAVIGATE_MODE = "driving"

# lat long constants  for tuples in polyline decode
LAT = "latitude"
LON = "longitude"

# Key validators
IS_MFG_KEYS = ["MFG EV", "MFG Forecourt", "MFG EV plus Forecourt"]
IS_EV_KEYS = ["MFG EV", "MFG EV plus Forecourt"]

# Following is the dictionary of urls for different sections

urls = {
    DASHBOARD_CONST: "/administrator/dashboard",
    SITES_CONST: "/administrator/stations/",
    PROMOTIONS_CONST: "/administrator/promotions/",
    REVIEW_CONST: "/administrator/reviews/",
    USER_MANAGEMENT_CONST: "/administrator/usermanagement/",
    CONFIGURATION_CONST: "/administrator/configurations/connectors/",
    RECONCILIATION_CONST: "/administrator/reconciliation/",
    TRANSACTIONS_CONST: "/administrator/session-transactions/",
    LOYALTY_CONST: "/administrator/offers/",
    AUDIT_TRAIL_CONST: "/administrator/audit-trail/?order_by_date=Descending",
    SESSION_PAYMENT_CONST: "/administrator/session-payments/",
    NOTIFICATION_CONST: "/administrator/notifications",
    EWALLET: "/administrator/wallet/",
    HOLD_PAYMENT_CONST: "/administrator/session-transactions/hold-payments-list/", 
    BLOCK_APP_USERS_CONST: "/administrator/app-users/block-app-users/",
    THIRD_PARTY_DATA_IMPORT:"/administrator/contactless/get-thirdparty-data/",
    THREE_DS_CONFIG_CONST:"/administrator/three-ds-config/",
}


# audit trail constants

APP_USER_DELETION = "APP_USER_DELETION"
APP_USER_MODULE = "APP_USER_MODULE"

# audit trail action constants
AUDIT_ADD_CONSTANT = "Create"
AUDIT_UPDATE_CONSTANT = "Update"
AUDIT_DELETE_CONSTANT = "Delete"


# History Constants
OLDER_TO_NEWER = "Older to newer"
NEWER_TO_OLDER = "Newer to older"

ALL_HISTORY = "All"
LAST_3_MONTH_HISTORY = "3 Months"
LAST_6_MONTH_HISTORY = "6 Months"

LAST_3_MONTH_HISTORY_VALUE = 3
LAST_6_MONTH_HISTORY_VALUE = 6

# electric vehicles constants
EV_MODEL_COMPARER_MATCH_PERCENTAGE = 60

GOOGLE_MAPS_EXCEPTION = (
    googlemaps.exceptions.ApiError,
    googlemaps.exceptions.TransportError,
    googlemaps.exceptions.HTTPError,
    googlemaps.exceptions.Timeout,
)

OTP_NUMBER_START_POINT = 1000
OTP_NUMBER_END_POINT = 9999
OTP_NUMBER_START_POINT_FOR_SMS = 100000
OTP_NUMBER_END_POINT_FOR_SMS = 999999
CONNECTOR_CLASS = "input-txt labels"
FORM_CONTAINER = "form-control my-2"
EXISTING_BACKOFFICE = "DRIIVZ"

# api return messages
SUCCESS_UPDATE = "Successfully updated"
CONNECTOR_ERROR = "Connector type and image are required fields."
UPLOAD_ERROR = "Error while Updating"
DELETE_ERROR = "Error while Deleting"
UPLOAD_UPDATE_SUCCESS = "Data has been updated"
INVALID_EMAIL = "Please enter valid email!!"
INVALID_CODE = "Incorrect Verification Code."
SESSION_CLOSED = "Session closed"
VEHICLE_ID_NOT_PROVIDED = "Vehicle id not provided."
VEHICLE_NOT_FOUND = "Vehicle with provided id not found."
VEHCILE_NOT_ADDED = "Provided vehicle was not added for user."
SUCCESS_CUSTOMERS = "successfully loaded customers"
SUCCESS_PAYMENT = "successfully receive payment"
SUCCESS_PROMOTIONS = "successfully loaded promotions"
# constants
SETTLEMENT_AMOUNT = "Settlement amount"
TRANSACTION_AMOUNT = "Transaction amount"
SORT_POSTIVIE_ERROR = "Sorting order must be a positive number."
SOMETHING_WRONG = "Something went wrong"
UNQUIE_BAR_CODE = "Unique/Barcode"
UNQUIE_RETAILBAR_CODE = "Retail Barcode"
STATION_ID = "Station ID"
UNQUIE_OPS_REGION = "Operation region"
ORDER_ID = "Order ID"
LOC_LAT = "Location Latitude"
LOC_LONG = "Location Longitude"
FUEL_BRANDS = "Fuel Brands"
OPS_REGION = "Ops Region"
REGIONAL_MANAGERS = "Regional Managers"
EMAIL_ADDRESS = "Email Address"
FOOD_TO_GO = "Food To Go"
ADDRESS_LINE_1 = "Address Line 1"
ADDRESS_LINE_2 = "Address Line 2"
ADDRESS_LINE_3 = "Address Line 3"
METHOD_MISMATCH = "Method mismatch"
NOT_AVAILABLE = "Not available"
HOURS_24 = "24 hours"


# loyalty db constants

IN_PROGRESS = "In progress"
QUEUED = "Queued"
COMEPLETED = "completed"
IN_PROGRESS = "In progress"
NEED_REVIEW = "Need review"
FAILED = "Failed"

LOYALTY_TYPES = ['Costa Coffee', 'Free']

# following constant used to set default string for EV power
# brands in default images functionality
EV_POWER_EXTENSION_FOR_DEFAULT_IMAGES = "& EV Power"
MFG_BRANDS = ["MFG", "EV Power"]

SWARCO = "SWARCO"
DRIIVZ = "DRIIVZ"

KWH = "kwh"
TOTAL_ENERGY = "totalEnergy"

DRIIVZ_STOP_ON = "stopOn"
DRIIVZ_START_ON = "startOn"
PAYTER_TIME_STAMP = "@timestamp"
SWARCO_END_TIME = "enddatetime"
SWARCO_START_TIME = "startdatetime"
CARD_PAYMENT_TIMELINE = "card_payment_timeline"
AUTHORIZED_AT = "authorized_at"
PUSH_NOTIFICATION_LOYALTY_TYPE = "Loyalty"

BILLED = "BILLED"
# payment failure error messages
RETRIEVE_PAYMENT_FAILED = "Failed to retrieve payment for payment id"
RETRIEVE_CUSTOMER_CARDS_FAILED = "Failed to retrieve customer cards"

# image sizes for different modules
STATION_INFO_IMAGE = "STATION_INFO_IMAGE"
EV_THUMBNAIL_IMAGE = "EV_THUMBNAIL_IMAGE"
EV_DETAIL_IMAGE = "EV_DETAIL_IMAGE"
PROMOTION_IMAGE = "PROMOTION_IMAGE"
LOYALTY_IMAGE = "LOYALTY_IMAGE"
EV_NOTIFICATION_IMAGE = "EV_NOTIFICATION_IMAGE"
LOYALTY_REWARD_IMAGE = "LOYALTY_REWARD_IMAGE"
THIRD_PARTY_SIGN_IN_PROFILE_PICTURE = "THIRD_PARTY_SIGN_IN_PROFILE_PICTURE"
MAP_MARKER_DEFAULT_IMAGE_SIZE = "MAP_MARKER_DEFAULT_IMAGE_SIZE"
MAP_MARKER_SMALL_IMAGE_SIZE = "MAP_MARKER_SMALL_IMAGE_SIZE"

# Image quality settings - using maximum quality for all images

SEVENTY_PERCENTAGE_QUALITY_COMPRESSION = 100
THIRTY_PERCENTAGE_QUALITY_COMPRESSION = 100
FULL_QUALITY_COMPRESSION = 100

IMAGE_SIZES_AND_QUALITY = {
    STATION_INFO_IMAGE: [(375, 175), SEVENTY_PERCENTAGE_QUALITY_COMPRESSION],
    EV_THUMBNAIL_IMAGE: [(120, 69), THIRTY_PERCENTAGE_QUALITY_COMPRESSION],
    EV_NOTIFICATION_IMAGE: [
        (572, 602),
        SEVENTY_PERCENTAGE_QUALITY_COMPRESSION,
    ],
    LOYALTY_REWARD_IMAGE: [
        (640, 640),
        100,
    ],
    EV_DETAIL_IMAGE: [(375, 210), SEVENTY_PERCENTAGE_QUALITY_COMPRESSION],
    PROMOTION_IMAGE: [
        (772, 332),
        SEVENTY_PERCENTAGE_QUALITY_COMPRESSION,
    ],
    LOYALTY_IMAGE: [
        (772, 332),
        SEVENTY_PERCENTAGE_QUALITY_COMPRESSION,
    ],
    THIRD_PARTY_SIGN_IN_PROFILE_PICTURE: [
        (100, 100),
        THIRTY_PERCENTAGE_QUALITY_COMPRESSION,
    ],
    MAP_MARKER_DEFAULT_IMAGE_SIZE: [
        (81, 102),
        None
    ],
    MAP_MARKER_SMALL_IMAGE_SIZE: [
        (59, 74),
        None
    ]
}

RGB_CONVERSION_MODE = "RGB"
JPEG_FORMAT = ".jpeg"
IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN = 4
NO_CARDS_ADDED_FOR_CUSTOMER = (
    "Customer do not have any added cards for payment"
)
FETCH_PAYMENT_CARDS_PROCESS_FAILED = "Failed to fetch customer cards"
CREATE_PAYMENT_PROCESS_FAILED = "Failed to create customer payment"
APPLE_GOOGLE_PAY_USED = "Apple/Google pay used; "

# transaction payment for types constants

WALLET_TRANSACTION_FOR_CONST = "Wallet"
LOYALTY_TRANSACTION_FOR_CONST = "Loyalty"

# transaction payment for sub type constants

LOAD_WALLET_TRANSACTION_FOR_CONST = "Load"
ACTIVATE_WALLET_TRANSACTION_FOR_CONST = "Activate"
REDEEM_WALLET_TRANSACTION_FOR_CONST = "Redeem"

# payments constants
ERROR_CONST = "errors"
CODE_CONST = "code"


# mail constants for template ids

# ****
# SESSION_FAILED_TEMPLATE_ID = (
#     "d-8d13c0797f904b0180e4c31f237bfff8"  # change this during deployment
# )
# AMOUNT_DUE_REMINDER_TEMPLATE_ID = (
#     "d-7c2ad21ab5be43fd9d113d1e2efbe716"  # change this during deployment
# )
# WALLET_CREDIT_TEMPLATE_ID = "d-2082755e41b648dd92d61e246b3270af"
# WALLET_ADMIN_CREDIT_TEMPLATE_ID = "d-a0510e0f002345fbb30cbbc6f3875872"
# WALLET_ADMIN_WITHDRAWL_TEMPLATE_ID = "d-a0510e0f002345fbb30cbbc6f3875872"
# ****

SESSION_FAILED_TEMPLATE_ID = config("DJANGO_APP_SESSION_FAILED_TEMPLATE_ID")
AMOUNT_DUE_REMINDER_TEMPLATE_ID = config(
    "DJANGO_APP_AMOUNT_DUE_REMINDER_TEMPLATE_ID"
)
WALLET_CREDIT_TEMPLATE_ID = config("DJANGO_APP_WALLET_CREDIT_TEMPLATE_ID")
WALLET_ADMIN_CREDIT_TEMPLATE_ID = config(
    "DJANGO_APP_WALLET_ADMIN_CREDIT_TEMPLATE_ID"
)
WALLET_ADMIN_WITHDRAWL_TEMPLATE_ID = config(
    "DJANGO_APP_WALLET_ADMIN_WITHDRAWL_TEMPLATE_ID"
)


# OTP constants
SMS_FROM_STRING = "mfg_custom_sms_sender_id"

DEFAULT_OTP_MESSAGE = """
Dear Customer, Your MFG Connect App verification code is: {{otp}}
"""
DEFAULT_FROM_SMS = "MFG CONNECT"

# Driivz api timeout
REQUEST_API_TIMEOUT = 300

# payments constants

GET_REQUEST = "GET"
POST_REQUEST = "POST"
PUT_REQUEST = "PUT"
PATCH_REQUEST = "PATCH"
DELETE_REQUEST = "DELETE"

SQUARE_BASE_URL = config("DJANGO_APP_SQUARE_APP_URL")
VALETING_KEY_WORDS = ["MOTOR_FUEL_LIMITED", "VALETING"]
VALETING_TAX_RATE = "valeting_tax_rate"
DEFAULT_VALETING_TAX_RATE = "20"

# charging session and payment constants
CHARGING_SESSION = "charging_session"
WALLET_TRANSACTIONS = "wallet_transaction"
NON_WALLET_TRANSACTIONS = "non_wallet_transaction"
CHARGING_SESSION = "charging_session"
COMBINED = "Combined"
PARTIAL = "Partial"
NON_WALLET = "non wallet"

# payter dataset constant
PAYTER_DAILY_DATASET_SIZE = "payter_daily_dataset_size"
DEFAULT_PAYTER_DAILY_DATASET_SIZE = 3000
VALETING_TAX_RATE = "valeting_tax_rate"
DEFAULT_VALETING_TAX_RATE = "20"
WORLDLINE_PAYMENT_TERMINAL = "Worldline"
PAYTER_PAYMENT_TERMINAL = "Payter"
ADVAM_PAYMENT_TERMINAL = "Advam"

#contactless error email constants
EMAIL_ID_FOR_ERROR_EMAIL_ALERT = "email_id_for_error_email_alert"
DEFAULT_EMAIL_ID_FOR_ERROR_EMAIL_ALERT = "mfgexceptions@sankeysolutions.com"
MFG_ADMIN = "MFG Admin"

"""loyalty constants"""
QR_CODE_ELEMENTS_ARRAY_SIZE = 14
PURCHASED = "Purchased"
REDEEMED = "Redeemed"
PURCHASED_ACTION_CODE = "P"
REDEEMED_ACTION_CODE = "R"
LOYALTY_TYPE = "L"
ACTIVE_LOYALTY_PRODUCTS = "Active"
SALE_AMOUNT = "saleAmount"
SALE_QUANTITY = "saleQuantity"
MFGEVCONNECT_CONSTANT = "MFGEVCONNECT_"
COUNT_CONST = "Count"
COSTA_COFFEE = "Costa Coffee"
REGULAR_LOYALTY = "Regular"
FREE_LOYALTY = "Free"
BURNED = "Burned"
REWARD_UNLOCK = "Reward Unlock Notification Identifier"
REWARD_EXPIRY = "Reward Expiry Notification Identifier"

DEFAULT_NOTIFICATION_IMAGE_URL = "static/images/notification-logo.png"

DEFAULT_NOTIFICATION_IMAGE = (
    config("DJANGO_APP_CDN_BASE_URL").split("media/")[0]
    + DEFAULT_NOTIFICATION_IMAGE_URL
)

# Screening constants
ON_HOLD = "On Hold"
SESSION_AMOUNT_FOR_SCREENING = "session_amount_for_screening"
DEFAULT_SESSION_AMOUNT_FOR_SCREENING = "99"
EMAIL_ID_FOR_SCREENING = "email_id_for_screening"
CARD_DETAIL = "card_details"
CARD = "card"
CARD_BRAND = "card_brand"
ACTION_TYPE = "actionType"
EDITED_AMOUNT = "editedAmount"
APPROVE = "Approve"
EDIT_HOLD_PAYMENT = "Edit"
MFG_ADMIN_USERNAME_FOR_SCREENING = "mfg_admin_username_for_screening"
DEFAULT_MFG_ADMIN_USERNAME_FOR_SCREENING = "MFG Admin"

# Screening error and success messages
INSUFFICIENT_DATA_TO_PROCESS_SESSION_ERROR = (
    "Data is insufficient to process session."
)
NEGATIVE_OR_NO_AMOUNT_ERROR = "Amount should be greater than 0."
EDITED_AND_PROCESSED_SUCCESSFULLY = "Successfully updated and processed"
SUCCESSFULLY_PROCESSED = "Successfully processed"
FAILED_TO_PROCESS_SESSION = "Failed to process session."
SECRET_KEY_NOT_PROVIDED = Response(
    {
        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
        "status": False,
        "message": "Secret key not provided.",
    }
)
SECRET_KEY_IN_VALID = Response(
    {
        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
        "status": False,
        "message": "Secret key is not valid.",
    }
)
ADMIN_SCREENING = "Admin-Screening"

DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET = settings.DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
# blocked app users constants
BLOCKED_USERS_EMAILS_LIST="Blocked email list"
BLOCKED_USERS_PHONE_LIST="Blocked phone list"

# Swarco constactless constants
SWARCO_SHEET_REQUIRED_FIELDS=[
    "ID",
    "Charger",
    "Accepted",
    "Start Source",
    "Start Card",
    "Stop Source",
    "Stop Card",
    "Extra Data",
    "Start Date",
    "End Date",
    "Total Time",
    "Total kWh",
    "Corrupt?",
    "Billing Plan",
    "Cost",
    "Unregistered Start Card",
    "Unregistered Stop Card"
]
ADVAM_SHEET_REQUIRED_FIELDS=[
    "Authorised",
    "Merchant",
    "Type",
    "Card",
    "Transaction Amount",
    "Currency",
    "CPID"
]

DRIIVZ_SHEET_REQUIRED_FIELDS=[
    "ID",
    "Charger",
    "Accepted",
    "Start Source",
    "Start Card",
    "Stop Source",
    "Stop Card",
    "Extra Data",
    "Start Date",
    "End Date",
    "Total Time",
    "Total kWh",
    "Corrupt?",
    "Billing Plan",
    "Cost",
    "Unregistered Start Card",
    "Unregistered Stop Card"
]

APP_VERSION_THREE=3
APP_VERSION_FOUR=4

DRIIVZ_DMS_TOKEN="driivz_dms_token"

# Sign In Options
GOOGLE_SIGN_IN="Google Sign In"
APPLE_SIGN_IN="Apple Sign In"
EMAIL_SIGN_IN="Email Sign In"
GUEST_SIGN_IN="Guest Sign In"

WEKK_DAYS_DATA = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday"
}

GENERIC_OFFERS = "Generic Offers"
LOYALTY_OFFERS = "Loyalty Offers"
IS_3DS_AVAILABLE=False

BEARER_CONSTANT_STRING = 'Bearer '
USER_DELETED = 'USER_DELETED'
IS_3DS_AVAILABLE=False

BEARER_CONSTANT_STRING = 'Bearer '

ROBOTS_TXT_RULES = [
    "User-agent: *",
    "Disallow: /",
]

CONTENT_TYPE_HEADER_KEY = "Content-Type"
JSON_DATA = "application/json"

OCPI_CREDENTIALS_CACHE_KEY = "OCPI_CREDENTIALS"

OCPI_LOCATIONS_KEY = "ocpi_locations"

CPO_EXISTS_MESSAGE = "OCPI configuration already exists."
GET_CREDENTIALS_ENDPOINT = "get-credentials-data/"
INITIATE_HANDSHAKE_ENDPOINT = "/initiate-handshake/"
UPDATE_EMSP_TOKEN_ENDPOINT = "/token-b-upgrade/"
OCPI_VERSIONS_ENDPOINT = '/versions'
VERSION = '2.2.1'
EMSP_TOKEN_KEY = "NODE_SECRET_TOKEN"

GET_TARIFF_ENDPOINT = "/tariffs/"
GET_SESSION_ENDPOINT = "/sessions/"

AMPECO_SESSIONS_ENDPOINT = "/resources/sessions/v1.0"
AMPECO_LOCATIONS_ENDPOINT = "/resources/locations/v2.0"
AMPECO_CHARGEPOINTS_ENDPOINT = "/resources/charge-points/v2.0"
SYNC_LOCATION_ENDPOINT = "/location/"
OCPI_EMSP_NAME = "MFG"

VAT_PERCENTAGE = 20
VAT_PERCENTAGE_KEY = "vat_percentage"
DEFAULT_VAT_PERCENTAGE = "20"

EMSP_ENDPOINT = config("DJANGO_APP_NEST_OCPI_BACKEND")

EMSP_NAME = "mfg"
OCPI_KEY = "OCPI"

SWARCO = "SWARCO"
DRIIVZ = "DRIIVZ"
KWH="kwh"

CACHE_UPDATE_TOKEN_KEY = "CACHE_UPDATE_TOKEN"
OCPI_TOKENS_ENDPOINT = "/ocpi-token"
REREGISTER_TOKENS_ENDPOINT = "/check-token"

GUEST_USERS = "Guest Users"
ALL_USERS = "All Users"
REGISTERED_USERS = "Registered Users"