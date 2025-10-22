"""configurations constants"""
ADD_MARKER_TEMPLATE = "configurations/map_markers.html"
BASE_CONFIRATIONS_TEMPLATE = "configurations/base_configurations.html"
OCPI_CONFIGURATIONS_TEMPLATE = "configurations/ocpi_configurations.html"
UPDATE_OCPI_CONFIGURATIONS_TEMPLATE = "configurations/ocpi_configuration_details.html"
DEFAULT_IMAGES_TEMPLATE = "configurations/default_brand_images.html"
OCPI_CREDENTIALS_CACHE_KEY = "OCPI_CREDENTIALS"
# response messages

INDICATOR_ADDED_SUCCESSFULLY = "Indicator added successfully"
INDICATOR_ADD_ERROR = "Indicator type and image are required fields"

BASE_CONF_ADDED_SUCCESSFULLY = "Base configuration added successfully"
BASE_CONF_UPDATED_SUCCESSFULLY = "Base configuration updated successfully"
BASE_CONF_ADD_ERROR = "Please provide all fields to add base configuration!"
UNABLE_TO_DISPLAY_DETAILS = "Unable to display failed handshake details"

DEFAULT_IMAGE_ADDED_SUCCESSFULLY = "Default image added successfully"
DEFAULT_IMAGE_UPDATED_SUCCESSFULLY = "Default image updated successfully"
DEFAULT_IMAGE_ADD_ERROR = "Please provide all fields to add default image!"

BRAND_INDICATOR_TYPE = "brand_indicator"
EV_INDICATOR_TYPE = "ev_indicator"

OCPI_CREDENTIALS_ADDED_SUCCESSFULLY = "OCPI credentials added successfully"
OCPI_CREDENTIALS_CREATE_ERROR = "Failed to complete handshake"
OCPI_CREDENTIALS_UPDATE_ERROR = "Failed to update OCPI credentials!"
INVALID_NAME_ERROR = "Please enter a valid name"
INVALID_TOKEN_ERROR = "Please enter a valid token"

# email notifications constants
PRE_DOWN_TIME = "pre_down_time"
POST_DOWN_TIME = "post_down_time"
PRE_RELEASE = "Pre-release"
POST_RELEASE = "Post-release"
CUSTOM = "Custom"
PRE_RELEASE_SUBJECT = "Pre-release email notification"
POST_RELEASE_SUBJECT = "Post-release email notification"
ALL_APP_USERS = "All App Users"
ONLY_SUBSCRIBED_USERS = "Only Subscribed Users"
DELIVERED = "Delivered"
SCHEDULED = "Scheduled"
FAILED = "Failed"
DRAFT = "Draft"
IN_PROGRESS = "In Progress"
FAILED = "Failed"
ONLY_SUBSCRIBED_USERS = "Only Subscribed Users"
ADD_NEW_EMAIL_NOTIFICATION = "Add New Email Notification"
ADD_NEW_PUSH_NOTIFICATION = "Add New Push Notification"
UPDATE_PUSH_NOTIFICATION = "Update Push Notification"
VIEW_PUSH_NOTIFICATION = "View Push Notification"
UPDATE_EMAIL_NOTIFICATION = "Update Email Notification"
EMAIL_NOTIFICATION = "Email Notification"
UNSUBSCRIBE_EMAIL = "Unsubscribe Emails"
FCM_NOTIFICATION = "FCM Notifications"
UNDER_MAINTENANCE_STATUS_KEY = "under_maintenance_status"
UNDER_MAINTENANCE_MESSAGE_KEY = "under_maintenance_message"
UNDER_MAINTENANCE_KEYS = [
    UNDER_MAINTENANCE_MESSAGE_KEY,
    UNDER_MAINTENANCE_STATUS_KEY,
]


UNDER_MAINTENANCE_DEFAULT_MESSAGE = (
    "Under maintenance, this functionality might not be "
    + "available for few hours please try again later."
)
