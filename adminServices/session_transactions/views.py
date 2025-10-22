"""session transactions views"""

# Date - 11/01/2022


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on views(backend logic)
#                       related to session transactions.
#   Name            - Payment Views
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 26/06/2025

# imports required to create views
import json
import math
from datetime import datetime, timedelta
from types import SimpleNamespace
from decimal import Decimal
import pytz
from cryptography.fernet import Fernet, InvalidToken
from simplejson import JSONDecodeError
from decouple import config
from square.client import Client
from itertools import chain
from cryptography.fernet import Fernet, InvalidToken

from django.db.models import Q, F, ExpressionWrapper, IntegerField
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.cache import cache
from django.views.decorators.http import require_http_methods
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
import traceback
from django.db.models import Value, BooleanField
from django.core.paginator import Paginator
from django.db.models.functions import Coalesce

from django.utils.encoding import force_str



# pylint:disable=import-error
from sharedServices.payments_helper_function import make_request
from sharedServices.model_files.charging_session_models import (
    ChargingSession,
    SessionTransactionStatusTracker,
)
from sharedServices.decorators import allowed_users, authenticated_user
from sharedServices.common import (
    array_to_string_converter,
    date_formater_for_frontend_date,
    filter_url,
    order_by_function,
    pagination_and_filter_func,
    string_to_array_converter,
    time_formatter_for_hours,
    filter_function_for_base_configuration,
    date_difference_function,
    search_validator,
    custom_round_function,
    pagination_function,
    paginate_data,
    get_cdr_details,
)
from sharedServices.common_audit_trail_functions import (
    add_audit_data,
    audit_data_formatter,
)

from sharedServices.common_session_payment_functions import (
    make_session_payment_function,
    make_session_payment_function_ocpi,
)

from sharedServices.common_session_functions import (
    get_session_details,
    send_charging_payment_mail,
    generate_payment_for_missed_sessions,
    amount_formatter,
    validate_payment_id,
    add_failed_payment_amount_in_user_account,
    get_user_due_amount_for_session,
    return_payment_error_message,
    send_old_charging_payment_mail,
    driivz_get_session_details,
)
from sharedServices.common_session_payment_functions import (
    combined_payment_function,
    partial_payment_function,
)
from sharedServices.email_common_functions import (
    get_formated_driivz_start_and_stop_date
)
from sharedServices.payments_helper_function import export_payments_data_function
from sharedServices.model_files.station_models import StationConnector
from sharedServices.model_files.station_models import Stations
from sharedServices.model_files.transaction_models import Transactions

from sharedServices.model_files.app_user_models import Profile
from sharedServices.model_files.ocpi_sessions_models import OCPISessions
from sharedServices.model_files.ocpi_credentials_models import OCPICredentials
from sharedServices.model_files.ocpi_locations_models import OCPIConnector,OCPIEVSE

from sharedServices.model_files.app_user_models import MFGUserEV



from sharedServices.constants import (
    BILLED,
    TRANSACTIONS_CONST,
    YES,
    EXPORT_TRUE,
    GET_METHOD_ALLOWED,
    POST_METHOD_ALLOWED,
    COMMON_ERRORS,
    ERROR_TEMPLATE_URL,
    JSON_ERROR_OBJECT,
    AUDIT_UPDATE_CONSTANT,
    PAYMENT_CONST,
    CHARGING_SESSION,
    NON_WALLET_TRANSACTIONS,
    POST_REQUEST,
    GET_REQUEST,
    WALLET_TRANSACTIONS,
    PARTIAL,
    COMBINED,
    AMOUNT_DUE_REMINDER_TEMPLATE_ID,
    DRIIVZ_PLAN_CODE,
    DEFAULT_DRIIVZ_PLAN_CODE,
    HOLD_PAYMENT_CONST,
    ON_HOLD,
    CARD,
    CARD_BRAND,
    CARD_DETAIL,
    NOT_AVAILABLE,
    INSUFFICIENT_DATA_TO_PROCESS_SESSION_ERROR,
    NEGATIVE_OR_NO_AMOUNT_ERROR,
    FAILED_TO_PROCESS_SESSION,
    SUCCESSFULLY_PROCESSED,
    EDITED_AND_PROCESSED_SUCCESSFULLY,
    EDIT_HOLD_PAYMENT,
    APPROVE,
    ACTION_TYPE,
    EDITED_AMOUNT,
    ERROR_CONST,
    CODE_CONST,
    ADMIN_SCREENING,
    OCPI_LOCATIONS_KEY,
    PAGINATION_COUNT
)

from ..dashboard.app_level_constants import (
    DASHBOARD_DATA_DAYS_LIMIT,
    DEFAULT_DASHBOARD_DATA_DAYS_LIMIT,
)
from .app_level_constants import (
    AMOUNT,
    CHARGEPOINT_ID,
    CODE,
    CURRENCY,
    DETAIL,
    END_DATE_TIME,
    ERRORS,
    PAYMENT,
    RECEIPT_URL,
    PAYMENT_BY_STATUS_LIST,
    SESSION_EXPORT,
    SESSION_STATUS_LIST,
    PAYMENT_STATUS_LIST,
    START_DATE_TIME,
    STATUS,
    TOTAL_MONEY,
    UPDATED_AT,
    FROM_DATE_CONST,
    TO_DATE_CONST,
    APPROVED,
    SESSION_STATUS_COMPLETED,
    TOTAL_ENERGY,
    TOTAL,
    COST,
    APPROVED_MONEY,
    CREATED_AT,
)

client = Client(
    access_token=config("DJANGO_PAYMENT_ACCESS_TOKEN"),
    environment=config("DJANGO_PAYMENT_ENV"),
)

payments_api = client.payments

CACHE_TTL = getattr(settings, "CACHE_TTL", DEFAULT_TIMEOUT)
# This function returns data such as operation regions, regions, area


def export_session_data(filtered_data_session, screen="payment_screen"):
    """export data"""
    session_ids = [
        st.id for st in filtered_data_session["filtered_table_for_export"]
        if not st.is_ocpi
    ]
    session_ids_ocpi = [
        st.id for st in filtered_data_session["filtered_table_for_export"]
        if st.is_ocpi
    ]
    session_transactions_for_export = (
        ChargingSession.objects.filter(id__in=session_ids)
        .values(
            "emp_session_id",
            "payment_id",
            "start_time",
            "end_time",
            "session_status",
            "paid_status",
            "total_cost",
            "payment_response",
            "charging_data",
            "user_account_number",
            "user_id__username",
            "chargepoint_id__charger_point_name",
            "station_id__station_id",
            "station_id__station_name",
        ).annotate(
            # chargepoint_id_id=Subquery(s_connector_subquery),
            is_ocpi=Value(False, output_field=BooleanField()),
            back_office_cdr_id = Value("Not Available"),
            email = F('user_id__encrypted_email'),
            key = F('user_id__key'),
            ocpi_connector_id = Value("Not Available"),
            evse_uid = Value("Not Available")
        ).distinct()
    )
    session_transactions_for_export_ocpi = (
        OCPISessions.objects.filter(id__in=session_ids_ocpi)
        .values(
            "emp_session_id",
            "session_id",
            "payment_id",
            "end_datetime",
            "session_status",
            "paid_status",
            "total_cost_incl",
            "payment_response",
            "charging_data",
            "user_account_number",
            "user_id__username",
            "chargepoint_id__charger_point_name",
            "station_id__station_id",
            "station_id__station_name",
            "cdr_id",
        ).annotate(
            # chargepoint_id_id=Subquery(s_connector_subquery),
            is_ocpi=Value(True, output_field=BooleanField()),
            start_time = F("start_datetime"),
            total_cost = F("total_cost_incl"),
            back_office_cdr_id = Coalesce(F("cdr_id"), Value("Not Available")),
            email = F('user_id__encrypted_email'),
            key = F('user_id__key'),
            ocpi_connector_id = F('connector_id__connector_id'),
            evse_uid = F('evse_id__uid')
        ).distinct()
    )
    for session in session_transactions_for_export:
        if session["start_time"] is not None:
            session["start_time"] = timezone.localtime(session["start_time"])
        if session["end_time"] is not None:
            session["end_time"] = timezone.localtime(session["end_time"])
    for session in session_transactions_for_export_ocpi:
        if session["start_time"] is not None:
            session["start_time"] = timezone.localtime(session["start_time"])
        if session["end_datetime"] is not None:
            session["end_datetime"] = timezone.localtime(session["end_datetime"])

    response = export_payments_data_function(
        # [session_transactions_for_export+session_transactions_for_export_ocpi],
        list(chain(session_transactions_for_export, session_transactions_for_export_ocpi)),
        [SESSION_EXPORT],
        [
            [
                "emp_session_id",
                "back_office_cdr_id",
                "payment_id",
                "start_time",
                "end_time",
                "session_status",
                "paid_status",
                "total_cost",
                "payment_response",
                "user_account_number",
                # "user_id__encrypted_email",
                "user_id__username",
                "chargepoint_id__charger_point_name",
                "station_id__station_id",
                "station_id__station_name",
                "ocpi_connector_id",
                "evse_uid",
                "email",
                "key",
            ]
        ],
        (
            ["Hold Session Transactions"]
            if screen == HOLD_PAYMENT_CONST
            else ["Session Transactions"]
        ),
    )
    if response:
        response.set_cookie(
            "exported_data_cookie_condition",
            EXPORT_TRUE,
            max_age=8,
        )
    return response


