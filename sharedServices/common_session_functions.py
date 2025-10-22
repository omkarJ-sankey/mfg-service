"""common functions for session"""

# Date - 09/06/2022

# File details-
#   Author          - Shubham Dhumal
#   Description     - This file contains common
#                     functions for charging session functionality.
#   Name            - Sessions Common functions
#   Modified by     - Shubham Dhumal
#   Modified date   - 09/06/2022


# These are all the imports that we are exporting from
# different module's from project or library.
import json
import uuid
import math
from datetime import datetime
from decimal import Decimal
import traceback
import requests

import pytz
import ast
from rest_framework import status
# from square.client import Client
from decouple import config
from django.utils import timezone
from cryptography.fernet import Fernet
from .model_files.charging_session_models import (
    ChargingSession,
    PaidPaymentLogs,
)
from .model_files.config_models import BaseConfigurations
from .model_files.app_user_models import Profile
from .model_files.transaction_models import Transactions
from .common import (
    array_to_string_converter,
    string_to_array_converter,
    time_formatter_for_hours,
    check_integer,
    redis_connection,
    custom_round_function,
)
from .loyalty_common_functions import handle_user_costa_loyalty
from .model_files.ocpi_charge_detail_records_models import OCPIChargeDetailRecords
from .payments_helper_function import make_request
from .driivz_api_gateway_functions import (
    get_driivz_api_gateway_dms_ticket
)

from .email_common_functions import (
    email_sender,
    session_details,
)
from .sentry_tracers import traced_request_with_retries
from .constants import (
    DATE_TIME_FORMAT,
    COMEPLETED,
    RETRIEVE_PAYMENT_FAILED,
    RETRIEVE_CUSTOMER_CARDS_FAILED,
    NO_CARDS_ADDED_FOR_CUSTOMER,
    CREATE_PAYMENT_PROCESS_FAILED,
    APPLE_GOOGLE_PAY_USED,
    NO,
    YES,
    CHARGING_SESSION,
    CARD_PAYMENT_TIMELINE,
    AUTHORIZED_AT,
    POST_REQUEST,
    GET_REQUEST,
    REQUEST_API_TIMEOUT,
    ADMIN_SCREENING,
    EDIT_HOLD_PAYMENT,
    COMMON_ERRORS,
    CONTENT_TYPE_HEADER_KEY,
    JSON_DATA,
    GET_TARIFF_ENDPOINT,
    GET_SESSION_ENDPOINT,
    EMSP_ENDPOINT,
    DRIIVZ,
    KWH,
    DRIIVZ_START_ON,
    DRIIVZ_STOP_ON,
    SWARCO,
    SWARCO_END_TIME,
    SWARCO_START_TIME,
    TOTAL_ENERGY,
    DEFAULT_VAT_PERCENTAGE,
    DRIIVZ_PLAN_CODE,
    DEFAULT_DRIIVZ_PLAN_CODE
)
from .error_codes import PAYMENT_ERROR_CODES
from .sentry_tracers import traced_request

from .model_files.ocpi_sessions_models import OCPISessions
from .model_files.ocpi_tariffs_models import Tariffs
from .common import (
    get_node_secret,
    get_cdr_details,
    filter_function_for_base_configuration
)
# client = Client(
#     access_token=config("DJANGO_PAYMENT_ACCESS_TOKEN"),
#     environment=config("DJANGO_PAYMENT_ENV"),
# )
# cards_api = client.cards

# payments_api = client.payments

def get_session_details(session):
    """this function returns transaction details
    for particular transaction"""
    
    # session = OCPISessions.objects.filter(id = session_id).first()
    token = get_node_secret()
    session_request={
        "OCPI":session.back_office,
        "date_from":datetime.strftime(session.start_datetime,"%Y-%m-%dT%H:%M:%S"),
        "session_id":str(session.session_id)
    }
    
    session_data_response = traced_request_with_retries(
        POST_REQUEST,
        (
            EMSP_ENDPOINT + GET_SESSION_ENDPOINT
        ),
        headers={
            CONTENT_TYPE_HEADER_KEY: JSON_DATA,
            "Authorization": f"Token {token}"
        },
        timeout=REQUEST_API_TIMEOUT,
        data=json.dumps(session_request)
    )
    
    return session_data_response



def get_ordinal_suffix(day):
    """get suffix for the day of the date"""
    if 11 <= day <= 13:
        return "th"
    else:
        return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")


def get_payment_completed_at_dates(card_response):
    """this function returns required format for the payment completed at dates"""

    # Parse and localize the datetime
    localized_date = timezone.localtime(
        datetime.strptime(
            card_response["payment"]["card_details"][
                CARD_PAYMENT_TIMELINE
            ][AUTHORIZED_AT].split(".")[0], DATE_TIME_FORMAT
        ).replace(tzinfo=pytz.UTC)
    )

    # Format the date
    day = localized_date.day
    month = localized_date.strftime("%B")
    year = localized_date.year

    return [
        f"{day}{get_ordinal_suffix(day)} {month} @{year}",
        localized_date.strftime("%d/%m/%Y")
    ]


