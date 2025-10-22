"""session transactions app level constants"""

# Date - 01/03/2022

# File details-
#   Author          - Manish Pawar
#   Description     - This file contains constants related to
#                       session transactions.
#   Name            - Session transaction constants
#   Modified by     - Anuj More
#   Modified date   - 03/01/2023
from sharedServices.constants import (
    ADMIN_SCREENING,
    EDIT_HOLD_PAYMENT,
    APPROVE,
)

SESSION_STATUS_LIST = [
    "start",
    "rejected",
    "running",
    "forbidden",
    "closed",
    "completed",
    "not available",
]

PAYMENT_STATUS_LIST = ["paid", "unpaid"]

APP_PAYMENT = "App"
ADMIN_PAYMENT = "Admin"
PAYMENT_BY_STATUS_LIST = [
    APP_PAYMENT,
    ADMIN_PAYMENT,
    f"{ADMIN_SCREENING}-{APPROVE}",
    f"{ADMIN_SCREENING}-{EDIT_HOLD_PAYMENT}",
]
SESSION_STATUS_FOR_TRANSACTIONS = "completed"
SESSION_STATUS_COMPLETED = "completed"
SESSION_STATUS_STOPPED = "stopped"
SESSION_STATUS_CLOSED = "closed"

REASON = "reason"
STATE = "state"
STATUS = "status"
UNKNOWN = "unknown"
NOT_AVAILABLE = "not available"

ERRORS = "errors"
DETAIL = "detail"
CODE = "code"
TOTAL_MONEY = "total_money"
APPROVED_MONEY = "approved_money"
PAYMENT = "payment"
AMOUNT = "amount"
CURRENCY = "currency"
UPDATED_AT = "updated_at"
RECEIPT_URL = "receipt_url"
APPROVED = "APPROVED"
CREATED_AT = "created_at"

CHARGEPOINT_ID = "chargePointId"
CONNECTOR = "connector"
AMOUNT = "amount"
CURRENCY = "currency"
KWH = "kwh"
START_DATE_TIME = "startOn"
END_DATE_TIME = "stopOn"
TOTAL_ENERGY = "totalEnergy"
TOTAL = "total"
COST = "cost"

SESSION_EXPORT = [
    "Session ID",
    "CDR ID",
    "Square Payment ID",
    "Session Start Time",
    "Session End Time",
    "Session Status",
    "Payment Status",
    "Payment Amount In Pennies",
    "Square Payment Response",
    # "Driivz session data",
    "User ID",
    "MFG App User Email",
    "Chargepoint ID",
    "Station ID",
    "Station Name",
    "Ocpi Connector ID",
    "Evse UID"
]


FROM_DATE_CONST = "from_date"
TO_DATE_CONST = "to_date"