def update_date(session_transactions, date_up, date_type):
    """update date"""
    updated_url = ""
    if date_type == FROM_DATE_CONST:
        session_transactions = session_transactions.filter(
            start_time__gte=date_formater_for_frontend_date(date_up)
        )
    else:
        session_transactions = session_transactions.filter(
            start_time__lte=date_formater_for_frontend_date(date_up)
            + timedelta(days=1)
        )
    updated_url += f"&{date_type}={date_up}"
    return [session_transactions, updated_url]


def return_payment_failed_message(message, session_data):
    """this function returns formatted message
    in case of payment failure"""
    return [
        False,
        "Unable to process payment: "
        + str(message)
        + ". Please contact customer directly for payment"
        + " Account: "
        + str(session_data["accountNumber"])
        + ", Session: "
        + str(session_data["transactionId"])
        + ".",
    ]


def complete_session_payment(session, validate_payment_status,is_ocpi = True):
    """complete session payment"""
    try:
        payment_id = session.first().payment_id
        payment_type = session.first().payment_type
        session_data = string_to_array_converter(
            session.first().charging_data
        )[0]
        session_cost = int(
            float(
                get_user_due_amount_for_session(
                    session.first().user_id, session.first().id
                )
            )
        )
        if (
            not session_cost or session_cost <= 0
        ) and session.first().preauth_status != "collected":
            session_cost = amount_formatter(session_data["cost"]["total"])
        if payment_id == WALLET_TRANSACTIONS and payment_type == PARTIAL:
            payment_result = partial_payment_function(
                session.first().id,
                session_cost,
                config("DJANGO_APP_PAYMENT_CURRENCY"),
                session,
                session.first().user_id,
                WALLET_TRANSACTIONS,
                admin_side_payment=True,
                is_ocpi=is_ocpi
            )
            session.update(
                payment_response=payment_result[1][1],
            )
            return [payment_result[0], payment_result[1][0]]
        else:
            payment_id_validation = validate_payment_id(
                payment_id, validate_payment_status, session.user_id.id
            )
            if (
                not session_cost or session_cost <= 0
            ) and session.first().preauth_status != "collected":
                session_cost = amount_formatter(session_data["cost"]["total"])
            else:
                session_cost = amount_formatter(
                    session_data["cost"]["total"]
                ) - int(float((payment_id_validation[3])))
            if payment_type == COMBINED:
                payment_result = combined_payment_function(
                    session.first().id,
                    payment_id,
                    session_cost,
                    config("DJANGO_APP_PAYMENT_CURRENCY"),
                    session,
                    session.first().user_id,
                    NON_WALLET_TRANSACTIONS,
                    admin_side_payment=True,
                    payment_id_validation=payment_id_validation,
                )
                session.update(
                    payment_response=payment_result[1][1],
                )
                return [payment_result[0], payment_result[1][0]]
            else:
                session_uid = session.first().id
                customer_id = session.first().user_id.customer_id

                if isinstance(payment_id_validation, str):
                    return return_payment_failed_message(
                        payment_id_validation, session_data
                    )
                if isinstance(payment_id_validation, list):
                    # payment id is invalid or expired
                    payment_response = generate_payment_for_missed_sessions(
                        payment_id_validation[0:3]
                        + [customer_id, session_cost, session]
                    )
                    if isinstance(payment_response, str):
                        return return_payment_failed_message(
                            payment_response, session_data
                        )
                    print("payment completed")
                    total_cost = payment_response["payment"]["total_money"][
                        "amount"
                    ]
                    add_failed_payment_amount_in_user_account(
                        session.first().user_id,
                        session.first().id,
                        payment_response["payment"]["id"],
                        session_cost,
                    )
                    session.update(
                        payment_response=array_to_string_converter(
                            [payment_response]
                        ),
                        payment_id=payment_response["payment"]["id"],
                        total_cost=total_cost,
                        paid_status="paid",
                    )
                    # is_ocpi =  True
                    if is_ocpi:
                        mail_status = send_charging_payment_mail(
                            session_uid, payment_response,config("DJANGO_APP_CHARGING_SESSION_PAYMENT_MAIL_TEMPLATE_ID")
                        )
                    else:
                        mail_status = send_old_charging_payment_mail(
                            session_uid, payment_response,config("DJANGO_APP_CHARGING_SESSION_PAYMENT_MAIL_TEMPLATE_ID")
                        )
                    if mail_status:
                        print("mail sent")
                        session.update(mail_status="sent")
                    session.update(
                        session_status="completed", is_reviewed="Admin"
                    )
                elif validate_payment_status:
                    # payment id is not expired yet
                    session.update(
                        session_status="closed", is_reviewed="Admin"
                    )
                    return [
                        True,
                        "Payment Re-process initiated. Please check after 10 minutes",
                    ]
    except (ValueError, JSONDecodeError) as error:
        print(f"Session payment process failed due to -> {str(error)}")
        session.update(
            session_status="completed",
            payment_response=array_to_string_converter(
                [
                    "Session payment process failed due to ->",
                    str(error),
                ]
            ),
            is_reviewed="Admin",
        )
        return [
            False,
            "Something went wrong while processing payment,"
            + "Please try after sometime.",
        ]
    return None


def return_payment_authorization_not_found_message(session_data):
    """this function returns payment authorization not found message"""
    return [
        False,
        "Payment Authorisation not found for session. "
        + "Please contact customer directly for payment."
        + " Account: "
        + str(session_data["accountNumber"])
        + ", Session: "
        + str(session_data["transactionId"])
        + ".",
    ]


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


def handle_session_payment(session_id,is_ocpi=True):
    """this function handles payment of unpaid sessions"""
    try:
        #get session details from cpo
        if session_id.first() is not None:
            if session_id.first().paid_status == "paid":
                return [
                    False,
                    "Session already paid. Cannot be re-processed.",
                ]
            session_data = session_id.first()
            # session_not_valid = validate_session_id(session_data)
            # if session_not_valid:
            #     return session_not_valid
            # session_id.update(
            #     charging_data=array_to_string_converter([session_data])
            # )
        if not is_ocpi:
            session_response = driivz_get_session_details(session_id)
            session_data = json.loads(session_response.content)
            session_not_valid = validate_session_id(session_data)
            if session_not_valid:
                return session_not_valid
            session_id.update(
                charging_data=array_to_string_converter([session_data])
            )
            connector_info = StationConnector.objects.filter(
                connector_id=session_data["connectorId"]
            ).first()
            if connector_info is None:
                return return_payment_authorization_not_found_message(
                    session_data
                )
            if (
                connector_info.station_id is None
                or connector_info.charge_point_id is None
            ):
                return return_payment_authorization_not_found_message(
                    session_data
                )
            # submit session details in session table
            start_time = datetime.strptime(
                session_data["startOn"].split(".")[0], "%Y-%m-%dT%H:%M:%S"
            ).replace(tzinfo=pytz.UTC)
            end_time = datetime.strptime(
                session_data["stopOn"].split(".")[0], "%Y-%m-%dT%H:%M:%S"
            ).replace(tzinfo=pytz.UTC)
            start_time_minute = start_time.minute
            
            session_check = ChargingSession.objects.filter(
                user_account_number=session_data["accountNumber"],
                session_status__in=["rejected", "start"],
                connector_id=connector_info,
                start_time__date=start_time.date(),
                start_time__hour=start_time.hour,
                start_time__minute__in=[
                    start_time_minute - 2,
                    start_time_minute - 1,
                    start_time_minute,
                    start_time_minute + 1,
                    start_time_minute + 2,
                ],
            ).order_by("-start_time")

            if session_check.first() is None:
                return return_payment_authorization_not_found_message(
                    session_data
                )
            session = ChargingSession.objects.filter(
                id=session_check.first().id
            )
            session_id.update(
                emp_session_id=session_data["transactionId"],
                end_time=timezone.localtime(end_time),
                charging_data=array_to_string_converter([session_data]),
            )
            if session_data["transactionStatus"] != BILLED:
                session.update(
                    session_status="completed",
                )
                return [
                    False,
                    "Session payment is not completed because,"
                    + " session status is not BILLED.",
                ]
            payment_response = complete_session_payment(
                session_id, True,is_ocpi=is_ocpi  # validate payment id status
            )
            if payment_response:
                return payment_response
        else:
            payment_response = complete_session_payment(
                session_id, False, is_ocpi=is_ocpi  # validate payment id status
            )
            if payment_response:
                return payment_response
        return [
            True,
            "Payment re-processed successfully.",
        ]
    except ConnectionError as error:
        print(f"Session payment process failed due to ->{str(error)}")
        return [
            False,
            "Something went wrong while processing payment,"
            + "Please try after sometime.",
        ]