def return_multiple_card_details(session, session_payment_data, v4_api_request=False):
    """This function return multiple card details
    if session payment is done using multiple cards"""
    primary_card_number = None
    secondary_card_number = None
    primary_card_payment_time = None
    secondary_card_payment_time = None
    primary_card_amount = None
    primary_card_payment_time_format_one = None
    secondary_card_amount = None
    secondary_card_payment_time_format_one = None
    primary_card_brand = None
    secondary_card_brand = None
    session_payments = (
        session_payment_data[f"{session.id}"]
        if f"{session.id}" in session_payment_data
        else None
    )
    if session.preauth_status == "collected" and session_payments and len(session_payments) > 1:
        primary_card_response, secondary_card_response = session_payments
        primary_card_number = primary_card_response["payment"][
            "card_details"
        ]["card"]["last_4"]
        primary_card_amount = float(
            primary_card_response["payment"]["total_money"]["amount"]
        )
        primary_card_brand = primary_card_response["payment"]["card_details"]["card"][
            "card_brand"
        ]
        secondary_card_brand = secondary_card_response["payment"]["card_details"]["card"][
            "card_brand"
        ]
        if v4_api_request:
            primary_card_payment_time = datetime.strptime(
                primary_card_response["payment"]["card_details"]["card_payment_timeline"][
                    "captured_at"
                ],
                "%Y-%m-%dT%H:%M:%S.%fZ",
            ).strftime("%d/%m/%Y %H:%M")
        else:
            (
                primary_card_payment_time,
                primary_card_payment_time_format_one
            ) = get_payment_completed_at_dates(
                primary_card_response
            )

        secondary_card_number = secondary_card_response["payment"][
            "card_details"
        ]["card"]["last_4"]
        secondary_card_amount = float(
            secondary_card_response["payment"]["total_money"]["amount"]
        )
        if (
            session.total_cost_incl
            and primary_card_amount + secondary_card_amount
            != float(session.total_cost_incl)
        ):
            payment_logs = PaidPaymentLogs.objects.filter(
                payment_id=secondary_card_response["payment"]["id"]
            )
            if (
                payment_logs
                and len(payment_logs) > 1
                and payment_logs.filter(charging_session_id=session.id)
            ):
                secondary_card_amount = float(
                    payment_logs.filter(charging_session_id=session.id)
                    .first()
                    .paid_due_amount
                )
                if primary_card_amount + secondary_card_amount != float(
                    session.total_cost_incl
                ):
                    secondary_card_amount = (
                        float(session.total_cost_incl) - primary_card_amount
                    )
        if v4_api_request:
            secondary_card_payment_time = datetime.strptime(
                secondary_card_response["payment"]["card_details"]["card_payment_timeline"][
                    "captured_at"
                ],
                "%Y-%m-%dT%H:%M:%S.%fZ",
            ).strftime("%d/%m/%Y %H:%M")
        else:
            (
                secondary_card_payment_time,
                secondary_card_payment_time_format_one
            ) = get_payment_completed_at_dates(
                secondary_card_response
            )
    else:
        if session_payments is not None and len(session_payments) != 0 :
            primary_card_response =  session_payments[0] #if len(session_payments) > 0 else payment_response#session.payment_response[0]#
            primary_card_number = primary_card_response["payment"][
                "card_details"
            ]["card"]["last_4"]
            primary_card_amount = float(
                primary_card_response["payment"]["total_money"]["amount"]
            )
            primary_card_brand = primary_card_response["payment"]["card_details"]["card"][
                "card_brand"
            ]
            (
                primary_card_payment_time,
                primary_card_payment_time_format_one
            ) = get_payment_completed_at_dates(
                primary_card_response
            )
        else:
            primary_card_number = None
            primary_card_amount = None
            primary_card_brand = None
            primary_card_payment_time = None
            primary_card_payment_time_format_one = None
    return [
        primary_card_number,
        secondary_card_number,
        primary_card_payment_time,
        primary_card_payment_time_format_one,
        secondary_card_payment_time,
        secondary_card_payment_time_format_one,
        (
            format(primary_card_amount / 100, ".2f")
            if primary_card_amount
            else None
        ),
        (
            format(secondary_card_amount / 100, ".2f")
            if secondary_card_amount
            else None
        ),
        primary_card_brand,
        secondary_card_brand,
    ]


