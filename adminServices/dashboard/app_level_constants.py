"""dashboard app level constants"""
DAY_POSITION_IN_DAYS_ARRAY = 0
MONTH_POSITION_IN_DAYS_ARRAY = 1
YEAR_POSITION_IN_DAYS_ARRAY = 2

WEEK_POSITION_IN_WEEKS_ARRAY = 0
YEAR_POSITION_IN_WEEKS_ARRAY = 1


MONTH_POSITION_IN_MONTHS_ARRAY = 0
YEAR_POSITION_IN_MONTHS_ARRAY = 1

ONE_STAR_REVIEWS = 0
TWO_STAR_REVIEWS = 1
THREE_STAR_REVIEWS = 2
FOUR_STAR_REVIEWS = 3
FIVE_STAR_REVIEWS = 4

MONTHS_LIST = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

SWARCO = "SWARCO"
DRIIVZ = "DRIIVZ"

# -1 is a placeholder for indexing purposes.
DAYS_IN_MONTH = [-1, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

DASHBOARD_DATA_DAYS_LIMIT = "dashboard_data_days_limit"
DEFAULT_DASHBOARD_DATA_DAYS_LIMIT=60

COMMON_SESSION_FIELDS = [
    'id',
    'emp_session_id',
    'session_status',
    'payment_id',
    'paid_status',
    'payment_response',
    'charging_data',
    'user_mail',
    'mail_status',
    'feedback',
    'rating',
    'is_reviewed',
    'end_time',
    'chargepoint_id_id',
    'connector_id_id',
    'user_id_id',
    'charging_session_id',
    'back_office',
    'user_account_number',
    'is_force_stopped',
    'payment_completed_at',
    'payment_method',
    'preauth_status',
    'preauth_collected_by',
    'payment_type',
    'session_tariff',
    'deducted_voucher_amount',
    'charging_authorization_status',
    'is_refund_initiated',
    'user_card_number',
    'station_id_id'
    ] 