def get_session_transactions_queryset(
    from_date,
    to_date,
    search,
    page_num,
    queryset,
    order_by_session_id,
    session_status=None,
    paid_status=None,
    reviewed_status=None,
    extra_queryset_modifiers=None,
    is_ocpi = False,
    cdr_id = False,
    is_hold_payment = True
):
    """Returns paginated and filtered session transactions for the given model."""
    
    # Allow further modifications (like annotate) if needed
    if extra_queryset_modifiers:
        queryset = extra_queryset_modifiers(queryset)

    # Apply ordering
    ordered_session_transactions = order_by_function(
        queryset,
        [{"emp_session_id": ["order_by_session_id", order_by_session_id]}],
    )
    queryset = ordered_session_transactions["ordered_table"]
    
    filters = [
                    "station_id__station_name__contains",
                    "station_id__station_id__contains",
                    "user_id__username__contains",
            ]
    if is_ocpi:
        filters.append("session_id__contains")
    else:
        filters.append("emp_session_id__contains")
    if cdr_id:
        filters.append("back_office_cdr_id__contains")
    # Date filtering
    updated_url = ""
    if from_date:
        (queryset, from_date_updated_url) = update_date(
            queryset, from_date, FROM_DATE_CONST
        )
        updated_url += from_date_updated_url
    if to_date:
        (queryset, to_date_updated_url) = update_date(
            queryset, to_date, TO_DATE_CONST
        )
        updated_url += to_date_updated_url

    # Filtering and pagination
    # Check if the filter is for hold payment or transaction list
    if not is_hold_payment:
        filtered_data_session = pagination_and_filter_func(
            page_num,
            queryset,
            [
                {
                    "search": search,
                    "search_array": filters,
                },
                {"paid_status__exact": paid_status},
                {"is_reviewed__exact": reviewed_status},
                {"session_status__exact": session_status},
                # {"back_office_cdr_id__exact": cdr_id},
            ],
        )
    else:
        filtered_data_session = pagination_and_filter_func(
            page_num,
            queryset,
            [
                {
                    "search": search,
                    "search_array": filters,
                }
            ],
        )
    return filtered_data_session, updated_url, ordered_session_transactions["url"]




# This view will help to render list of session transactions.
# Here the function starting with @ is the 'decorator' used to restrict user.
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=TRANSACTIONS_CONST)
def session_transactions_list(request):
    """session transactions list view"""
    try:
        # Database call to fetch all transations
        old_transactions = (
            ChargingSession.objects.only(
                "id",
                "start_time",
                "end_time",
                "user_account_number",
                "is_reviewed",
                "paid_status",
                "session_status",
                "emp_session_id",
                "back_office",
                "user_id_id",
                "mail_status",
                "chargepoint_id_id",
            )
            .filter(~Q(paid_status=ON_HOLD))
            .annotate(
                is_ocpi=Value(False, output_field=BooleanField()),
                session_id = F("emp_session_id"),
                back_office_cdr_id = Value("Not Available"),
            )
            .order_by("-start_time")
        )
       
        ocpi_sessions = OCPISessions.objects.filter(
            ~Q(paid_status=ON_HOLD)
        ).only(
            "id",
            "start_datetime",
            "end_time",
            "user_account_number",
            "is_reviewed",
            "paid_status",
            "session_status",
            "emp_session_id",
            "back_office",
            "user_id_id",
            "mail_status",
            "chargepoint_id_id",
            "location_id_id",
            "end_datetime",
            "cdr_id"
        ).annotate(
            is_ocpi=Value(True, output_field=BooleanField()),
            start_time = F("start_datetime"),
            back_office_cdr_id = Coalesce(F("cdr_id"), Value("Not Available")),
        ).order_by("-start_time")

        
        dashboard_data_days_limit = int(
            filter_function_for_base_configuration(
                DASHBOARD_DATA_DAYS_LIMIT, DEFAULT_DASHBOARD_DATA_DAYS_LIMIT
            )
        )

        from_date = request.GET.get(
            "from_date",
            (
                (
                    timezone.now() - timedelta(days=dashboard_data_days_limit)
                ).strftime("%d/%m/%Y")
            ),
        )
        if from_date == "":
            from_date = (
                timezone.now() - timedelta(days=dashboard_data_days_limit)
            ).strftime("%d/%m/%Y")
        to_date = request.GET.get("to_date", "")

        if (
            to_date != ""
            and (
                date_formater_for_frontend_date(to_date)
                - date_formater_for_frontend_date(from_date)
            ).days
            < 0
        ):
            to_date = ""

        current_and_from_date_difference = (
            timezone.now() - date_formater_for_frontend_date(from_date)
        ).days
        if (
            current_and_from_date_difference <= dashboard_data_days_limit
            and to_date == ""
        ):
            to_date = timezone.now().strftime("%d/%m/%Y")

        maximum_to_date = 0

        to_date_and_from_date_diffrence = (
            current_and_from_date_difference
            if to_date == ""
            else (
                date_formater_for_frontend_date(to_date)
                - date_formater_for_frontend_date(from_date)
            ).days
        )
        if to_date_and_from_date_diffrence > dashboard_data_days_limit:
            to_date = (
                date_formater_for_frontend_date(from_date)
                + timedelta(days=dashboard_data_days_limit)
            ).strftime("%d/%m/%Y")
            maximum_to_date = (
                abs(
                    (
                        timezone.now()
                        - date_formater_for_frontend_date(from_date)
                    ).days
                )
                - dashboard_data_days_limit
            )
        elif (
            to_date != ""
            and current_and_from_date_difference > dashboard_data_days_limit
        ):
            maximum_to_date = (
                abs(
                    (
                        timezone.now()
                        - date_formater_for_frontend_date(from_date)
                    ).days
                )
                - dashboard_data_days_limit
            )

        # Declaration of all query params that helps in filtering
        # data and pagination.
        page_num = request.GET.get("page", 1)
        session_status = request.GET.get("session_status", None)
        paid_status = request.GET.get("paid_status", None)
        reviewed_status = request.GET.get("is_reviewed", None)
        search = request.GET.get("search", None)
        search = search_validator(search)
        do_export = request.GET.get("export", None)
        sessions_available = True
        updated_url = ""
        date_difference = 0
        order_by_session_id = request.GET.get("order_by_session_id", None)

        filtered_data_session_cs, updated_url_cs, url_cs = get_session_transactions_queryset(
            from_date,
            to_date,
            search,
            page_num,
            old_transactions,
            order_by_session_id,
            session_status,
            paid_status,
            reviewed_status,
            is_ocpi=False,
            cdr_id = True,
            is_hold_payment=False
        )
        filtered_data_session_ocpi, _, _ = get_session_transactions_queryset(
            from_date,
            to_date,
            search,
            page_num,
            ocpi_sessions,
            order_by_session_id,
            session_status,
            paid_status,
            reviewed_status,
            is_ocpi=True,
            cdr_id = True,
            is_hold_payment=False
        )
        total_len = filtered_data_session_ocpi["data_count"]+filtered_data_session_cs["data_count"]

        filtered_data_session_ocpi["last_record_number"] += filtered_data_session_cs["last_record_number"]
        # sorted(list(chain(charging_sessions_array, ocpi_charging_sessions_array)), key=lambda s: s["date"])

        # Handeled ordering of old sessions and ocpi sessions according to date
        filtered_table = sorted(list(chain(filtered_data_session_cs['filtered_table_for_export'],filtered_data_session_ocpi['filtered_table_for_export'])), key=lambda s: s.start_time,reverse=True)
        data = paginate_data(filtered_table,page_num)
        number_list = pagination_function(len(filtered_table), filtered_data_session_ocpi["count"], page_num)

        old_sessions_initial_record = filtered_data_session_cs['first_record_number']
        ocpi_sessions_initial_record = filtered_data_session_ocpi['first_record_number']

        paginator = Paginator(filtered_table, filtered_data_session_cs["count"])

        if int(page_num) <= 0 or int(page_num) > math.ceil(total_len / filtered_data_session_cs["count"]):
            page_num = 1
        page = paginator.page(page_num)
        last_record_number = int(page_num) * filtered_data_session_cs["count"]
        first_record_number = last_record_number - (filtered_data_session_cs["count"] - 1)
        last_record_number = min(last_record_number, total_len)
        number_list = pagination_function(total_len, filtered_data_session_cs["count"], page_num)
        prev_page = int(page_num) - 1
        next_page = int(page_num) + 1
        if prev_page <= 0:
            prev_page = None
        if next_page > math.ceil(total_len / filtered_data_session_cs["count"]):
            next_page = None
        if len(page) == 0:
            first_record_number = 0
        
        filtered_data_session = {
            "filtered_table": filtered_table,
            "filtered_table_for_export": filtered_table,
            "data_count": len(filtered_table),
            "first_record_number": old_sessions_initial_record if old_sessions_initial_record != 0 else ocpi_sessions_initial_record,
            "last_record_number": filtered_data_session_ocpi['last_record_number'],
            "number_list": number_list,
            "prev_page": prev_page,
            "next_page": next_page,
            "url": updated_url_cs  + filtered_data_session_ocpi["url"] + url_cs,
        }

        
        if from_date and to_date:
            formatted_to_date = date_formater_for_frontend_date(to_date)
            date_difference = date_difference_function(
                from_date, formatted_to_date
            )

        time_difference = 0
        if from_date:
            time_difference = (
                abs(
                    (
                        date_formater_for_frontend_date(from_date)
                        - timezone.now()
                    ).days
                )
                - 1
            )
        # Here filter_url() function is used to filter navbar
        # elements so that we can render only those navbar tabs
        # to which logged in user have access.
        url_data = filter_url(
            request.user.role_id.access_content.all(), TRANSACTIONS_CONST
        )

        if len(filtered_data_session["filtered_table_for_export"]) == 0:
            sessions_available = False

        if do_export == YES:
            return export_session_data(filtered_data_session)

        context = {
            "to_date_difference_from_current_date": date_difference,
            "session_transactions": list(data['page']),#session_transaction_list,
            "data_count": total_len,
            "first_data_number": first_record_number,
            "last_data_number": last_record_number,
            "session_status_list": SESSION_STATUS_LIST,
            "payment_status_list": PAYMENT_STATUS_LIST,
            "review_status_list": PAYMENT_BY_STATUS_LIST,
            "prev_search": search if search else "",
            "prev_reviewed_status": reviewed_status,
            "prev_session_order": order_by_session_id,
            "prev_paid_status": paid_status,
            "prev_session_status": session_status,
            "prev_from_date": from_date if from_date else "",
            "prev_to_date": to_date if to_date else "",
            "update_url_param": updated_url
            + updated_url_cs  + filtered_data_session_ocpi["url"] + url_cs,
            "pagination_num_list": filtered_data_session["number_list"],
            "current_page": int(page_num),
            "prev": filtered_data_session["prev_page"],
            "next": filtered_data_session["next_page"],
            "data": url_data,
            "sessions_available": sessions_available,
            "maximum_to_date": maximum_to_date,
            "time_difference": time_difference,
            "dashboard_data_days_limit": dashboard_data_days_limit,
        }
        #reprocess payment
        if request.method == "POST":
            session_id = request.POST.get("session_id").strip()
            back_office = session_id.split('-')[0]
            is_ocpi = OCPICredentials.objects.filter(name__iexact = back_office).exists()
            if is_ocpi:
                session = OCPISessions.objects.filter(cdr_id__iexact = session_id)
            else:
                session = ChargingSession.objects.filter(emp_session_id = session_id)
            # is_ocpi = False
            # if session.filter() is None:
            #     session = OCPISessions.objects.filter(session_id = id)
            #     is_ocpi = True
            if session.first() is None:
                return messages.warning(
                    request,
                    "Session ID not found",
                )
            success_tag, message = handle_session_payment(session,is_ocpi)
            session_payment_tracker = SessionTransactionStatusTracker()
            session_payment_tracker.session_id = session_id
            session_payment_tracker.comment = message
            session_payment_tracker.created_date = timezone.localtime(
                timezone.now()
            )
            session_payment_tracker.added_by = request.user
            if success_tag:
                session_payment_tracker.status = "Successful"
                messages.success(
                    request,
                    message,
                )
            else:
                session_payment_tracker.status = "Failed"
                messages.warning(
                    request,
                    message,
                )
            session_payment_tracker.save()
        return render(
            request, "session_transactions/transaction_list.html", context
        )
    except Exception as e:#COMMON_ERRORS:
        traceback.print_exc()
        print(e)
        return render(request, ERROR_TEMPLATE_URL)