def charging_session_mail_data_formatter(*args):
    """this functions formats data for charging session mail"""
    (
        transaction_id,
        decrypter,
        email,
        first_name,
        last_name,
        site_title,
        station_name,
        charger_point_name,
        location,
        owner,
        back_office,
        start_session_date,
        start_session_time,
        end_session_date,
        end_session_time,
        tariff_currency,
        tariff_amount,
        charging_duration,
        energy_supplied,
        session_amount_without_tax,
        session_amount_with_tax,
        session_tax_amount,
        tax_rate,
        payment_card_last_four,
        payment_date,
        payment_time,
        due_amount,
        session_tariff,
        voucher_amount,
        total_paid,
        deducted_from_voucher,
        is_multicard_payment,
        primary_card_number,
        secondary_card_number,
        primary_card_payment_time,
        primary_card_payment_time_format_one,
        secondary_card_payment_time,
        secondary_card_payment_time_format_one,
        primary_card_amount,
        secondary_card_amount,
        primary_card_brand,
        secondary_card_brand,
        vat_percentage,
    ) = args
    data = {
        "vat_percentage":vat_percentage,
        "transaction_number": transaction_id,
        "email": f"{decrypter.decrypt(email).decode()}",
        "user_name": f"{decrypter.decrypt(first_name).decode()}",
        "full_name": f"{decrypter.decrypt(first_name).decode()}\
            {decrypter.decrypt(last_name).decode()}",
        "charger_name": f"{site_title}, \
                {station_name}".strip(),
        "charger_point_name": charger_point_name,
        "location": location,
        "network": f"{owner} {back_office}",
        "start_date_time": f"{start_session_date} {start_session_time}",
        "end_date_time": f"{end_session_date} {end_session_time}",
        "price": (
            f"{session_tariff}/kWh"
            if session_tariff is not None
            else f"{tariff_currency} {tariff_amount}/kWh"
        ),
        "duration": charging_duration,
        "energy_supplied": f"{energy_supplied} kWh",
        "total_cost_without_tax": session_amount_without_tax,
        "tax_amount": session_tax_amount,
        "tax_rate": tax_rate,
        "total_cost": session_amount_with_tax,
        "payment_card": (
            f"**** **** **** { payment_card_last_four }"
            if payment_card_last_four
            else "MFG Connect - Voucher"
        ),
        "payment_date": f"{payment_date} {payment_time}",
        "due_amount": format(float(due_amount) / 100, ".2f"),
        "voucher_amount": voucher_amount,
        "voucher_amount_available": float(voucher_amount) > 0,
        "total_paid": total_paid,
        "deducted_from_voucher": deducted_from_voucher,
        "is_multicard_payment": is_multicard_payment,
        "primary_card_number": primary_card_number,
        "secondary_card_number": secondary_card_number,
        "primary_card_payment_time": primary_card_payment_time,
        "primary_card_payment_time_format_one": primary_card_payment_time_format_one,
        "secondary_card_payment_time": secondary_card_payment_time,
        "secondary_card_payment_time_format_one": secondary_card_payment_time_format_one,
        "primary_card_amount": primary_card_amount,
        "secondary_card_amount": secondary_card_amount,
        "primary_card_brand": primary_card_brand,
        "secondary_card_brand": secondary_card_brand,
        "overstay": None,
        "tariff_amount": tariff_amount
    }
    return data

