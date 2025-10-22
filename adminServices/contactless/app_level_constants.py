"""this file contains constants values for contact less module"""
from datetime import datetime
from decouple import config

AMOUNT_TOLERANCE = 0.10
TIME_TOLERANCE = 0
CUSTOMER_CARE_EMAIL = "customercare@motorfuelgroup.com"
HEADOFFICE_ADDRESS = "10 Bricket Road, Marlborough Court,\nSt Albans, Hertfordshire,AL1 3JX"
CUSTOMER_CARE_PHONE = "01727898890"

SESSION_NOT_FOUND_ERROR_MESSAGE = (
    "We are currently unable to find your session details, "
    + "please click the "
    + CUSTOMER_CARE_EMAIL
    + " email link and this will enable us to find "
    + "your details and provide your receipt."
)

RECAPTCHA_FAILED = (
    "Recaptcha failed, Please try again."
)

GET_RECEIPTS_TIMEOUT_VALUE=20
CONTACTLESS_RECEIPTS_TAX_RATE=20
DATE_FORMAT = "%Y-%m-%d"
DRIIVZ = "driivz"
PAYTER = "payter"
BILLING_PLAN_CODE = "billingPlanCode"
BILLING_PLAN_CODE_VALUE = ["Payter-Plan", "Worldline-Plan"]
WORLDLINE_PLAN = "Worldline-Plan"
PAYTER_PLAN = "Payter-Plan"
ADVAM_PLAN = "Advam-Plan"
DATE_FORMAT_FOR_DRIIVZ = "%Y-%m-%dT%H:%M:%Sz"
DATE_FORMAT_FOR_DRIIVZ_V2 = "%Y-%m-%dT%H:%M:%S.%fZ"
SUCCESSFULLY_FETCHED_DATA = "Successfully Fetched data"
COMPLETE = "Complete"
FAILED = "Failed"
MIN_MONTHS_RANGE = "3"
MIN_DATE_FOR_DATA_RETRNTION_KEY = "minimum_date_for_data_retention"
VALETING_VAT_RATE = 20

DRIIVZ_ADMIN_USERNAME = config("DJANGO_APP_DRIIVZ_ADMIN_USERNAME")
DRIIVZ_ADMIN_PASSWORD = config("DJANGO_APP_DRIIVZ_ADMIN_PASSWORD")
SWARCO = "swarco"
ADVAM = "advam"
ADVAM_API_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
PDI_MORRISONS = "PDI-Morrisons"
BRAND_MORRISONS = "MFG Morrisons"
MORRISONS = "Morrisons"
FUEL = "Fuel"
BUNKERING = "Bunkering"
EV = "EV"
VALETING = "Valeting"
CUSTOM_SEARCH = "Custom"
PAYTER_PAYMENT_TERMINAL = "Payter"
WORLDLINE_PAYMENT_TERMINAL = "Worldline"
ADVAM_PAYMENT_TERMINAL = "Advam"
SWARCO_HISTORY_DATA_DATE = datetime(2024, 1, 1)

#DRIIVZ V2
PLAN_CODE = "planCode"
DRIIVZ_V1 = "v1"
DRIIVZ_V2 = "v2"

AMPECO = "AMPECO"