# This view will be used to fetched details of session  issues.
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=TRANSACTIONS_CONST)
def view_session_transaction_details(request, session_pk):
    """view sessions issues in details"""
    try:
        enable_pre_auth = False
        square_payment_status = ""
        charging_data = None
        # is_ocpi = bool(request.GET.get("is_ocpi",False))
        # print("request.GET.get(,False) : ",request.GET.get("is_ocpi",False))
        # print("is_ocpi ;",is_ocpi)
        # print(type(is_ocpi))
        is_ocpi_str = request.GET.get("is_ocpi", "false").lower()
        is_ocpi = is_ocpi_str in ("true", "1")
        if is_ocpi is True:
            session = OCPISessions.objects.filter(id=session_pk).annotate(
                    total_cost = ExpressionWrapper(
                        F('total_cost_incl') * 100,
                        output_field=IntegerField()
                    ),
                    back_office_cdr_id = Coalesce(F("cdr_id"), Value("Not Available")),
                    is_ocpi=Value(True, output_field=BooleanField()),
                    ).only(
                    'charging_data',
                    'payment_id',
                    'user_id',
                    'session_status',
                    'preauth_status',
                ).first()
        else:
            session = ChargingSession.objects.filter(id=session_pk).annotate(
                back_office_cdr_id = Value("Not Available"),
                is_ocpi=Value(False, output_field=BooleanField()),
                session_id = F("emp_session_id")
                # evse_id_uid = Value("Not Available"),
                # connector_id_connector_id = Value("Not Available"),
                # user_id_email = Value('user_id__email'),
                # user_id_key = Value('user_id__key'),
                # chargepoint_id_charger_point_name = Value('chargepoint_id__charger_point_name')
                ).only(
                    'charging_data',
                    'payment_id',
                    'user_id',
                    'session_status',
                    'preauth_status',
                    # 'user_id_id',
                ).first()
        user_data = MFGUserEV.objects.filter(id = session.user_id.id).first()
        email = "Not Available"
        key = "Not Available"
        if user_data:
            email = user_data.user_email
            key = user_data.key
        user_profile_details = Profile.objects.filter(
            user=session.user_id
        ).first()
        
        if user_data.key is not None:
            decrypter = Fernet(user_data.key)
            
            decrypted_email = decrypter.decrypt(
                user_data.encrypted_email
            ).decode()
        else:
            decrypted_email = "Not Available"
        # user_last_name = decrypter.decrypt(
        #     user_exists_data.first().last_name
        # ).decode()

        session_data = {
            "start_on": None,
            "stop_on": None,
            "session_duration": None,
            "total_energy": None,
            "charge_point_id": None,
            "total_amount": (
                int(float(session.total_cost)) / 100
                if session.total_cost
                else None
            ),
        }
        if is_ocpi is True:
            cdr_data = get_cdr_details(session)
            cdr_common_data = cdr_data.first()
            if cdr_common_data:
                session_data["total_amount"] = int(json.loads(cdr_common_data.total_cost)["incl_vat"])
        if session.charging_data:
            charging_data = string_to_array_converter(session.charging_data)[0]
            if not session_data["total_amount"]:
                session_data["total_amount"] = (
                    charging_data[COST][TOTAL]
                    if COST in charging_data and TOTAL in charging_data[COST]
                    else None
                )

        if session.payment_id and len(session.payment_id) > 20:
            session.payment_id_sub_parts = [
                session.payment_id[0:20],
                session.payment_id[20:],
            ]

        if session.back_office_cdr_id and len(session.back_office_cdr_id) > 20:
            session.cdr_id_sub_parts = [
                session.back_office_cdr_id[0:20],
                session.back_office_cdr_id[20:],
            ]
        payment_response = make_request(
            GET_REQUEST,
            f"/payments/{session.payment_id}",
            session.user_id.id,
            module="Collect preauth module (get payment)",
        )
        payment_data = json.loads(payment_response.content)
        if (
            payment_response.status_code == 200
            and "payment" in payment_data
            and "error" not in payment_data
        ):
            square_payment_status = payment_data[PAYMENT][STATUS]
            if (
                (session.session_status in [SESSION_STATUS_COMPLETED])
                and (session.preauth_status is None)
                # and (session.total_cost is not None)
                and session.payment_id != WALLET_TRANSACTIONS
                and square_payment_status == APPROVED
                and session_data["total_amount"]
                and int(Decimal(str(session_data["total_amount"])) * 100)
                >= int(payment_data[PAYMENT][APPROVED_MONEY][AMOUNT])
            ):
                enable_pre_auth = True
        if charging_data:
            session_data["start_on"] = (
                get_formated_driivz_start_and_stop_date(
                    charging_data[START_DATE_TIME],
                    provide_local_time_dates=True
                )
                if START_DATE_TIME in charging_data
                else None
            )

            session_data["stop_on"] = (
                get_formated_driivz_start_and_stop_date(
                        charging_data[END_DATE_TIME],
                        provide_local_time_dates=True
                )
                if END_DATE_TIME in charging_data
                else None
            )
            session_data["session_duration"] = (
                time_formatter_for_hours(
                    int(
                        (
                            session_data["stop_on"] - session_data["start_on"]
                        ).total_seconds()
                    )
                )
                if session_data["start_on"] and session_data["stop_on"]
                else None
            )
            session_data["total_energy"] = (
                charging_data[TOTAL_ENERGY]
                if TOTAL_ENERGY in charging_data
                else None
            )
            session_data["evse_uid"] = session.evse_id.uid if is_ocpi and session.evse_id.uid else "Not Available"
            session_data["ocpi_connector_id"] = session.connector_id.connector_id if is_ocpi and session.connector_id.connector_id else "Not Available"
            session_data["charge_point_id"] = (
                session.chargepoint_id.charger_point_id
                if session.chargepoint_id.charger_point_id
                else "Not Available"
            )
        if session.payment_response:
            session_payment_response = string_to_array_converter(
                session.payment_response
            )[0]
            if session.paid_status != "paid":
                if (
                    ERRORS in session_payment_response.keys()
                    and len(session_payment_response[ERRORS]) > 0
                    and DETAIL in session_payment_response[ERRORS][0].keys()
                ):
                    session.payment_message = session_payment_response[ERRORS][
                        0
                    ][DETAIL]
                    if CODE in session_payment_response[ERRORS][0].keys():
                        session.payment_response_code = (
                            session_payment_response[ERRORS][0][CODE]
                        )
                else:
                    session.payment_message = "Errors not available"
            else:
                session.payment_message = "Payment successful"
                if PAYMENT in session_payment_response.keys():
                    session.currency = session_payment_response[PAYMENT][
                        TOTAL_MONEY
                    ][CURRENCY]
                    session.amount = session_payment_response[PAYMENT][
                        TOTAL_MONEY
                    ][AMOUNT]
                    session.payment_time = datetime.strptime(
                        session_payment_response[PAYMENT][UPDATED_AT],
                        "%Y-%m-%dT%H:%M:%S.%fZ",
                    )
                    session.receipt_url = session_payment_response[PAYMENT][
                        RECEIPT_URL
                    ]
        else:
            session.payment_message = "Payment details not available"

        if session.user_id:
            key = session.user_id.key
            if key:
                decrypter = Fernet(key)
                session.user_first_name = decrypter.decrypt(
                    session.user_id.first_name
                ).decode()
                session.user_last_name = decrypter.decrypt(
                    session.user_id.last_name
                ).decode()
                if session.user_id.encrypted_email:    
                    session.user_id.decrypted_email = decrypter.decrypt(
                        session.user_id.encrypted_email
                    ).decode()
                else:
                    session.user_id.decrypted_email = None
        url_data = filter_url(
            request.user.role_id.access_content.all(), TRANSACTIONS_CONST
        )
        context = {
            "data": url_data,
            "session": session,
            "session_data": session_data,
            "user_profile_details": user_profile_details,
            "enable_pre_auth": enable_pre_auth,
            "square_payment_status": square_payment_status,
            "decrypted_email":decrypted_email,
        }

        return render(
            request,
            "session_transactions/session_transaction_details.html",
            context,
        )

    except Exception as e:#COMMON_ERRORS:
        traceback.print_exc()
        return render(request, ERROR_TEMPLATE_URL)