def send_charging_payment_mail(
    session_id,
    payment_response=None,
    template_id=config("DJANGO_APP_CHARGING_SESSION_PAYMENT_MAIL_TEMPLATE_ID"),
    due_amount="0",
):
    """send charging payment mail"""
    try:
        print(f"Session id {session_id} - Inside send payment mail function")
        charging_session = OCPISessions.objects.get(id=session_id)
        cdr_data = get_cdr_details(session_id)
        if charging_session.charging_data is None:
            return False
        print(f"Session id {session_id} -inside charging data condition")
        session_tariff = charging_session.session_tariff
        charging_data = string_to_array_converter(
            charging_session.charging_data
        )
        payment_created_date = timezone.now()
        card_last_4 = "MFG Voucher"
        if "totalEnergy" not in charging_data[0]:
            return False
        # cost_data = charging_data[0]["cost"]
        session_amount_with_tax = 0
        session_amount_without_tax = 0
        session_tax_amount = 0
        cost_incl = 0
        cost_excl = 0
        tax_rate = 0
        
        for cdr in cdr_data:
            cost_incl+=json.loads(cdr.total_cost)["incl_vat"]
            cost_excl+=json.loads(cdr.total_cost)["excl_vat"]
        
        if cost_incl > 0:
            tax_rate = Decimal(str(round(
                ((cost_incl - cost_excl)/(cost_excl)) * 100
            ))) if cost_incl > 0 else 0
        elif charging_session.total_cost_incl is not None and charging_session.total_cost_incl > 0:
            tax_rate = Decimal(str(round(
                ((charging_session.total_cost_incl - charging_session.total_cost_excl)/(charging_session.total_cost_excl)) * 100
            ))) if charging_session.total_cost_incl > 0 else 0
        
        connector = charging_session.connector_id
        
        total_paid = 0
        voucher_amount = (
            Decimal(str(charging_session.deducted_voucher_amount)) / 100
            if charging_session.deducted_voucher_amount is not None
            else 0
        )
        if (
            charging_session.is_reviewed
            == f"{ADMIN_SCREENING}-{EDIT_HOLD_PAYMENT}"
        ):
            session_amount_with_tax = custom_round_function(
                Decimal(cost_incl) , 2, False
            )
            session_amount_without_tax = custom_round_function(
                Decimal(cost_excl) , 2, False
            )
            session_tax_amount = Decimal(
                f"{session_amount_with_tax}"
            ) - Decimal(f"{session_amount_without_tax}")
            total_paid = (
                Decimal(str(cost_incl)) 
                if cost_incl is not None
                else 0
            )
        else:
            session_amount_with_tax = Decimal(cost_incl) if cost_incl is not None else 0
            session_amount_without_tax = Decimal(
                cost_excl
            ) if cost_incl is not None else 0
            session_tax_amount = session_amount_with_tax - session_amount_without_tax
            total_paid = Decimal(str(session_amount_with_tax)) - voucher_amount
        is_multicard_payment = False
        user_transactions = Transactions.objects.filter(
            customer_id=charging_session.user_id.customer_id,
            payment_for=CHARGING_SESSION,
            payment_for_reference_id=charging_session.id,
        )
        session_payment_data = {f"{charging_session.id}": []}
        for transation in user_transactions:
            session_db_id = transation.payment_for_reference_id
            current_payment_response = string_to_array_converter(
                transation.payment_response
            )[0]
            if (
                current_payment_response["payment"]["card_details"]["card"][
                    "card_brand"
                ]
                != "SQUARE_GIFT_CARD"
                and current_payment_response["payment"]["status"]
                == "COMPLETED"
            ):
                session_payment_data[f"{session_db_id}"].append(
                    current_payment_response
                )
        (
            primary_card_number,
            secondary_card_number,
            primary_card_payment_time,
            primary_card_payment_time_format_one,
            secondary_card_payment_time,
            secondary_card_payment_time_format_one,
            primary_card_amount,
            secondary_card_amount,
            primary_card_brand,
            secondary_card_brand
        ) = return_multiple_card_details(
            charging_session, session_payment_data
        )
        if (
            primary_card_number
            and secondary_card_number
            and primary_card_payment_time
            and secondary_card_payment_time
            and primary_card_amount
            and secondary_card_amount
        ):
            is_multicard_payment = True
        else:
            if (
                payment_response
                and "errors" not in list(payment_response.keys())
                and payment_response["payment"]["status"] == "COMPLETED"
            ):
                payment_created_date = timezone.localtime(
                    datetime.strptime(
                        payment_response["payment"]["updated_at"],
                        "%Y-%m-%dT%H:%M:%S.%fZ",
                    ).replace(tzinfo=pytz.UTC)
                )
                card_last_4 = (
                    None
                    if payment_response["payment"]["card_details"]["card"][
                        "card_brand"
                    ]
                    == "SQUARE_GIFT_CARD"
                    else payment_response["payment"]["card_details"]["card"][
                        "last_4"
                    ]
                )
        print(f"Session id {session_id} -inside payment response condition")
        # session payment mail template id
        user_key = charging_session.user_id.key
        decrypter = Fernet(user_key)

        to_emails = [
            (
                decrypter.decrypt(
                    charging_session.user_id.encrypted_email
                ).decode(),
                decrypter.decrypt(
                    charging_session.user_id.first_name
                ).decode(),
            )
        ]
        # charging session start and end time
        (
            charging_session_consumption,
            charging_session_end_time_history,
            charging_session_start_time_history,
        ) = session_details(
            charging_session
        )
        charging_duration_history = time_formatter_for_hours(
            int(
                (
                    charging_session_end_time_history
                    - charging_session_start_time_history
                ).total_seconds()
            )
        )

        dynamic_data = charging_session_mail_data_formatter(
            charging_session.emp_session_id,
            decrypter,
            charging_session.user_id.encrypted_email,
            charging_session.user_id.first_name,
            charging_session.user_id.last_name,
            (
                charging_session.station_id.driivz_display_name
                if charging_session.station_id.driivz_display_name
                else charging_session.station_id.site_title
            ),
            charging_session.location_id.name,
            charging_session.chargepoint_id.charger_point_name,
            charging_session.location_id.get_full_address().strip(),
            charging_session.station_id.owner,
            charging_session.chargepoint_id.back_office,
            charging_session_start_time_history.date().strftime("%d/%m/%Y"),
            charging_session_start_time_history.time().strftime("%H:%M"),
            charging_session_end_time_history.date().strftime("%d/%m/%Y"),
            charging_session_end_time_history.time().strftime("%H:%M"),
            charging_session.currency,
            # charging_session.connector_id.tariff_amount,
            session_tariff,
            charging_duration_history,
            format(charging_session_consumption, ".2f"),
            format(session_amount_without_tax, ".2f"),
            format(session_amount_with_tax, ".2f"),
            format(session_tax_amount, ".2f"),
            format(tax_rate, ".2f"),
            card_last_4,
            payment_created_date.date().strftime("%d/%m/%Y"),
            payment_created_date.time().strftime("%H:%M:%S"),
            due_amount,
            session_tariff,
            format(voucher_amount, ".2f"),
            format(total_paid, ".2f"),
            True if voucher_amount > 0 else False,
            is_multicard_payment,
            primary_card_number,
            secondary_card_number,
            primary_card_payment_time,
            primary_card_payment_time_format_one,
            secondary_card_payment_time,
            secondary_card_payment_time_format_one,
            primary_card_amount,
            secondary_card_amount,
            primary_card_brand,
            secondary_card_brand,
            format(Decimal(charging_session.vat_percentage), ".2f")
        )
        return email_sender(template_id, to_emails, dynamic_data)

    except COMMON_ERRORS:
        traceback.print_exc()
        print(
            "Exception in send charging"
            + f"payment mail for session -> {session_id}"
        )

