"""app level constants for session flow"""
CHECK_SESSION_CONNECTION_TIME_IN_SECONDS = 300

# back office constants
SWARCO = "SWARCO"
DRIIVZ = "DRIIVZ"

# driivz constants
CURRENCY = "currency"
PLAN_CODE = "planCode"
PLAN_ID = "planId"
CUSTOMER = "customer"
OVERRIDEACTIVATION = "overrideActivation"
CONTRACT = "contract"

# base configurations constants for Driivz
DRIIVZ_CURRENCY = "Driivz_currency"
DRIIVZ_PLAN_ID = "Driivz_plan_id"


# driivz register API response constants
DRRIVZ_USER_ACCOUNT_NUMBER = "accountNumber"
DRRIVZ_USER_VIRTUAL_CARD_ID = "virtualCardId"
DRRIVZ_USER_VIRTUAL_CARD_NUMBER = "virtualCardNumber"


# Drrivz card constants=
CARD_ID = "cardId"
CARD_NUMBER = "cardNumber"


# transactions related constants

TRANSACTION_ID = "transactionId"
TRANSACTION_STATUS = "transactionStatus"
STARTED = "STARTED"
DRIIVZ_STOPPED = "STOPPED"
UPDATED = "UPDATED"
DRIIVZ_RUNNING_SESSION_STATUSES = [STARTED, UPDATED]
RUNNING = "running"
REJECTED = "rejected"
STOPPED = "stopped"
CLOSED = "closed"
COMPLETED = "completed"
BILLED = "BILLED"
RUNNING_SESSION_STATUSES = [RUNNING, STOPPED]
CRON_JOB_SESSION_STATUSES = [CLOSED, STOPPED]
DRIIVZ_CHECK_FORCE_STOP_CONDITIONS = [DRIIVZ_STOPPED, BILLED]

# wallet transaction constants
WALLET_TRANSACTIONS = "wallet_transaction"
NON_WALLET_TRANSACTIONS = "non_wallet_transaction"
CHARGING_SESSION = "charging_session"

# payment type contants
COMBINED = "Combined"
PARTIAL = "Partial"
NON_WALLET = "non wallet"

# messages

PLEASE_COMPLETE_MOBILE_NUMBER_VERIFICATION = (
    "Please complete the mobile number verification."
)
UNABLE_TO_CREATE_SESSION = (
    "Unable to start a session. Please contact support."
)
BACK_OFFICE_NOT_PROVIDED = "Back office not provided."
SESSION_TARRIF_NOT_PROVIDED = "Session tariff not provided."
USER_HAVING_RUNNING_SESSION = "User have running charging session!"
PREVIOUS_SESSSION_PAYMENT_PENDING_MESSAGE = (
    "Please wait until the payment of previous session is processed."
)
STATION_NOT_FOUND_MESSAGE = "Failed to fetch station with provided station id."
CHARGEPOINT_NOT_FOUND_MESSAGE = (
    "Failed to fetch chargepoint with provided chargepoint id."
)
CONNECTOR_NOT_FOUND_MESSAGE = (
    "Failed to fetch connector with provided connector id."
)

EVSE_NOT_FOUND_MESSAGE = (
    "Failed to fetch EVSE."
)

CONNECTOR_NOT_AVAILABLE = (
    "Connector not available."
)

OCPI_TOKENS_ENDPOINT = "/ocpi-token"
EMSP_COUNTRY_CODE = "GB"
EMSP_PARTY_ID = "EVP"
APP_USER = "APP_USER"
OCPI_TOKEN_ISSUER = "MFG-CONNECT-TEST"

START_SESSION_ENDPOINT = "commands-start-session/"
STOP_SESSION_ENDPOINT = "commands-stop-session/"