# This view is used to mark the transaction as reviewed
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
def mark_as_reviewed(request):
    """marke session as reviewed"""
    try:
        # Post request to make database queries securely.
        if request.method == "POST":
            # Decoding JSON data from frontend
            post_data_from_front_end = json.loads(
                request.POST["getdata"],
                object_hook=lambda d: SimpleNamespace(**d),
            )

        # Status update operation.
        session = ChargingSession.objects.filter(
            id__exact=int(post_data_from_front_end.session_id)
        )
        if (session.preauth_status != 'collected' or session.paid_status != 'paid') and session.user_card_number is None:
            session = OCPISessions.objects.filter(id__exact=int(post_data_from_front_end.session_id)).first()

        session.update(is_reviewed=YES)
        cache.expire("cache_session_transactions", timeout=0)
        response = {"status": 1, "message": "ok"}
        return JsonResponse(response)
    except COMMON_ERRORS:
        return JSON_ERROR_OBJECT


# This function is used to track payment session
def maintain_session(
    preauth_message,
    session_transaction_status,
    created_at,
    added_by,
    session_id,
):
    SessionTransactionStatusTracker.objects.create(
        comment=preauth_message,
        status=session_transaction_status,
        created_date=created_at,
        added_by=added_by,
        session_id=session_id,
    )


# This function calls squares complete payment api to collect pre auth amount
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=TRANSACTIONS_CONST)
def collect_pre_auth(request, session_id):
    try:
        preauth_message = "Failed to collect preauth"
        status_code = 500
        # is_ocpi = request.GET.get('is_ocpi',False)
        # is_ocpi = request.POST["is_ocpi"]
        is_ocpi_str = request.POST.get("is_ocpi", "false").lower()
        is_ocpi = is_ocpi_str in ("true", "1")
        if is_ocpi :
            session = OCPISessions.objects.filter(id=session_id).annotate(
                is_ocpi=Value(True, output_field=BooleanField()),
                total_cost=ExpressionWrapper(
                        F('total_cost_incl') * 100,
                        output_field=IntegerField()
                    ),
                start_time = F("start_datetime")
                ).first()
        else:
            session = ChargingSession.objects.filter(id=session_id).annotate(
                is_ocpi=Value(False, output_field=BooleanField())
                ).first()

        if session.preauth_status == "collected":
            return JsonResponse(
                {"status_code": 200, "message": "Preauth is already collected"}
            )
        if session.payment_id:
            body = {}
            # complete payment call
            payment_response = make_request(
                POST_REQUEST,
                f"/payments/{session.payment_id}/complete",
                session.user_id.id,
                data=body,
                module="Collect preauth module (complete payment)",
            )
            payment_body = json.loads(payment_response.content)
            session_transaction_status = "Successful"
            if (
                payment_response.status_code != 200
                or "payment" not in payment_body
                or "error" in payment_body
            ):
                print(
                    f"Preauth collection API failed for session => {session.id}"
                )
                session_transaction_status = "Failed"
                maintain_session(
                    preauth_message,
                    session_transaction_status,
                    payment_body[PAYMENT]["updated_at"],
                    request.user.full_name,
                    session.emp_session_id,
                )
                return JsonResponse(
                    {"status_code": status_code, "message": preauth_message}
                )
            else:
                print(
                    f"Preauth collection API Successful for session => {session.id}"
                )
                status_code = 200
                old_data = audit_data_formatter(PAYMENT_CONST, session_id)
                preauth_message = "Preauth collected successfully"
                payment_data = payment_body[PAYMENT]
                transaction = Transactions.objects.create(
                    station_id=Stations.objects.filter(
                        id=session.station_id.id
                    ).first(),
                    payment_id=payment_data["id"],
                    order_id=payment_data["order_id"],
                    transaction_id=payment_data["order_id"],
                    transaction_amount=payment_data["total_money"]["amount"],
                    transaction_currency=payment_data["total_money"][
                        "currency"
                    ],
                    created_date=timezone.now(),
                    payment_response=array_to_string_converter([payment_body]),
                    customer_id=payment_data["customer_id"],
                    payment_for=CHARGING_SESSION,
                    payment_for_reference_id=session.id,
                )
                if not transaction:
                    print(
                        f"Failed to save transaction for session => {session.id}"
                    )
                print(f"Transaction saved for session => {session.id}")
                session_amount = 0
                if is_ocpi:
                    cdr_data = get_cdr_details(session)
                    cdr_common_data = cdr_data.first()
                    if cdr_common_data:
                        session_amount = int(json.loads(cdr_common_data.total_cost)["incl_vat"] * 100)
                else:
                    session_amount = session.total_cost
                if session.total_cost:
                    print(f"Total cost found for session => {session.id}")
                    due_amount = int(session.total_cost) - int(
                        payment_body[PAYMENT]["amount_money"]["amount"]
                    )
                    (
                        add_failed_payment_amount_in_user_account(
                            session.user_id,
                            due_or_paid_amount=due_amount,
                            reference_id=session.id,
                            amount_due_for=CHARGING_SESSION,
                            payment_source=NON_WALLET_TRANSACTIONS,
                            have_due_amount=YES,
                            is_ocpi=session.is_ocpi
                        )
                        if due_amount != 0
                        else add_failed_payment_amount_in_user_account(
                            session.user_id,
                            session.id,
                            payment_body[PAYMENT]["id"],
                            payment_body[PAYMENT]["amount_money"]["amount"],
                            is_ocpi=session.is_ocpi,
                        )
                    )
                    print(f"Due amount updated for session => {session.id}")
                    if due_amount == 0:
                        print(f"Receipt email for session => {session.id}")
                        if is_ocpi:
                            send_session_summary_mail = send_charging_payment_mail(
                                session.id, payment_body
                            )
                            if send_session_summary_mail:
                                OCPISessions.objects.filter(id = session.id).update(mail_status="sent")
                        else:
                            send_session_summary_mail = send_old_charging_payment_mail(
                                session.id, payment_body
                            )
                            if send_session_summary_mail:
                                ChargingSession.objects.filter(id = session.id).update(mail_status="sent")
                    else:
                        print(
                            f"Due remainder email for session => {session.id}"
                        )
                        if is_ocpi:
                            send_due_amount_reminder_email = (
                                send_charging_payment_mail(
                                    session.id,
                                    template_id=AMOUNT_DUE_REMINDER_TEMPLATE_ID,
                                    due_amount=str(due_amount),
                                )
                            )
                        else:
                            send_due_amount_reminder_email = (
                                send_old_charging_payment_mail(
                                    session.id,
                                    template_id=AMOUNT_DUE_REMINDER_TEMPLATE_ID,
                                    due_amount=str(due_amount),
                                )
                            )
                        if send_due_amount_reminder_email:
                            print(
                                f"Due payment reminder email sent for user -> {session.user_id}"
                            )
                if is_ocpi:
                    # cdr_data = get_cdr_details(session)
                    # cdr_common_data = cdr_data.first()
                    # if cdr_common_data:
                    #     session_amount = int(json.loads(cdr_common_data.total_cost)["incl_vat"] * 100)
                    due_amount = int(session_amount) - int(
                        payment_body[PAYMENT]["amount_money"]["amount"]
                    )
                    (
                        add_failed_payment_amount_in_user_account(
                            session.user_id,
                            due_or_paid_amount=due_amount,
                            reference_id=session.id,
                            amount_due_for=CHARGING_SESSION,
                            payment_source=NON_WALLET_TRANSACTIONS,
                            have_due_amount=YES,
                            is_ocpi=session.is_ocpi
                        )
                        if due_amount != 0
                        else add_failed_payment_amount_in_user_account(
                            session.user_id,
                            session.id,
                            payment_body[PAYMENT]["id"],
                            payment_body[PAYMENT]["amount_money"]["amount"],
                            is_ocpi=session.is_ocpi,
                        )
                    )
                    print(f"Due amount updated for session => {session.id}")
                    if due_amount == 0:
                        print(f"Receipt email for session => {session.id}")
                        if is_ocpi:
                            send_session_summary_mail = send_charging_payment_mail(
                                session.id, payment_body
                            )
                            if send_session_summary_mail:
                                OCPISessions.objects.filter(id = session.id).update(mail_status="sent")
                        else:
                            send_session_summary_mail = send_old_charging_payment_mail(
                                session.id, payment_body
                            )
                            if send_session_summary_mail:
                                ChargingSession.objects.filter(id = session.id).update(mail_status="sent")
                    else:
                        print(
                            f"Due remainder email for session => {session.id}"
                        )
                        if is_ocpi:
                            send_due_amount_reminder_email = (
                                send_charging_payment_mail(
                                    session.id,
                                    template_id=AMOUNT_DUE_REMINDER_TEMPLATE_ID,
                                    due_amount=str(due_amount),
                                )
                            )
                        else:
                            send_due_amount_reminder_email = (
                                send_old_charging_payment_mail(
                                    session.id,
                                    template_id=AMOUNT_DUE_REMINDER_TEMPLATE_ID,
                                    due_amount=str(due_amount),
                                )
                            )
                        if send_due_amount_reminder_email:
                            print(
                                f"Due payment reminder email sent for user -> {session.user_id}"
                            )
                    # due_amount = int(session_amount) - int(
                    #     payment_body[PAYMENT]["amount_money"]["amount"]
                    # )
                    print("Due amount value for user ",session.user_id," updated to : ",due_amount)
                    OCPISessions.objects.filter(id = session.id).update(
                        is_reviewed="Admin",
                        session_status="completed",
                        preauth_status="collected",
                        paid_status=(
                            PAYMENT_STATUS_LIST[0]
                            if due_amount == 0
                            else PAYMENT_STATUS_LIST[1]
                        ),
                        payment_response=array_to_string_converter([payment_body]),
                        payment_id=payment_data["id"],
                        payment_completed_at=payment_body[PAYMENT]["updated_at"],
                        preauth_collected_by=request.user.full_name,
                    )
                else:
                    ChargingSession.objects.filter(id = session.id).update(
                        is_reviewed="Admin",
                        session_status="completed",
                        preauth_status="collected",
                        paid_status=(
                            PAYMENT_STATUS_LIST[0]
                            if due_amount == 0
                            else PAYMENT_STATUS_LIST[1]
                        ),
                        payment_response=array_to_string_converter([payment_body]),
                        payment_id=payment_data["id"],
                        payment_completed_at=payment_body[PAYMENT]["updated_at"],
                        preauth_collected_by=request.user.full_name,
                    )
                print(f"Session updated => {session.id}")
                if is_ocpi:
                    maintain_session(
                        preauth_message,
                        session_transaction_status,
                        payment_body[PAYMENT]["updated_at"],
                        request.user,
                        session.session_id,
                    )
                else:
                    maintain_session(
                        preauth_message,
                        session_transaction_status,
                        payment_body[PAYMENT]["updated_at"],
                        request.user,
                        session.emp_session_id,
                    )

                new_data = audit_data_formatter(PAYMENT_CONST, session_id)

                if old_data != new_data:
                    add_audit_data(
                        request.user,
                        f"{session.id}",
                        f"{PAYMENT}-{session.id}",
                        AUDIT_UPDATE_CONSTANT,
                        PAYMENT_CONST,
                        new_data,
                        old_data,
                    )

    except Exception as error:
        traceback.print_exc()
        maintain_session(
            str(error),
            "Failed",
            payment_body[PAYMENT]["updated_at"],
            request.user,
            session.emp_session_id,
        )
        return JsonResponse(
            {"status_code": 500, "message": "Failed to collect preauth"}
        )

    return JsonResponse(
        {"status_code": status_code, "message": preauth_message}
    )