#This function is used to send mail to users having due amount prior ocpi integration
def send_old_charging_payment_mail(
    session_id,
    payment_response=None,
    template_id=config("DJANGO_APP_CHARGING_SESSION_PAYMENT_MAIL_TEMPLATE_ID"),
    due_amount="0",
):
    """send charging payment mail"""
    try:
        print(f"Session id {session_id} - Inside send payment mail function")
        charging_session = ChargingSession.objects.get(id=session_id)
        if charging_session.charging_data is None:
            return False
        
        print(f"Session id {session_id} -inside charging data condition")
        session_tariff = charging_session.session_tariff
        charging_data = string_to_array_converter(
            charging_session.charging_data
        )
        payment_created_date = timezone.now()
        card_last_4 = "MFG Voucher"
        if "totalEnergy" not in charging_data[0]:
            return False
        cost_data = charging_data[0]["cost"]
        session_amount_with_tax = 0
        session_amount_without_tax = 0
        session_tax_amount = 0
        tax_rate = Decimal(str(round(
            (cost_data["totalTax"] /(cost_data["total"] - cost_data["totalTax"])) * 100
        ))) if cost_data["total"] > 0 else 0
        total_paid = 0
        voucher_amount = (
            Decimal(str(charging_session.deducted_voucher_amount)) / 100
            if charging_session.deducted_voucher_amount is not None
            else 0
        )
        if (
            charging_session.is_reviewed
            == f"{ADMIN_SCREENING}-{EDIT_HOLD_PAYMENT}"
        ):
            session_amount_with_tax = custom_round_function(
                Decimal(charging_session.total_cost) / 100, 2, False
            )
            session_amount_without_tax = custom_round_function(
                Decimal(
                    str(cost_data["total"])
                ) - Decimal(str(cost_data["totalTax"])),
                2,
                False,
            )
            session_tax_amount = Decimal(
                f"{session_amount_with_tax}"
            ) - Decimal(f"{session_amount_without_tax}")
            total_paid = (
                Decimal(str(charging_session.total_cost)) / 100
                if charging_session.total_cost is not None
                else 0
            )
        else:
            session_amount_with_tax = Decimal(str(cost_data["total"]))
            session_amount_without_tax = Decimal(
                str(cost_data["total"])
            ) - Decimal(str(cost_data["totalTax"]))
            session_tax_amount = Decimal(str(cost_data["totalTax"]))
            total_paid = Decimal(str(cost_data["total"])) - voucher_amount
        is_multicard_payment = False
        user_transactions = Transactions.objects.filter(
            customer_id=charging_session.user_id.customer_id,
            payment_for=CHARGING_SESSION,
            payment_for_reference_id=charging_session.id,
        )
        session_payment_data = {f"{charging_session.id}": []}
        for transation in user_transactions:
            session_db_id = transation.payment_for_reference_id
            current_payment_response = string_to_array_converter(
                transation.payment_response
            )[0]
            if (
                current_payment_response["payment"]["card_details"]["card"][
                    "card_brand"
                ]
                != "SQUARE_GIFT_CARD"
                and current_payment_response["payment"]["status"]
                == "COMPLETED"
            ):
                session_payment_data[f"{session_db_id}"].append(
                    current_payment_response
                )
        (
            primary_card_number,
            secondary_card_number,
            primary_card_payment_time,
            primary_card_payment_time_format_one,
            secondary_card_payment_time,
            secondary_card_payment_time_format_one,
            primary_card_amount,
            secondary_card_amount,
            primary_card_brand,
            secondary_card_brand
        ) = return_multiple_card_details(
            charging_session, session_payment_data
        )
        if (
            primary_card_number
            and secondary_card_number
            and primary_card_payment_time
            and secondary_card_payment_time
            and primary_card_amount
            and secondary_card_amount
        ):
            is_multicard_payment = True
        else:
            if (
                payment_response
                and "errors" not in list(payment_response.keys())
                and payment_response["payment"]["status"] == "COMPLETED"
            ):
                payment_created_date = timezone.localtime(
                    datetime.strptime(
                        payment_response["payment"]["updated_at"],
                        "%Y-%m-%dT%H:%M:%S.%fZ",
                    ).replace(tzinfo=pytz.UTC)
                )
                card_last_4 = (
                    None
                    if payment_response["payment"]["card_details"]["card"][
                        "card_brand"
                    ]
                    == "SQUARE_GIFT_CARD"
                    else payment_response["payment"]["card_details"]["card"][
                        "last_4"
                    ]
                )
        print(f"Session id {session_id} -inside payment response condition")
        # session payment mail template id
        user_key = charging_session.user_id.key
        decrypter = Fernet(user_key)

        to_emails = [
            (
                decrypter.decrypt(
                    charging_session.user_id.encrypted_email
                ).decode(),
                decrypter.decrypt(
                    charging_session.user_id.first_name
                ).decode(),
            )
        ]
        # charging session start and end time
        (
            charging_session_consumption,
            charging_session_end_time_history,
            charging_session_start_time_history,
        ) = session_details_according_to_back_office(
            charging_session, charging_data[0]
        )
        charging_duration_history = time_formatter_for_hours(
            int(
                (
                    charging_session_end_time_history
                    - charging_session_start_time_history
                ).total_seconds()
            )
        )

        dynamic_data = charging_session_mail_data_formatter(
            charging_session.emp_session_id,
            decrypter,
            charging_session.user_id.encrypted_email,
            charging_session.user_id.first_name,
            charging_session.user_id.last_name,
            (
                charging_session.station_id.driivz_display_name
                if charging_session.station_id.driivz_display_name
                else charging_session.station_id.site_title
            ),
            charging_session.station_id.station_name,
            charging_session.chargepoint_id.charger_point_name,
            charging_session.station_id.get_full_address().strip(),
            charging_session.station_id.owner,
            charging_session.chargepoint_id.back_office,
            charging_session_start_time_history.date().strftime("%d/%m/%Y"),
            charging_session_start_time_history.time().strftime("%H:%M"),
            charging_session_end_time_history.date().strftime("%d/%m/%Y"),
            charging_session_end_time_history.time().strftime("%H:%M"),
            charging_session.connector_id.tariff_currency,
            charging_session.connector_id.tariff_amount,
            charging_duration_history,
            charging_session_consumption,
            format(session_amount_without_tax, ".2f"),
            format(session_amount_with_tax, ".2f"),
            format(session_tax_amount, ".2f"),
            format(tax_rate, ".2f"),
            card_last_4,
            payment_created_date.date().strftime("%d/%m/%Y"),
            payment_created_date.time().strftime("%H:%M:%S"),
            due_amount,
            session_tariff,
            format(voucher_amount, ".2f"),
            format(total_paid, ".2f"),
            True if voucher_amount > 0 else False,
            is_multicard_payment,
            primary_card_number,
            secondary_card_number,
            primary_card_payment_time,
            primary_card_payment_time_format_one,
            secondary_card_payment_time,
            secondary_card_payment_time_format_one,
            primary_card_amount,
            secondary_card_amount,
            primary_card_brand,
            secondary_card_brand,
            DEFAULT_VAT_PERCENTAGE
        )
        return email_sender(template_id, to_emails, dynamic_data)

    except Exception as e:# COMMON_ERRORS:
        traceback.print_exc()
        print(
            "Exception in send charging"
            + f"payment mail for session -> {session_id}"
        )










def session_details_according_to_back_office(session, charging_response):
    """this function will prepare session details according
    to back office to send mails"""
    charging_session_consumption = 0
    if session.back_office == SWARCO:
        charging_session_consumption = charging_response["kwh"]
    if session.back_office == DRIIVZ:
        charging_session_consumption = charging_response["totalEnergy"]
    if session.back_office == SWARCO and KWH in charging_response:
        charging_session_end_time_history = timezone.localtime(
            datetime.strptime(
                charging_response[SWARCO_END_TIME], DATE_TIME_FORMAT
            ).replace(tzinfo=pytz.UTC)
        )
        charging_session_start_time_history = timezone.localtime(
            datetime.strptime(
                charging_response[SWARCO_START_TIME], DATE_TIME_FORMAT
            ).replace(tzinfo=pytz.UTC)
        )
    if session.back_office == DRIIVZ and TOTAL_ENERGY in charging_response:
        charging_session_end_time_history = timezone.localtime(
            datetime.fromtimestamp(int(charging_response[DRIIVZ_START_ON]), tz=pytz.UTC)
            if str(charging_response[DRIIVZ_START_ON]).isdigit()
            else datetime.strptime(str(charging_response[DRIIVZ_START_ON]).split(".")[0], DATE_TIME_FORMAT).replace(tzinfo=pytz.UTC)
        )

        
        # timezone.localtime(
        #     datetime.strptime(
        #         str(charging_response[DRIIVZ_STOP_ON]).split(".")[0],
        #         DATE_TIME_FORMAT,
        #     ).replace(tzinfo=pytz.UTC)
        # )
        charging_session_start_time_history = timezone.localtime(
                datetime.fromtimestamp(int(charging_response[DRIIVZ_START_ON]), tz=pytz.UTC)
                if str(charging_response[DRIIVZ_START_ON]).isdigit()
                else datetime.strptime(str(charging_response[DRIIVZ_START_ON]).split(".")[0], DATE_TIME_FORMAT).replace(tzinfo=pytz.UTC)
            )

        
        # timezone.localtime(
        #     datetime.fromtimestamp(
        #         int(charging_response[DRIIVZ_START_ON]),
        #         tz=pytz.UTC
        #     )
        # )

        
        # timezone.localtime(
        #     datetime.strptime(
        #         str(charging_response[DRIIVZ_START_ON]).split(".")[0],
        #         DATE_TIME_FORMAT,
        #     ).replace(tzinfo=pytz.UTC)
        # )
    return [
        charging_session_consumption,
        charging_session_end_time_history,
        charging_session_start_time_history,
    ]


def update_session_data_on_failure(session, response,is_ocpi=True):
    """this function updates payment response in
    db if payment response fails"""
    if is_ocpi:
        OCPISessions.objects.filter(id = session.id).update(
            payment_response=array_to_string_converter([response]),
            session_status=COMEPLETED,
        )
    else:
        ChargingSession.objects.filter(id = session.id).update(
            payment_response=array_to_string_converter([response]),
            session_status=COMEPLETED,
        )


def pre_auth_expiry_time_formatter(val):
    """this is time formatter function"""
    expiry_string = "P"
    # if math.floor(val/24):
    #     expiry_string += f"{str(math.floor(val/24))}DT"
    # if val%24:
    #     expiry_string += f"{str(val%24)}H"
    expiry_string += f"T{str(val)}H"
    return expiry_string


def get_pre_auth_expiry_time():
    """this function returns pre auth expity time"""
    cached_pre_auth_expiry = redis_connection.get("pre_auth_expiry")
    if cached_pre_auth_expiry:
        return cached_pre_auth_expiry.decode("utf-8")
    pre_auth_expiry = BaseConfigurations.objects.filter(
        base_configuration_key="pre_auth_expiry"
    ).first()
    pre_auth_expiry_text = "PT168H"
    if (
        pre_auth_expiry
        and check_integer(pre_auth_expiry.base_configuration_value)
        and math.ceil(float(pre_auth_expiry.base_configuration_value))
        in range(1, 8760)
    ):
        pre_auth_expiry_text = pre_auth_expiry_time_formatter(
            math.ceil(float(pre_auth_expiry.base_configuration_value))
        )
    redis_connection.set("pre_auth_expiry", pre_auth_expiry_text)
    return pre_auth_expiry_text