@require_http_methods([GET_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=HOLD_PAYMENT_CONST)
def hold_payment_list(request):
    """this function list down the hold payments"""
    try:
        # Database call to fetch all transations
        session_transactions_old = (
            ChargingSession.objects.only(
                "id",
                "start_time",
                "end_time",
                "user_account_number",
                "is_reviewed",
                "paid_status",
                "session_status",
                "emp_session_id",
                "back_office",
                "user_id_id",
                "mail_status",
                "chargepoint_id_id",
            )
            .annotate(
                back_office_cdr_id = Value("Not Available"),
                is_ocpi=Value(False, output_field=BooleanField()),
                session_id = F("emp_session_id")
                )
            .filter(paid_status=ON_HOLD)
            .order_by("-start_time")
        )

        session_transactions_ocpi = (
            OCPISessions.objects.only(
                "id",
                "session_id",
                "start_datetime",
                "end_time",
                "user_account_number",
                "is_reviewed",
                "paid_status",
                "session_status",
                "emp_session_id",
                "back_office",
                "user_id_id",
                "mail_status",
                "chargepoint_id_id",
            )
            .annotate(
            # chargepoint_id_id=Subquery(s_connector_subquery),
            back_office_cdr_id = Coalesce(F("cdr_id"), Value("Not Available")),
            is_ocpi=Value(True, output_field=BooleanField()),
            start_time = F("start_datetime")
            )
            .order_by("-start_time")
            .filter(paid_status=ON_HOLD)
            )

        # Combine both QuerySets as lists
        # session_transactions = list(session_transactions_old) + list(session_transactions_ocpi)


        dashboard_data_days_limit = int(
            filter_function_for_base_configuration(
                DASHBOARD_DATA_DAYS_LIMIT, DEFAULT_DASHBOARD_DATA_DAYS_LIMIT
            )
        )

        from_date = request.GET.get(
            "from_date",
            (
                (
                    timezone.now() - timedelta(days=dashboard_data_days_limit)
                ).strftime("%d/%m/%Y")
            ),
        )
        if from_date == "":
            from_date = (
                timezone.now() - timedelta(days=dashboard_data_days_limit)
            ).strftime("%d/%m/%Y")
        to_date = request.GET.get("to_date", "")

        if (
            to_date != ""
            and (
                date_formater_for_frontend_date(to_date)
                - date_formater_for_frontend_date(from_date)
            ).days
            < 0
        ):
            to_date = ""

        current_and_from_date_difference = (
            timezone.now() - date_formater_for_frontend_date(from_date)
        ).days
        if (
            current_and_from_date_difference <= dashboard_data_days_limit
            and to_date == ""
        ):
            to_date = timezone.now().strftime("%d/%m/%Y")

        maximum_to_date = 0

        to_date_and_from_date_diffrence = (
            current_and_from_date_difference
            if to_date == ""
            else (
                date_formater_for_frontend_date(to_date)
                - date_formater_for_frontend_date(from_date)
            ).days
        )
        if to_date_and_from_date_diffrence > dashboard_data_days_limit:
            to_date = (
                date_formater_for_frontend_date(from_date)
                + timedelta(days=dashboard_data_days_limit)
            ).strftime("%d/%m/%Y")
            maximum_to_date = (
                abs(
                    (
                        timezone.now()
                        - date_formater_for_frontend_date(from_date)
                    ).days
                )
                - dashboard_data_days_limit
            )
        elif (
            to_date != ""
            and current_and_from_date_difference > dashboard_data_days_limit
        ):
            maximum_to_date = (
                abs(
                    (
                        timezone.now()
                        - date_formater_for_frontend_date(from_date)
                    ).days
                )
                - dashboard_data_days_limit
            )

        # Declaration of all query params that helps in filtering
        # data and pagination.
        page_num = request.GET.get("page", 1)
        # from_date = request.GET.get("from_date", None)
        # to_date = request.GET.get("to_date", None)
        search = request.GET.get("search", None)
        do_export = request.GET.get("export", None)
        sessions_available = True
        updated_url = ""
        date_difference = 0
        # ordering parameters
        order_by_session_id = request.GET.get("order_by_session_id", None)
        
        filtered_data_session_old, updated_url_cs, url_cs = get_session_transactions_queryset(
        from_date,
        to_date,
        search,
        page_num,
        session_transactions_old,
        order_by_session_id,
        )

        filtered_data_session_ocpi, updated_url_cs, url_cs = get_session_transactions_queryset(
        from_date,
        to_date,
        search,
        page_num,
        session_transactions_ocpi,
        order_by_session_id,
        cdr_id = True
        )

        # filtered_table = list(filtered_data_session_old['filtered_table']) + list(filtered_data_session_ocpi['filtered_table'])
        # Handeled ordering of old sessions and ocpi sessions according to date 
        filtered_table = sorted(list(chain(filtered_data_session_old['filtered_table'],filtered_data_session_ocpi['filtered_table'])), key=lambda s: s.start_time,reverse=True)

        data = paginate_data(filtered_table,page_num)
            
        # Here pagination_and_filter_func() is the common function to provide
        # filteration and pagination.
        
        filtered_data_session = {
            "filtered_table": filtered_table,
            "filtered_table_for_export": filtered_table,
            "data_count": data['total_length'],
            "first_record_number": data['first_record_number'],
            "last_record_number": data['last_record_number'],
            "number_list": data['number_list'],
            "prev_page": data['prev_page'],
            "next_page": data['next_page'],
            "url": updated_url_cs  + url_cs,
        }


        time_difference = 0
        if from_date:
            time_difference = (
                abs(
                    (
                        date_formater_for_frontend_date(from_date)
                        - timezone.now()
                    ).days
                )
                - 1
            )
        # Here filter_url() function is used to filter navbar
        # elements so that we can render only those navbar tabs
        # to which logged in user have access.
        url_data = filter_url(
            request.user.role_id.access_content.all(), HOLD_PAYMENT_CONST
        )
        if len(filtered_data_session["filtered_table_for_export"]) == 0:
            sessions_available = False

        if do_export == YES:
            return export_session_data(
                filtered_data_session, screen=HOLD_PAYMENT_CONST
            )
        session_transaction_list = filtered_data_session["filtered_table"]
        for i in data['page']:
            try:
                if i.user_id and i.user_id.encrypted_email and i.user_id.key:
                    decrypter = Fernet(i.user_id.key)
                    i.user_id.decrypted_email = decrypter.decrypt(
                        i.user_id.encrypted_email
                    ).decode()
                else:
                    i.user_id.decrypted_email = None
            except (InvalidToken, ValueError, TypeError) as e:
                print(f"Failed to decrypt email for user {i.user_id}: {e}")
                i.user_id.decrypted_email = None

        context = {
            "to_date_difference_from_current_date": date_difference,
            "session_transactions":  list(data['page']),#session_transaction_list,
            "data_count": filtered_data_session["data_count"],
            "first_data_number": filtered_data_session["first_record_number"],
            "last_data_number": filtered_data_session["last_record_number"],
            "prev_search": search if search else "",
            "prev_session_order": order_by_session_id,
            "prev_from_date": from_date if from_date else "",
            "prev_to_date": to_date if to_date else "",
            "update_url_param": updated_url
            + filtered_data_session["url"],
            # + ordered_session_transactions["url"],
            "pagination_num_list": filtered_data_session["number_list"],
            "current_page": int(page_num),
            "prev": filtered_data_session["prev_page"],
            "next": filtered_data_session["next_page"],
            "data": url_data,
            "sessions_available": sessions_available,
            "maximum_to_date": maximum_to_date,
            "time_difference": time_difference,
            "dashboard_data_days_limit": dashboard_data_days_limit,
        }
        return render(
            request,
            "session_transactions/hold_payment_list.html",
            context,
        )
    except COMMON_ERRORS:
        return JSON_ERROR_OBJECT


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=HOLD_PAYMENT_CONST)
def hold_payment_details(request, session_pk):
    """this function is used to render hold payment details page"""
    try:
        charging_data = None
        # is_ocpi = bool(request.GET.get("is_ocpi",False))
        is_ocpi_str = request.GET.get("is_ocpi", "false").lower()
        is_ocpi = is_ocpi_str in ("true", "1")
        if is_ocpi is True:
            charging_session_queryset = OCPISessions.objects.filter(
                id=session_pk
            ).annotate(
                is_ocpi=Value(True, output_field=BooleanField()),
                # total_cost=F('total_cost_incl'),
                total_cost=ExpressionWrapper(
                        F('total_cost_incl') * 100,
                        output_field=IntegerField()
                    ),
                start_time = F("start_datetime"),
                back_office_cdr_id = F('cdr_id')
            )
        else:
            charging_session_queryset = ChargingSession.objects.filter(
                id=session_pk
            ).annotate(
                is_ocpi=Value(False, output_field=BooleanField()),
                session_id = F("emp_session_id"),
                cdr_id = Value("Not Available"),
                back_office_cdr_id = Value("Not Available")
                )
        
        session = charging_session_queryset.first()
        if session.paid_status.lower() != ON_HOLD.lower():
            return redirect("hold_payment_list")
        if request.method == POST_METHOD_ALLOWED:
            print(POST_REQUEST)
            if session.paid_status == "paid":
                return JsonResponse(
                    {
                        "status": False,
                        "message": "Session is already paid",
                    }
                )
            old_data = audit_data_formatter(HOLD_PAYMENT_CONST, session_pk)
            hold_payment_data = json.loads(request.body.decode("utf-8"))
            session_amount = 0
            reviewed_by = ""
            if is_ocpi:
                cdr_data = get_cdr_details(session)
                cdr_common_data = cdr_data.first()
                if cdr_common_data:
                    session_amount = int(json.loads(cdr_common_data.total_cost)["incl_vat"] * 100)
                else:
                    return JsonResponse(
                        {
                            "status": False,
                            "message": "CDR not found",
                        }
                    )
            if ACTION_TYPE in hold_payment_data:
                if hold_payment_data[ACTION_TYPE] == APPROVE:
                    #handle total cost in ocpi in pennies
                    if not is_ocpi:
                        session_amount = int(session.total_cost)
                    reviewed_by = f"{ADMIN_SCREENING}-{APPROVE}"
                elif (
                    hold_payment_data[ACTION_TYPE] == EDIT_HOLD_PAYMENT
                    and EDITED_AMOUNT in hold_payment_data
                ):
                    session_amount = int(
                        Decimal(str(hold_payment_data[EDITED_AMOUNT])) * 100
                    )
                    reviewed_by = f"{ADMIN_SCREENING}-{EDIT_HOLD_PAYMENT}"
                else:
                    return JsonResponse(
                        {
                            "status": False,
                            "message": INSUFFICIENT_DATA_TO_PROCESS_SESSION_ERROR,
                        }
                    )
                if (
                    isinstance(session_amount, int) is False
                    or session_amount == 0
                ):
                    charging_session_queryset.update(
                        paid_status="unpaid",
                        is_reviewed=reviewed_by,
                    )
                    new_data = audit_data_formatter(
                        HOLD_PAYMENT_CONST, session.id
                    )
                    if old_data != new_data:
                        # maintain log in audit trail
                        add_audit_data(
                            request.user,
                            f"{session.id}, {session.emp_session_id}",
                            f"{HOLD_PAYMENT_CONST}-{session.id}",
                            AUDIT_UPDATE_CONSTANT,
                            HOLD_PAYMENT_CONST,
                            new_data,
                            old_data,
                        )
                    return JsonResponse(
                        {
                            "status": False,
                            "message": NEGATIVE_OR_NO_AMOUNT_ERROR,
                            "updated_data": {
                                "paid_amount": f'£ {format(float(session_amount) / 100, ".2f")}',
                                "payment_time": NOT_AVAILABLE,
                                "paid_status": charging_session_queryset.first().paid_status.capitalize(),
                            },
                        }
                    )
                if is_ocpi:
                    # if hold_payment_data[ACTION_TYPE] == EDIT_HOLD_PAYMENT:
                    #     charging_session_queryset.update(
                    #         total_cost_incl=str(float(session_amount)/100.0),
                    #         is_reviewed=reviewed_by,
                    #     )
                    # else:
                    #     charging_session_queryset.update(
                    #         total_cost_incl=str(float(session_amount)),
                    #         is_reviewed=reviewed_by,
                    #     )
                    charging_session_queryset.update(
                            total_cost_incl=str(float(session_amount)/100),
                            is_reviewed=reviewed_by,
                        )
                else:
                    charging_session_queryset.update(
                        total_cost=str(session_amount),
                        is_reviewed=reviewed_by,
                    )
                if is_ocpi:
                    payment_response = make_session_payment_function_ocpi(
                        session.id,
                        session.payment_id,
                        session_amount,
                        config("DJANGO_APP_PAYMENT_CURRENCY"),
                        session.payment_type,
                    )
                else:
                    payment_response = make_session_payment_function(
                        session.id,
                        session.payment_id,
                        session_amount,
                        config("DJANGO_APP_PAYMENT_CURRENCY"),
                        session.payment_type,
                    )
                charging_session_queryset.update(
                    session_status="completed",
                    payment_response=payment_response[1],
                )
                updated_session = charging_session_queryset.first()
                hold_payment_response = None
                if payment_response is not None and isinstance(
                    payment_response, list
                ):
                    if payment_response[0] is True:
                        hold_payment_response = {
                            "status": True,
                            "message": (
                                EDITED_AND_PROCESSED_SUCCESSFULLY
                                if hold_payment_data[ACTION_TYPE]
                                == EDIT_HOLD_PAYMENT
                                else SUCCESSFULLY_PROCESSED
                            ),
                            "updated_data": {
                                "paid_amount": f'£ {format(float(updated_session.total_cost) / 100, ".2f")}',
                                "payment_time": (
                                    timezone.localtime(
                                        updated_session.payment_completed_at
                                    ).strftime("%d/%m/%Y %H:%M")
                                    if updated_session.payment_completed_at
                                    else NOT_AVAILABLE
                                ),
                                "paid_status": updated_session.paid_status.capitalize(),
                            },
                        }
                    else:
                        charging_session_queryset.update(
                            paid_status="unpaid",
                        )
                        error_response = string_to_array_converter(
                            payment_response[1]
                        )[0]
                        if (
                            isinstance(error_response, dict)
                            and ERROR_CONST in error_response
                            and CODE_CONST in error_response[ERROR_CONST][0]
                        ):
                            hold_payment_response = {
                                "status": False,
                                "message": return_payment_error_message(
                                    error_response,
                                    FAILED_TO_PROCESS_SESSION,
                                ),
                                "updated_data": {
                                    "paid_amount": f'£ {format(float(updated_session.total_cost) / 100, ".2f")}',
                                    "payment_time": (
                                        updated_session.payment_completed_at.strftime(
                                            "%d/%m/%Y %H:%M"
                                        )
                                        if updated_session.payment_completed_at
                                        else NOT_AVAILABLE
                                    ),
                                    "paid_status": charging_session_queryset.first().paid_status.capitalize(),
                                },
                            }
                else:
                    charging_session_queryset.update(
                        paid_status="unpaid",
                    )
                new_data = audit_data_formatter(HOLD_PAYMENT_CONST, session.id)
                if old_data != new_data:
                    # maintain log in audit trail
                    add_audit_data(
                        request.user,
                        f"{session.id}, {session.emp_session_id}",
                        f"{HOLD_PAYMENT_CONST}-{session.id}",
                        AUDIT_UPDATE_CONSTANT,
                        HOLD_PAYMENT_CONST,
                        new_data,
                        old_data,
                    )
                if hold_payment_response:
                    return JsonResponse(hold_payment_response)
                return JsonResponse(
                    {
                        "status": False,
                        "message": FAILED_TO_PROCESS_SESSION,
                        "updated_data": {
                            "paid_amount": f'£ {format(float(updated_session.total_cost) / 100, ".2f")}',
                            "payment_time": (
                                updated_session.payment_completed_at.strftime(
                                    "%d/%m/%Y %H:%M"
                                )
                                if updated_session.payment_completed_at
                                else NOT_AVAILABLE
                            ),
                            "paid_status": charging_session_queryset.first().paid_status.capitalize(),
                        },
                    }
                )
            return JsonResponse(
                {
                    "status": False,
                    "message": INSUFFICIENT_DATA_TO_PROCESS_SESSION_ERROR,
                }
            )
        status_details = {
            "session_status": (
                session.session_status
                if session.session_status
                else NOT_AVAILABLE
            ),
            "payment_status": (
                session.paid_status if session.paid_status else NOT_AVAILABLE
            ),
            "mail_status": (
                session.mail_status if session.mail_status else NOT_AVAILABLE
            ),
            "driivz_amount": NOT_AVAILABLE,
        }
        if is_ocpi:
            session_id = session.session_id if session.session_id else NOT_AVAILABLE
        else:
            session_id = session.emp_session_id if session.emp_session_id else NOT_AVAILABLE

        session_details = {
            "session_id": (
                session_id
            ),
            "charge_point_id": NOT_AVAILABLE,
            "back_office": (
                session.back_office if session.back_office else NOT_AVAILABLE
            ),
            "start_time": NOT_AVAILABLE,
            "end_time": NOT_AVAILABLE,
            "duration": NOT_AVAILABLE,
            "power_consumed": NOT_AVAILABLE,
            "station_name": (
                session.station_id.station_name
                if session.station_id
                else NOT_AVAILABLE
            ),
        }
        if session.charging_data:
            charging_data = string_to_array_converter(session.charging_data)[0]
            # if (
            #     charging_data and
            #     'transactionStatus' in charging_data and
            #     charging_data['transactionStatus'] == BILLED
            # ):
            status_details["driivz_amount"] = (
                f"£ {charging_data[COST][TOTAL]}"
            )
            session_details["start_time"] = (
                get_formated_driivz_start_and_stop_date(
                    charging_data[START_DATE_TIME],
                    provide_local_time_dates=True
                )
                if START_DATE_TIME in charging_data
                else NOT_AVAILABLE
            )
            session_details["end_time"] = (
                get_formated_driivz_start_and_stop_date(
                    charging_data[END_DATE_TIME],
                    provide_local_time_dates=True
                )
                if END_DATE_TIME in charging_data
                else NOT_AVAILABLE
            )
            session_details["duration"] = (
                time_formatter_for_hours(
                    int(
                        (
                            session_details["end_time"]
                            - session_details["start_time"]
                        ).total_seconds()
                    )
                )
                if session_details["start_time"] != NOT_AVAILABLE
                and session_details["end_time"] != NOT_AVAILABLE
                else NOT_AVAILABLE
            )
            session_details["power_consumed"] = (
                charging_data[TOTAL_ENERGY]
                if TOTAL_ENERGY in charging_data
                else NOT_AVAILABLE
            )
            session_details["user_account_number"] = session.user_account_number
            # print("evse id is : ",session.evse_id.uid, is_ocpi)
            session_details["evse_uid"] = session.evse_id.uid if is_ocpi and session.evse_id.uid else "Not Available"
            session_details["ocpi_connector_id"] = session.connector_id.connector_id if is_ocpi and session.connector_id.connector_id else "Not Available"
            session_details["charge_point_id"] = (
                session.chargepoint_id.charger_point_id
                if session.chargepoint_id.charger_point_id
                else "Not Available"
            )
            session_details["cdr_id"] = session.cdr_id if is_ocpi else "Not Available"
            if session_details["cdr_id"] and len(session_details["cdr_id"]) > 20:
                session_details["cdr_id_sub_parts"] = [
                    session_details["cdr_id"][0:20],
                    session_details["cdr_id"][20:],
                ]
        amount = NOT_AVAILABLE
        if session.total_cost:
            # amount = f"£ {format(session.total_cost,'.2f')}"
            amount = f"£ {format(float(session.total_cost)/100,'.2f')}"
            # if is_ocpi:
            #     amount = f"£ {format(session.total_cost,'.2f')}"
            # else:
            #     amount = f"£ {format(float(session.total_cost)/100,'.2f')}"

        payment_details = {
            "payment_id": (
                [
                    (
                        session.payment_id[0:20]
                        if len(session.payment_id) > 20
                        else session.payment_id
                    ),
                    (
                        session.payment_id[20:]
                        if len(session.payment_id) > 20
                        else ""
                    ),
                ]
                if session.payment_id
                else NOT_AVAILABLE
            ),
            "type_of_payment": (
                session.payment_method
                if session.payment_method
                else NOT_AVAILABLE
            ),
            "card_brand": NOT_AVAILABLE,
            "amount": (
                amount
            ),
            "payment_time": (
                session.payment_completed_at
                if session.payment_completed_at
                else NOT_AVAILABLE
            ),
            "payment_initiated_by": (
                session.is_reviewed if session.is_reviewed else NOT_AVAILABLE
            ),
        }
        payment_response = make_request(
            GET_REQUEST,
            f"/payments/{session.payment_id}",
            session.user_id.id,
            module="Hold payment module (get payment)",
        )
        payment_data = json.loads(payment_response.content)
        if payment_response.status_code == 200 and PAYMENT in payment_data:
            # payment_details["type_of_payment"]=session.payment_method
            payment_details["card_brand"] = payment_data[PAYMENT][CARD_DETAIL][
                CARD
            ][CARD_BRAND]
            payment_details["preauth_amount"] = format(
                float(payment_data[PAYMENT][APPROVED_MONEY][AMOUNT]) / 100,
                ".2f",
            )
            payment_details["preauth_time"] = timezone.localtime(
                datetime.strptime(
                    payment_data[PAYMENT][CREATED_AT],
                    "%Y-%m-%dT%H:%M:%S.%fZ",
                ).replace(tzinfo=pytz.UTC)
            )
        user_details = {
            "username": (
                session.user_id.username
                if session.user_id
                else "Not available "
            ),
            "driivz_account_number": (
                session.user_account_number
                if session.user_account_number
                else NOT_AVAILABLE
            ),
        }
        reviews = {
            "rating": session.rating if session.rating else NOT_AVAILABLE,
            "feedback": (
                session.feedback if session.feedback else NOT_AVAILABLE
            ),
        }
        calculated_session_amount = None
        if session.session_tariff is not None and (
            session_details["power_consumed"] != NOT_AVAILABLE
        ):
            calculated_session_amount = custom_round_function(
                Decimal(str(session_details["power_consumed"]))
                * Decimal(
                    str(session.session_tariff.replace("/kWh", "").strip())
                ),
                2,
            )
        url_data = filter_url(
            request.user.role_id.access_content.all(), HOLD_PAYMENT_CONST
        )

        if session.user_id.key is not None:
            decrypter = Fernet(session.user_id.key)
            
            decrypted_email = decrypter.decrypt(
                session.user_id.encrypted_email
            ).decode()
        else:
            decrypted_email = "Not Available"

        # decrypter = Fernet(session.user_id.key)
        # decrypted_email = decrypter.decrypt(
        #     session.user_id.encrypted_email
        # ).decode()
        context = {
            "data": url_data,
            "status_details": status_details,
            "charging_session": session,
            "session_details": session_details,
            "payment_details": payment_details,
            "user_details": user_details,
            "decrypted_email":decrypted_email,
            "reviews": reviews,
            "calculated_session_amount": calculated_session_amount,
            "formatted_session_tariff": (
                session.session_tariff.replace("/kWh", "").strip()
                if session.session_tariff
                else NOT_AVAILABLE
            ),
            "decrypted_email":decrypted_email,
        }

        return render(
            request,
            "session_transactions/hold_payment_details.html",
            context,
        )

    except Exception as e:#COMMON_ERRORS:
        traceback.print_exc()
        return render(request, ERROR_TEMPLATE_URL)