def create_payment_with_auto_deduct(
    pay_body,
    customer_id,
    session,
    admin_screen_payment=True,
    is_ocpi = True
):
    """this function is to deduct money on payment creation"""
    idempotency_key = str(uuid.uuid1())
    pay_body["customer_id"] = customer_id
    pay_body["idempotency_key"] = idempotency_key
    pay_body["reference_id"] = str(session.id)
    pay_body["autocomplete"] = True
    create_payment_result = make_request(
        POST_REQUEST,
        f"/payments",
        session.user_id.id,
        module="Square create payment with auto deduct API",
        data=pay_body,
    )
    response_data = json.loads(create_payment_result.content)
    if admin_screen_payment is False:
        return response_data
    if create_payment_result.status_code != 200:
        update_session_data_on_failure(session, response_data,is_ocpi)
        return return_payment_error_message(
            response_data, CREATE_PAYMENT_PROCESS_FAILED
        )
    if "payment" in response_data:
        print("auto completed payment*")
        return response_data
    return CREATE_PAYMENT_PROCESS_FAILED


def return_payment_error_message(pay_response, back_up_message):
    """this function return error message on payment failure"""
    if (
        "errors" in pay_response
        and len(pay_response["errors"])
        and "detail" in pay_response["errors"][0]
    ):
        return PAYMENT_ERROR_CODES.get(pay_response["errors"][0]["code"])
    return back_up_message


def return_card_data_from_payment_response(payment_response):
    """this function return card data for payment"""
    return [
        payment_response["payment"]["card_details"]["card"]["last_4"],
        payment_response["payment"]["card_details"]["card"]["exp_month"],
        payment_response["payment"]["card_details"]["card"]["exp_year"],
        payment_response["payment"]["total_money"]["amount"],
    ]


def validate_payment_id(payment_id, validate_payment_status, user_id):
    """this function validates payment id
    whether its expired or not"""
    retrieve_payments_result = make_request(
        GET_REQUEST,
        f"/payments/{payment_id}",
        user_id,
        module="Square get payment details API",
    )
    response_data = json.loads(retrieve_payments_result.content)
    if retrieve_payments_result.status_code != 200:
        return return_payment_error_message(
            response_data,
            RETRIEVE_PAYMENT_FAILED + str(payment_id),
        )
    if "payment" not in response_data:
        return return_payment_error_message(
            response_data,
            RETRIEVE_PAYMENT_FAILED + str(payment_id),
        )
    if (
        validate_payment_status is False
        or response_data["payment"]["status"] == "CANCELED"
    ):
        if (
            response_data["payment"]["card_details"]["entry_method"]
            != "ON_FILE"
        ):
            return APPLE_GOOGLE_PAY_USED
        return return_card_data_from_payment_response(response_data)
    if response_data["payment"]["status"] == "APPROVED":
        return False
    return RETRIEVE_PAYMENT_FAILED + str(payment_id)


def generate_payment_for_missed_sessions(*args, admin_screen_payment=True,is_ocpi=True):
    """this function generates payment for missed sessions"""
    (
        last_4_digits,
        exp_month,
        exp_year,
        customer_id,
        amount,
        session,
    ) = args
    customer_cards = make_request(
        GET_REQUEST,
        f"/cards?customer_id={customer_id}&include_disabled=false",
        session.first().user_id.id,
        module="Square retrieve user cards API",
    )
    response_data = json.loads(customer_cards.content)
    if customer_cards.status_code != 200:
        update_session_data_on_failure(session.first(), response_data,is_ocpi=is_ocpi)
        return return_payment_error_message(
            response_data, RETRIEVE_CUSTOMER_CARDS_FAILED
        )
    if "cards" in response_data:
        customer_cards = list(
            filter(
                lambda card: (
                    card["last_4"] == last_4_digits,
                    card["exp_month"] == exp_month,
                    card["exp_year"] == exp_year,
                ),
                response_data["cards"],
            )
        )
        if len(customer_cards):
            card = customer_cards[0]
            pay_body = {
                "source_id": card["id"],
                "amount_money": {
                    "amount": amount,
                    "currency": (
                        "GBP"
                        
                    ),
                },
                "customer_id": customer_id,
            }
            return create_payment_with_auto_deduct(
                pay_body, customer_id, session.first(), admin_screen_payment, is_ocpi=is_ocpi
            )
    return NO_CARDS_ADDED_FOR_CUSTOMER


def amount_formatter(amount):
    """amount formatter"""
    return None if amount is None else int(Decimal(str(amount)) * 100)


def add_failed_payment_amount_in_user_account(
    session_user,
    reference_id,
    payment_id=None,
    due_or_paid_amount="0",
    amount_due_for=None,
    payment_source=None,
    have_due_amount=NO,
    is_ocpi=True
):
    """this function adds due payment amount in user account"""
    if due_or_paid_amount is None or int(float(due_or_paid_amount)) <= 0:
        have_due_amount = NO
    user_profile = Profile.objects.filter(user=session_user)
    previous_due_amount_data = (
        string_to_array_converter(user_profile.first().due_amount_data)
        if user_profile.first().due_amount_data
        else []
    )

    if have_due_amount == NO:
        temp_due_amount_data = []
        prev_due_flag = False
        for session_data in previous_due_amount_data:
            if session_data["reference_id"] != reference_id:
                temp_due_amount_data.append(session_data)
            else:
                prev_due_flag = True
        previous_due_amount_data = temp_due_amount_data
        if prev_due_flag:
            if is_ocpi:
                PaidPaymentLogs.objects.create(
                    user=session_user,
                    charging_session_ocpi=OCPISessions.objects.filter(
                        id=reference_id
                    ).first(),
                    payment_id=payment_id,
                    paid_due_amount=str(due_or_paid_amount),
                    created_date=timezone.localtime(timezone.now()),
                    updated_date=timezone.localtime(timezone.now()),
                )
            else:
                PaidPaymentLogs.objects.create(
                    user=session_user,
                    charging_session=ChargingSession.objects.filter(
                        id=reference_id
                    ).first(),
                    payment_id=payment_id,
                    paid_due_amount=str(due_or_paid_amount),
                    created_date=timezone.localtime(timezone.now()),
                    updated_date=timezone.localtime(timezone.now()),
                )
        handle_user_costa_loyalty(session_user, reference_id,is_ocpi)
    else:
        due_amount_data_updated = NO
        for session_data in previous_due_amount_data:
            if session_data["reference_id"] == reference_id:
                session_data["amount"] = str(due_or_paid_amount)
                session_data["amount_due_for"] = amount_due_for
                session_data["payment_source"] = payment_source
                due_amount_data_updated = YES
        if due_amount_data_updated == NO:
            previous_due_amount_data.append(
                {
                    "amount": str(due_or_paid_amount),
                    "reference_id": reference_id,
                    "amount_due_for": amount_due_for,
                    "payment_source": payment_source,
                }
            )
    user_profile.update(
        have_amount_due=(
            YES
            if [
                session_data
                for session_data in previous_due_amount_data
                if session_data["amount"] != "0"
            ]
            else NO
        ),
        due_amount_data=array_to_string_converter(previous_due_amount_data),
    )


def get_user_due_amount_for_session(user, charging_session_id):
    """this function returns user due amount if it is there"""
    user_profile = Profile.objects.filter(user=user)
    if user_profile.first():
        user_due_amount_data = string_to_array_converter(
            user_profile.first().due_amount_data
        )
        for session_data in user_due_amount_data:
            if (
                str(session_data["reference_id"]) == str(charging_session_id)
                and int(session_data["amount"]) > 0
                and session_data["amount_due_for"] == CHARGING_SESSION
            ):
                return str(session_data["amount"])
    return 0


def get_user_total_due_amount(user, session_reference_id=None):
    """this function returns user due amount if it is there"""
    user_profile = Profile.objects.filter(user=user)
    if user_profile.first() and user_profile.first().due_amount_data:
        user_due_amount_data = string_to_array_converter(
            user_profile.first().due_amount_data
        )
        return sum(
            int(session_data["amount"])
            for session_data in user_due_amount_data
            if (
                (
                    session_reference_id is None and
                    int(session_data["amount"]) > 0
                    and session_data["amount_due_for"] == CHARGING_SESSION
                ) or (
                    session_reference_id and
                    str(session_reference_id) == str(session_data["reference_id"])
                )
            )
        )
    return None


def driivz_get_session_details(transaction_id):
    """this function returns transaction details
    for particular transaction"""
    auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket()
    if auth_response is not None and auth_response.status_code != 200:
        return None
    session_data_response = traced_request(
        GET_REQUEST,
        (
            config(
                "DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL"
            ) + f"/api-gateway/v1/ev-transactions/{transaction_id}"
        ),
        headers={
            "Content-Type": "application/json",
            "dmsTicket": dms_ticket
        },
        timeout=REQUEST_API_TIMEOUT,
    )
    if session_data_response.status_code == 403:
        auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket(
            generate_token=True
        )
        if auth_response is not None and auth_response.status_code != 200:
            return None
        session_data_response = traced_request(
            GET_REQUEST,
            (
                config(
                    "DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL"
                ) + f"/api-gateway/v1/ev-transactions/{transaction_id}"
            ),
            headers={
                "Content-Type": "application/json",
                "dmsTicket": dms_ticket
            },
            timeout=REQUEST_API_TIMEOUT,
        )
    return session_data_response

def validate_session_id(session_data):
    """this function validates drrivz session"""
    if len(session_data.keys()) == 0:
        return [
            False,
            "Session ID not found.",
        ]
    if session_data["transactionStatus"] == "STOPPED":
        return [
            False,
            "Session id is in STOPPED state on Driivz."
            + " Payment cannot be re-processed"
            + ", Session: "
            + str(session_data["transactionId"])
            + ".",
        ]
    if session_data[
        "billingPlanCode"
    ] != filter_function_for_base_configuration(
        DRIIVZ_PLAN_CODE, DEFAULT_DRIIVZ_PLAN_CODE
    ):
        return [
            False,
            "Invalid Session ID: Not an MFG App Session.",
        ]
    return None
