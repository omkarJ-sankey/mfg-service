"""charging sessions apis"""

# Date - 26/06/2021

# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on APIs
#                       related to charging sessions.
#   Name            - chrging session APIs
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 07/06/2025


# These are all the imports that we are exporting from different
# module's from project or library.
import concurrent.futures
import threading
import sys
from datetime import timedelta
import json
from decimal import Decimal

# from square.client import Client
import requests
from simplejson import JSONDecodeError
from passlib.hash import django_pbkdf2_sha256 as handler
from decouple import config

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import datetime, timedelta, timezone

from django.utils import timezone as timezone_util
from django.db.models import Q
import traceback

# pylint:disable=import-error
from backendServices.backend_app_constants import (
    MULTIPLE_LOGIN,
    UNAUTHORIZED,
)
from sharedServices.constants import (
    COMEPLETED,
    CRON_JOB_TIME_INTERVAL,
    NO,
    YES,
    BILLED,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    SESSION_AMOUNT_FOR_SCREENING,
    DEFAULT_SESSION_AMOUNT_FOR_SCREENING,
    EMAIL_ID_FOR_SCREENING,
    ON_HOLD,
    MFG_ADMIN_USERNAME_FOR_SCREENING,
    DEFAULT_MFG_ADMIN_USERNAME_FOR_SCREENING,
    SECRET_KEY_NOT_PROVIDED,
    SECRET_KEY_IN_VALID,
    DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET,
    COSTA_COFFEE,
    ACTIVE,
    OCPI_TOKENS_ENDPOINT,
    REGISTERED_USERS,
    ALL_USERS,
)
from sharedServices.model_files.app_user_models import Profile
from sharedServices.model_files.station_models import (
    ChargePoint,
    StationConnector,
    Stations,
)
from sharedServices.model_files.charging_session_models import ChargingSession
from sharedServices.model_files.config_models import BaseConfigurations
from sharedServices.model_files.loyalty_models import Loyalty
from sharedServices.common import (
    array_to_string_converter,
    get_session_api_call_time,
    handle_concurrent_user_login,
    string_to_array_converter,
    redis_connection,
    filter_function_for_base_configuration,
    get_node_secret,
    date_formater_for_frontend_date,
    get_data_from_cache,
    get_cdr_details,
    ensure_str
)
from sharedServices.common_session_functions import (
    get_session_details,
    amount_formatter,
)

from sharedServices.common_session_payment_functions import (
    get_driivz_account_number_for_user,
    make_session_payment_function,
    make_session_payment_function_ocpi,
)
from sharedServices.email_common_functions import send_hold_session_email

from .session_helper_functions import (
    start_session_back_office_selector,
    stop_session_back_office_selector,
    force_stop_session_back_office_selector,
    handle_start_session_pre_auth,
)
from .swarco_apis import (
    swarco_check_session_status_api_call,
    swarco_generate_tokens_for_new_user,
    swarco_user_authentication_using_refresh_token,
)
from .driivz_apis import (
    update_user_wallet_balance,
    check_3ds_trigger_for_user
)
from .v4_apis import refund_session_payment
from .app_level_constants import (
    DRIIVZ,
    REJECTED,
    RUNNING,
    STARTED,
    STOPPED,
    SWARCO,
    TRANSACTION_ID,
    TRANSACTION_STATUS,
    RUNNING_SESSION_STATUSES,
    CRON_JOB_SESSION_STATUSES,
    CLOSED,
    WALLET_TRANSACTIONS,
    PLEASE_COMPLETE_MOBILE_NUMBER_VERIFICATION,
    UNABLE_TO_CREATE_SESSION,
    BACK_OFFICE_NOT_PROVIDED,
    SESSION_TARRIF_NOT_PROVIDED,
    USER_HAVING_RUNNING_SESSION,
    STATION_NOT_FOUND_MESSAGE,
    CHARGEPOINT_NOT_FOUND_MESSAGE,
    CONNECTOR_NOT_FOUND_MESSAGE,
    EVSE_NOT_FOUND_MESSAGE,
    START_SESSION_ENDPOINT,
    STOP_SESSION_ENDPOINT,
    CONNECTOR_NOT_AVAILABLE,
)
from sharedServices.constants import (
    YES,
    COMMON_ERRORS,
    EMSP_ENDPOINT,
)

from sharedServices.ocpi_common_functions import get_back_office_data, get_user_token_details

from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

# pylint:disable=import-error
from sharedServices.model_files.audit_models import AuditTrail
from sharedServices.model_files.admin_user_models import RoleAccessTypes
from sharedServices.decorators import allowed_users, authenticated_user
from sharedServices.model_files.ocpi_sessions_models import OCPISessions
from sharedServices.model_files.ocpi_locations_models import OCPILocation,OCPIEVSE,OCPIConnector
from sharedServices.constants import OCPI_CREDENTIALS_CACHE_KEY
from sharedServices.model_files.ocpi_credentials_models import OCPICredentials,OCPICredentialsRole
from sharedServices.model_files.ocpi_tokens_models import OCPITokens
from django.forms.models import model_to_dict
from sharedServices.sentry_tracers import traced_request,traced_request_with_retries

from sharedServices.constants import (
    NO,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    REQUEST_API_TIMEOUT,
    SECRET_KEY_IN_VALID,
    SECRET_KEY_NOT_PROVIDED,
    DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET,
    POST_REQUEST,
    CONTENT_TYPE_HEADER_KEY,
    JSON_DATA,
    VAT_PERCENTAGE,
    VAT_PERCENTAGE_KEY
)
from backendServices.charging_sessions.driivz_apis import stop_session_api_call
from sharedServices.model_files.ocpi_charge_detail_records_models import OCPIChargeDetailRecords
# client = Client(
#     access_token=config("DJANGO_PAYMENT_ACCESS_TOKEN"),
#     environment=config("DJANGO_PAYMENT_ENV"),
# )

# payments_api = client.payments

from ..loyalty.v4_apis import get_user_offers

class StartSession(APIView):
    """start session api"""

    @classmethod
    def post(cls, start_session_request):
        """post method to start sessions"""
        try:
            if not start_session_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                start_session_request.user.id, start_session_request.auth
            ):
                return MULTIPLE_LOGIN
            payment_failure_object = {
                "payment_fail": True,
                "two_factor_auth_done": True,
            }
            user_two_factor_auth_done = (
                start_session_request.user.user_profile.two_factor_done
            )
            if (
                user_two_factor_auth_done is None
                or user_two_factor_auth_done == NO
            ):
                payment_failure_object["two_factor_auth_done"] = False
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            PLEASE_COMPLETE_MOBILE_NUMBER_VERIFICATION
                        ),
                        "data": payment_failure_object,
                    }
                )
            back_office = start_session_request.data.get("back_office", None)
            session_tariff = start_session_request.data.get("tariff", None)
            if back_office is None or session_tariff is None:
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": (
                            BACK_OFFICE_NOT_PROVIDED
                            if not back_office
                            else SESSION_TARRIF_NOT_PROVIDED
                        ),
                        "data": payment_failure_object,
                    }
                )
            user_running_sessions = ChargingSession.objects.filter(
                user_id=start_session_request.user, session_status="running"
            )
            if user_running_sessions.first():
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": USER_HAVING_RUNNING_SESSION,
                        "data": payment_failure_object,
                    }
                )
            access_token = Profile.objects.filter(
                user=start_session_request.user
            )

            station = Stations.objects.filter(
                station_id=start_session_request.data.get("station_id", False),
                deleted=NO,
            )
            chargepoint = ChargePoint.objects.filter(
                station_id=station.first(),
                charger_point_name=start_session_request.data.get(
                    "chargepoint", False
                ),
                deleted=NO,
            )
            connector = StationConnector.objects.filter(
                station_id=station.first(),
                charge_point_id=chargepoint.first(),
                connector_id=start_session_request.data.get(
                    "connector", False
                ),
                deleted=NO,
            )
            if not station.first():
                return Response(
                    {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "status": False,
                        "message": STATION_NOT_FOUND_MESSAGE,
                        "data": payment_failure_object,
                    }
                )

            if not chargepoint.first():
                return Response(
                    {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "status": False,
                        "message": CHARGEPOINT_NOT_FOUND_MESSAGE,
                        "data": payment_failure_object,
                    }
                )

            if not connector.first():
                return Response(
                    {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "status": False,
                        "message": CONNECTOR_NOT_FOUND_MESSAGE,
                        "data": payment_failure_object,
                    }
                )
            prev_charging_session = ChargingSession.objects.filter(
                start_time__range=(
                    (timezone_util.localtime(timezone_util.now()) - timedelta(minutes=10)),
                    timezone_util.localtime(timezone_util.now()),
                ),
                station_id=station.first(),
                chargepoint_id=chargepoint.first(),
                paid_status="unpaid",
                is_refund_initiated=NO,
                # connector_id=connector.first(),
                user_id=start_session_request.user,
                back_office=chargepoint.first().back_office,
                session_status="start",
            )
            payment_id = payment_method = payment_type = None
            if prev_charging_session.first():
                charging_session = ChargingSession.objects.filter(
                    id=prev_charging_session.first().id
                )
                charging_session.update(
                    start_time=timezone_util.localtime(timezone_util.now()),
                    session_tariff=start_session_request.data.get("tariff", None),
                )
                charging_session = charging_session.first()
            else:
                charging_session = ChargingSession.objects.create(
                    start_time=timezone_util.localtime(timezone_util.now()),
                    station_id=station.first(),
                    user_account_number=int(
                        start_session_request.user.user_profile.driivz_account_number
                    ),
                    user_card_number=start_session_request.user.user_profile.driivz_virtual_card_number,
                    chargepoint_id=chargepoint.first(),
                    connector_id=connector.first(),
                    user_id=start_session_request.user,
                    back_office=chargepoint.first().back_office,
                    session_status="start",
                    session_tariff=start_session_request.data.get("tariff", None),
                )
                # check_3ds_trigger_for_user(
                #     start_session_request.user,
                #     three_ds_status=False
                # )
                payment_data = handle_start_session_pre_auth(
                    start_session_request, payment_failure_object, charging_session.id
                )
                if not isinstance(payment_data, list):
                    if (
                        start_session_request.user.user_profile.is_3ds_check_active
                    ):
                        check_3ds_trigger_for_user(
                            start_session_request.user,
                            three_ds_status=False
                        )
                    ChargingSession.objects.filter(id=charging_session.id).update(
                        emp_session_id=(
                            str(timezone_util.now().timestamp())
                            + "-"
                            + str(charging_session.id)
                        ),
                        session_status="completed",
                        payment_response=array_to_string_converter([payment_data.data])
                    )
                    return payment_data
                payment_id, payment_method, payment_type = payment_data
                ChargingSession.objects.filter(id=charging_session.id).update(
                    emp_session_id=(
                        str(timezone_util.now().timestamp())
                        + "-"
                        + str(charging_session.id)
                    ),
                    payment_id=payment_id,
                    payment_method=payment_method,
                    payment_type=payment_type,
                )
            if charging_session:
                print(f"Charging session started for user -> {start_session_request.user.id}")
            if not charging_session:
                print(
                    f"Failed to create session entry in database for user -> {start_session_request.user.id}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "status": False,
                        "message": "Failed to create session entry in database",
                        "data": payment_failure_object,
                    }
                )
            payment_failure_object["payment_fail"] = False
            try:
                return Response(
                    start_session_back_office_selector(
                        back_office,
                        start_session_request,
                        station.first(),
                        chargepoint.first(),
                        connector.first(),
                        access_token,
                        payment_id,
                        payment_method,
                        payment_type,
                        payment_failure_object,
                        prev_charging_session
                    )
                )
            except requests.exceptions.ConnectionError:
                return Response(
                    {
                        "status_code": status.HTTP_504_GATEWAY_TIMEOUT,
                        "status": False,
                        "message": "Service Unavailable",
                    }
                )
        except COMMON_ERRORS as error:
            print(
                "Start charging session API failed for the user =>"
                + f"{start_session_request.user}"
                + "\n"
                + f"due to error =>{error}"
                + "\n"
            )
            return API_ERROR_OBJECT


class StartSessionOCPI(APIView):
    """start session api"""

    @classmethod
    def post(cls, start_session_request):
        """post method to start sessions"""
        try:
            if not start_session_request.auth:
                return UNAUTHORIZED
            if not handle_concurrent_user_login(
                start_session_request.user.id, start_session_request.auth
            ):
                return MULTIPLE_LOGIN
            payment_failure_object = {
                "payment_fail": True,
                "two_factor_auth_done": True,
            }
            user_two_factor_auth_done = (
                start_session_request.user.user_profile.two_factor_done
            )
            if (
                user_two_factor_auth_done is None
                or user_two_factor_auth_done == NO
            ):
                payment_failure_object["two_factor_auth_done"] = False
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            PLEASE_COMPLETE_MOBILE_NUMBER_VERIFICATION
                        ),
                        "data": payment_failure_object,
                    }
                )
            back_office = start_session_request.data.get("back_office", None)
            session_tariff = start_session_request.data.get("tariff", None)
            if back_office is None or session_tariff is None:
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": (
                            BACK_OFFICE_NOT_PROVIDED
                            if not back_office
                            else SESSION_TARRIF_NOT_PROVIDED
                        ),
                        "data": payment_failure_object,
                    }
                )
            token = get_node_secret()
            user_tokens = OCPITokens.objects.filter(user_id_id = start_session_request.user, type = 'APP_USER')
            user_token = user_tokens.first()
            if user_token is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            UNABLE_TO_CREATE_SESSION
                        ),
                        "data": payment_failure_object,
                    }
                )
            back_office = back_office.upper()
            token_register_request_data = model_to_dict(user_token)
            token_register_request_data.pop("back_offices")
            if not user_token.is_verified:
                registered_back_offices = user_token.back_offices
                if registered_back_offices.get(back_office) is None:
                    registered_back_offices[back_office] = False
                is_token_registered = registered_back_offices[back_office]
                if not is_token_registered:
                    back_office_list = []
                    back_office_list.append(back_office)
                    token_register_request_data['OCPI']  = back_office_list
                    response = traced_request_with_retries(
                        POST_REQUEST,
                        EMSP_ENDPOINT + OCPI_TOKENS_ENDPOINT,
                        headers={
                            CONTENT_TYPE_HEADER_KEY: JSON_DATA,
                            "Authorization": f"Token {ensure_str(token)}"
                        },
                        data=json.dumps(token_register_request_data, default=str),
                        timeout=REQUEST_API_TIMEOUT,
                    )
                    if response is None or response.status_code != status.HTTP_201_CREATED or json.loads(response.content.decode())["status_code"] != status.HTTP_200_OK:
                        print("Failed to register user token on ",back_office)
                        print("Response from CPO -> ",response.content.decode())
                        return Response(
                                {
                                    "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                                    "status": False,
                                    "message": (
                                        UNABLE_TO_CREATE_SESSION
                                    ),
                                    "data": payment_failure_object,
                                }
                            )
                    else:
                        registered_back_offices[back_office] = True
                        flag  = 0
                        for k,v in registered_back_offices.items():
                            if v is False or v == 0:
                                flag = 1
                        if flag == 1:
                            user_tokens.update(back_offices = registered_back_offices)
                        else:
                            user_tokens.update(is_verified = True, back_offices = registered_back_offices)


            cdr_token = {
                "uid" : user_token.uid,
                "type" : user_token.type,
                "contract_id" : user_token.contract_id,
                "issuer":user_token.issuer,
                "valid":user_token.valid,
                "whitelist":user_token.whitelist,
                "language":user_token.language,
                "last_updated": (user_token.last_updated).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "country_code":user_token.country_code,
                "party_id":user_token.party_id,
            }
            
            user_running_sessions = OCPISessions.objects.filter(
                user_id=start_session_request.user, session_status="running"
            )
            if user_running_sessions.first():
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": USER_HAVING_RUNNING_SESSION,
                        "data": payment_failure_object,
                    }
                )
            access_token = Profile.objects.filter(
                user=start_session_request.user
            )
            station = Stations.objects.filter(
                station_id=start_session_request.data.get("station_id", False),
                deleted=NO,
            )
            if not station.first():
                return Response(
                    {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "status": False,
                        "message": STATION_NOT_FOUND_MESSAGE,
                        "data": payment_failure_object,
                    }
                )

            country_code, party_id = get_back_office_data(back_office)
            location = OCPILocation.objects.filter(
                station_mapping_id = station.first(),
                country_code = country_code,
                party_id = party_id
            )
            if not location.first():
                return Response(
                    {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "status": False,
                        "message": STATION_NOT_FOUND_MESSAGE,
                        "data": payment_failure_object,
                    }
                )
            chargepoint = ChargePoint.objects.filter(
                station_id=station.first(),
                charger_point_name=start_session_request.data.get(
                    "chargepoint", False
                ),
                deleted=NO,
            )
            if not chargepoint.first():
                return Response(
                    {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "status": False,
                        "message": CHARGEPOINT_NOT_FOUND_MESSAGE,
                        "data": payment_failure_object,
                    }
                )
            connector = StationConnector.objects.filter(
                station_id=station.first(),
                charge_point_id=chargepoint.first(),
                connector_id=start_session_request.data.get(
                    "connector", False
                ),
                back_office = back_office.upper(),
                deleted=NO,
            )
            if not connector.first():
                return Response(
                    {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "status": False,
                        "message": CONNECTOR_NOT_FOUND_MESSAGE,
                        "data": payment_failure_object,
                    }
                )
            ocpi_connector = OCPIConnector.objects.filter(
                connector_mapping_id = connector.first(),
                evse_id__location_id = location.first().id
            ).select_related('evse_id')
            if not ocpi_connector.first():
                return Response(
                    {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "status": False,
                        "message": CONNECTOR_NOT_FOUND_MESSAGE,
                        "data": payment_failure_object,
                    }
                )
            evse = OCPIEVSE.objects.filter(
                location_id = location.first(),
                id = ocpi_connector.first().evse_id.id
            )
            if not evse.first():
                return Response(
                    {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "status": False,
                        "message": EVSE_NOT_FOUND_MESSAGE,
                        "data": payment_failure_object,
                    }
                )
            
            connector_status = OCPISessions.objects.filter(
                ~Q(user_id=start_session_request.user),
                session_status__in = ["running","start"],
                station_connector_id = connector.first(),
            )

            if connector_status.first() is not None:
                return Response(
                    {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "status": False,
                        "message": CONNECTOR_NOT_AVAILABLE,
                        "data": payment_failure_object,
                    }
                )


            prev_charging_session = OCPISessions.objects.filter(
                start_datetime__range=(
                    (timezone_util.localtime(timezone_util.now()) - timedelta(minutes=10)),
                    timezone_util.localtime(timezone_util.now()),
                ),
                location_id_id=location.first().id,
                connector_id_id=ocpi_connector.first().id,
                paid_status="unpaid",
                is_refund_initiated=NO,
                user_id_id=start_session_request.user,
                back_office= start_session_request.data.get("back_office"),
                session_status="start"
            )
            payment_id = payment_method = payment_type = None
            if prev_charging_session.first():
                charging_session = OCPISessions.objects.filter(
                    id=prev_charging_session.first().id
                )
                charging_session.update(
                    start_datetime=timezone_util.localtime(timezone_util.now()),
                    session_tariff=start_session_request.data.get("tariff", None),
                )
                charging_session = charging_session.first()
            else:
                
                vat_percentage_raw = get_data_from_cache(VAT_PERCENTAGE_KEY)

                vat_percentage = Decimal(vat_percentage_raw)
                charging_session = OCPISessions.objects.create(
                    start_datetime=timezone_util.localtime(timezone_util.now()),
                    location_id=location.first(),
                    evse_id = evse.first(),
                    user_account_number=user_token.uid,
                    connector_id=ocpi_connector.first(),
                    user_id=start_session_request.user,
                    back_office=start_session_request.data.get("back_office"),
                    session_status="start",
                    session_tariff=start_session_request.data.get("tariff", None),
                    cdr_token = json.dumps(cdr_token),
                    station_id = station.first(),
                    chargepoint_id = chargepoint.first(),
                    station_connector_id = connector.first(),
                    status="AWAITING",
                    vat_percentage = vat_percentage
                )
            payment_data = handle_start_session_pre_auth(
                start_session_request, payment_failure_object, charging_session.id
            )
            if not isinstance(payment_data, list):
                if (
                    start_session_request.user.user_profile.is_3ds_check_active
                ):
                    check_3ds_trigger_for_user(
                        start_session_request.user,
                        three_ds_status=False
                    )
                OCPISessions.objects.filter(id=charging_session.id).update(
                    emp_session_id=(
                        str(timezone_util.now().timestamp())
                        + "-"
                        + str(charging_session.id)
                    ),
                    session_status="completed",
                    payment_response=array_to_string_converter([payment_data.data])
                )
                return payment_data
            
            payment_id, payment_method, payment_type = payment_data
            
            charging_session.emp_session_id = (
                str(timezone_util.now().timestamp())
                + "-"
                + str(charging_session.id)
            )
            charging_session.session_id = charging_session.id
            charging_session.payment_id = payment_id
            charging_session.payment_method = payment_method
            charging_session.payment_type = payment_type
            charging_session.save()
            

            if charging_session:
                request_body = {
                        "token":cdr_token,
                        "session_id": str(charging_session.id),
                        "evse_uid": str(evse.first().uid),
                        "location_id":str(location.first().location_id),
                        "cpo_name":str(start_session_request.data.get("back_office", None))
                    }
                command_data = traced_request_with_retries(
                    POST_REQUEST,
                    EMSP_ENDPOINT +
                    "/" + START_SESSION_ENDPOINT,
                    json=request_body,
                    timeout=REQUEST_API_TIMEOUT,
                    headers= {
                        CONTENT_TYPE_HEADER_KEY: JSON_DATA,
                        "Authorization": f"Token {token}"}
                    )
                
                # if command_data is None or command_data.status_code != status.HTTP_201_CREATED or json.loads(command_data.content.decode())["status_code"] != status.HTTP_200_OK:
                if command_data is None or command_data.status_code != status.HTTP_201_CREATED :
                    return Response(
                    {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "status": False,
                        "message": "Failed to create session",
                        "data": payment_failure_object,
                    }
                )
                
            if not charging_session:
                print(
                    f"Failed to create session entry in database for user -> {start_session_request.user.id}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "status": False,
                        "message": "Failed to create session entry in database",
                        "data": payment_failure_object,
                    }
                )
            print(f"Charging session started for user -> {start_session_request.user.id}")
            payment_failure_object["payment_fail"] = False
            try:
                return Response(
                    start_session_back_office_selector(
                        back_office,
                        start_session_request,
                        station.first(),
                        chargepoint.first(),
                        connector.first(),
                        access_token,
                        payment_id,
                        payment_method,
                        payment_type,
                        payment_failure_object,
                        prev_charging_session
                    )
                )
            except requests.exceptions.ConnectionError:
                return Response(
                    {
                        "status_code": status.HTTP_504_GATEWAY_TIMEOUT,
                        "status": False,
                        "message": "Service Unavailable",
                    }
                )
        except Exception as e:# COMMON_ERRORS as error:
            traceback.print_exc()
            print(
                "Start charging session API failed for the user =>"
                + f"{start_session_request.user}"
                + "\n"
                + f"due to error =>{e}"
                + "\n"
            )
            return API_ERROR_OBJECT
    
    

class SubmitIntermediateSubmitData(APIView):
    """forecefully stop session"""

    @classmethod
    def post(cls, submit_transaction_data_request):
        """post request to submit session intermediate data"""
        try:
            if not submit_transaction_data_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                submit_transaction_data_request.user.id,
                submit_transaction_data_request.auth,
            ):
                return MULTIPLE_LOGIN

            session_id = submit_transaction_data_request.data.get(
                "session_id", None
            )
            session_data = submit_transaction_data_request.data.get(
                "session_data", None
            )
            if session_data is None or session_id is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Transaction details not provided",
                    }
                )

            session = ChargingSession.objects.filter(id=session_id)
            if session.first() is None:
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "status": False,
                        "message": "Session with provided id not found",
                    }
                )
            if session_data[TRANSACTION_STATUS] == STARTED and str(
                session_data["accountNumber"]
            ) == get_driivz_account_number_for_user(
                submit_transaction_data_request.user
            ):
                content = {
                    "cardNumber": session_data["cardNumber"],
                    "connectorId": session_data["connectorId"],
                    "transactionId": session_data["transactionId"],
                    "transactionStatus": session_data["transactionStatus"],
                    "accountNumber": session_data["accountNumber"],
                    "chargeTime": session_data["chargeTime"],
                    "totalEnergy": session_data["totalEnergy"],
                    "realTimePower": session_data["realTimePower"],
                    "startOn": session_data["startOn"],
                    "stopOn": session_data["stopOn"],
                    "cost": session_data["cost"],
                    "chargePower": session_data["chargePower"],
                }
                session.update(
                    emp_session_id=session_data[TRANSACTION_ID],
                    session_status=RUNNING,
                    charging_data=array_to_string_converter([content]),
                )
            else:
                session.update(
                    session_status=REJECTED,
                    charging_data=array_to_string_converter([session_data]),
                    feedback="Session is expired because user did not \
                                    connected to the charger.",
                )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Session data updated.",
                }
            )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT


def get_session_data_for_running_session(running_session, user):
    """this function formats session data for running session"""
    # print("data : ",running_session.connector_id.evse_id.evse_uid)
    # print("data : ",running_session.chargepoint_id.evse_id.evse_uid)
    # print(" connector :",running_session.connector_id.evse_id.evse_uid)
    data = {
        "session_id": running_session.emp_session_id,
        "connector_id": running_session.station_connector_id.id,
        "chargepoint_id": running_session.chargepoint_id.charger_point_id,
        "station_phone": BaseConfigurations.objects.filter(
            base_configuration_key=(
                running_session.chargepoint_id.back_office.lower() + "_number"
            )
        )
        .first()
        .base_configuration_value,
        "back_office": running_session.station_connector_id.back_office,
        "session_api_call_time": get_session_api_call_time(),
        "session_data": (
            string_to_array_converter(running_session.charging_data)[0]
            if running_session.session_status == STOPPED
            else None
        ),
        "offers": get_user_offers(user, running_session.station_id)
    }
    # if running_session.chargepoint_id.back_office == SWARCO:
    #     data["access_token"] = (
    #         Profile.objects.filter(user=user).first().swarco_token
    #     )
    # if running_session.chargepoint_id.back_office == DRIIVZ:
    data["acoount_number"] = get_user_token_details(user)
    return data


class CheckUserRunningSessions(APIView):
    """check user running sessions api"""

    @classmethod
    def post(cls, check_user_running):
        """check user running sessions"""
        try:
            if not check_user_running.auth:
                return UNAUTHORIZED
            if not handle_concurrent_user_login(
                check_user_running.user.id, check_user_running.auth
            ):
                return MULTIPLE_LOGIN

            user_running_sessions = OCPISessions.objects.filter(
                user_id=check_user_running.user,
                session_status__in=RUNNING_SESSION_STATUSES,
            )
            if user_running_sessions.last() is None:
                print(
                    f"user ({check_user_running.user.id}) dont have any running sesions"
                )
                return Response(
                    {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "status": False,
                        "message": "No running sessions",
                        "data": None,
                    }
                )
            print(f"User {check_user_running.user.id}, have running sesions")
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "User have running charging session!",
                    "data": get_session_data_for_running_session(
                        user_running_sessions.last(), check_user_running.user
                    ),
                }
            )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT


class UserAutomaticallyStoppedSessions(APIView):
    """check user running sessions api"""

    @classmethod
    def post(cls, check_user_stopped_sessions):
        """check user running sessions"""
        try:
            if not check_user_stopped_sessions.auth:
                return UNAUTHORIZED
            if not handle_concurrent_user_login(
                check_user_stopped_sessions.user.id,
                check_user_stopped_sessions.auth,
            ):
                return MULTIPLE_LOGIN
            user_stopped_sessions = OCPISessions.objects.filter(
                ~Q(charging_data=None),
                ~Q(payment_response=None),
                user_id=check_user_stopped_sessions.user,
                is_force_stopped=YES,
                session_status=COMEPLETED,
            ).order_by("end_time")
            if (
                user_stopped_sessions.first()
                and user_stopped_sessions.last().is_force_stopped == YES
            ):
                user_stopped_sessions.update(is_force_stopped=NO)
                print(
                    f"User id -{check_user_stopped_sessions.user.id},\
                    user have forcely stopped session"
                )
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "Your last charging session has completed. "
                        + "Check charging history for details.",
                    }
                )
            print(
                f"user {check_user_stopped_sessions.user.id}"
                + "\n"
                + "dont have any forcely stopped session"
            )
            return Response(
                {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "status": False,
                    "message": "No recent force stopped sessions",
                }
            )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT


class ForcedStopSessionsAPI(APIView):
    """forecefully stop session"""

    @classmethod
    def post(cls, force_stop_session):
        """post request to stop session"""
        try:
            if not force_stop_session.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                force_stop_session.user.id, force_stop_session.auth
            ):
                return MULTIPLE_LOGIN

            back_office = force_stop_session.data.get("back_office", None)
            if back_office is None:
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": "Back office not provided.",
                    }
                )
            emp_session_id = force_stop_session.data.get(
                "emp_session_id", None
            )
            if emp_session_id is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Session id not provided",
                    }
                )
            charging_session = ChargingSession.objects.filter(
                user_id=force_stop_session.user,
                emp_session_id=force_stop_session.data["emp_session_id"],
            )

            if charging_session.first() is None:
                return Response(
                    {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "status": False,
                        "message": "Session not found",
                    }
                )

            charging_session.update(
                session_status="closed",
                end_time=timezone_util.localtime(timezone_util.now()),
            )
            return Response(
                force_stop_session_back_office_selector(
                    back_office,
                    force_stop_session,
                )
            )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT


class StopSession(APIView):
    """stop session api"""

    @classmethod
    def post(cls, stop_session_request):
        """stop sesion post method call"""
        try:
            if not stop_session_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                stop_session_request.user.id, stop_session_request.auth
            ):
                return MULTIPLE_LOGIN

            back_office = stop_session_request.data.get("back_office", None)
            if back_office is None:
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": "Back office not provided.",
                    }
                )
            session_id = stop_session_request.data.get("emp_session_id", None)
            if session_id is None:
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": "Session id not provided.",
                    }
                )
            access_token = Profile.objects.filter(
                user=stop_session_request.user
            )
            try:
                return Response(
                    stop_session_back_office_selector(
                        back_office,
                        stop_session_request,
                        access_token,
                        session_id,
                    )
                )
            except requests.exceptions.ConnectionError:
                return Response(
                    {
                        "status_code": status.HTTP_504_GATEWAY_TIMEOUT,
                        "status": False,
                        "message": "Service Unavailable",
                    }
                )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT

class StopSessionOCPI(APIView):
    """stop session api"""

    @classmethod
    def post(cls, stop_session_request):
        """stop sesion post method call"""
        try:
            if not stop_session_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                stop_session_request.user.id, stop_session_request.auth
            ):
                return MULTIPLE_LOGIN

            back_office = stop_session_request.data.get("back_office", None)
            if back_office is None:
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": "Back office not provided.",
                    }
                )
            session_id = stop_session_request.data.get("emp_session_id", None)
            if session_id is None:
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": "Session id not provided.",
                    }
                )
            
            session_object = OCPISessions.objects.filter(session_id = session_id, back_office = back_office)#.first()
            token = get_node_secret()
            try:
                command_response = traced_request_with_retries(
                    POST_REQUEST,
                    EMSP_ENDPOINT +
                    "/" + STOP_SESSION_ENDPOINT,
                    json={
                        "session_id":session_id,
                        "cpo_name":back_office
                    },
                    timeout=REQUEST_API_TIMEOUT,
                    headers={
                        CONTENT_TYPE_HEADER_KEY: JSON_DATA,
                        "Authorization": f"Token {token}"
                        }
                )
                #commented code for future reference
                # if command_response is None or command_response.status_code != status.HTTP_201_CREATED or json.loads(command_response.content.decode())["status_code"] != status.HTTP_200_OK:
                # if command_response is None or command_response.status_code != status.HTTP_201_CREATED :
                #     print("Error: Failed to stop session - ", session_id )
                #     return Response(
                #         {
                #             "status_code": status.HTTP_200_OK,
                #             #status.HTTP_500_INTERNAL_SERVER_ERROR,
                #             "status": True,
                #             "message": command_response.message,
                #         }
                #     )
                if session_object.first().session_status == RUNNING:
                    session_object.update(
                        # session_status="closed",
                        end_time=timezone_util.localtime(timezone_util.now()),
                    )
                account_number = Profile.objects.filter(user_id = stop_session_request.user.id).first().driivz_account_number
                return Response(
                        {
                            "status_code": status.HTTP_200_OK,
                            "status": True,
                            "message": "Successfully stopped session",
                            "data": {
                            "emp_session_id": session_object.first().session_id,
                            "back_office": back_office,
                            "account_number": get_user_token_details(stop_session_request.user)
                            }
                        }
                    )
                # return Response(
                    # stop_session_back_office_selector(
                    #     back_office,
                    #     stop_session_request,
                    #     access_token,
                    #     session_id,
                    # )
                # )
            except requests.exceptions.ConnectionError:
                return Response(
                    {
                        "status_code": status.HTTP_504_GATEWAY_TIMEOUT,
                        "status": False,
                        "message": "Service Unavailable",
                    }
                )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT


class SessionInfoAndFeedback(APIView):
    """submit session feedback api"""

    @classmethod
    def post(cls, session_info_request):
        """post request to submit feedback"""
        try:
            print(
                f"User id-{session_info_request.user.id},"
                "\n"
                "Inside session info and feedback"
            )
            if not session_info_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                session_info_request.user.id, session_info_request.auth
            ):
                return MULTIPLE_LOGIN

            emp_session_id = session_info_request.data.get(
                "emp_session_id", None
            )
            if emp_session_id is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Session id not provided.",
                    }
                )

            user = Profile.objects.filter(user=session_info_request.user)
            session = OCPISessions.objects.filter(
                user_id=session_info_request.user,
                session_id=emp_session_id,
            )
            if session.first() is None or user.first() is None:
                return Response(
                    {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "status": False,
                        "message": (
                            "Session with provided session id not found."
                        ),
                    }
                )
            if session_info_request.data["rating"] in range(1, 6):
                session.update(
                    feedback=session_info_request.data["feedback"],
                    rating=session_info_request.data["rating"],
                    is_force_stopped=NO,
                )
                if (
                    session.first().paid_status != "paid" and session.first().session_status != "completed"
                ):
                    session.update(
                        session_status=CLOSED,
                        # charging_data=array_to_string_converter(
                        #     [session_info_request.data["session_data"]]
                        # ),
                    )
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "Thanks for your feedback!",
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                    "status": False,
                    "message": "Please provide valid data.",
                }
            )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT


def remove_session_cache(session):
    """this function removes session cache set in node server"""
    session_in_cache = redis_connection.get(
        str(session.user_account_number) + "-" + str(session.emp_session_id)
    )
    if session_in_cache and session_in_cache.decode("utf-8") != "null":
        redis_connection.delete(
            str(session.user_account_number)
            + "-"
            + str(session.emp_session_id)
        )
    wallet_amount_in_cache = redis_connection.get(
        str(session.user_account_number)
    )
    user_wallet_runnning_sessions = OCPISessions.objects.filter(
        session_status=RUNNING, payment_id=WALLET_TRANSACTIONS
    ).first()
    if (
        wallet_amount_in_cache
        and wallet_amount_in_cache.decode("utf-8") != "null"
        and user_wallet_runnning_sessions is None
    ):
        redis_connection.delete(str(session.user_account_number))
    if user_wallet_runnning_sessions:
        update_user_wallet_balance(user_wallet_runnning_sessions.user_id)

#This function is unused
#code kept for future reference
def swarco_payment_initialization(session):
    """this function initializes payment for session"""
    sessions = ChargingSession.objects.filter(id=session.id)
    try:
        remove_session_cache(session)
        user = Profile.objects.filter(user=session.user_id)
        auth_response = swarco_user_authentication_using_refresh_token(
            user, user.first().user
        )
        if auth_response.status_code == 401:
            auth_response = swarco_generate_tokens_for_new_user(
                user.first().user
            )

        if auth_response.status_code == 200:
            response = swarco_check_session_status_api_call(
                auth_response, user.first().user, session
            )
            if response.status_code == 200:
                content = json.loads(response.content)
                sessions.update(
                    charging_data=array_to_string_converter([content])
                )
                if content["status"]:
                    print(
                        "SWARCO running state check -> user session \
                            is closed"
                    )
                    payment_status = make_session_payment_function(
                        session.id,
                        session.payment_id,
                        amount_formatter(content["amount"]),
                        config("DJANGO_APP_PAYMENT_CURRENCY"),
                    )
                    sessions.update(
                        session_status="completed",
                        payment_response=payment_status[1],
                    )
                else:
                    sessions.update(session_status="completed")
            if response.status_code != 200:
                try:
                    sessions.update(
                        session_status="completed",
                        charging_data=array_to_string_converter(
                            [json.loads(response.content)]
                        ),
                    )
                except JSONDecodeError:
                    sessions.update(
                        session_status="completed",
                        charging_data=array_to_string_converter(
                            ["SWARCO session API failed."]
                        ),
                    )
        if auth_response.status_code != 200:
            try:
                sessions.update(
                    session_status="completed",
                    charging_data=array_to_string_converter(
                        [json.loads(auth_response.content)]
                    ),
                )
            except JSONDecodeError as erorrespo:
                sessions.update(
                    session_status="completed",
                    charging_data=array_to_string_converter(
                        [
                            "SWARCO authentication failed for user",
                            erorrespo,
                        ]
                    ),
                )

    except ValueError as error:
        # here basic exception is used so that functionality keep
        # running even if one of
        # row in forloop failed to  execute
        (
            exception_type,
            exception_object,
            exception_traceback,
        ) = sys.exc_info()
        print(f"exception_object {exception_object}")
        print(
            f"Error in complete payment sessions cronjob -  \
                time {timezone_util.localtime(timezone_util.now())}"
        )
        print(f"Exception type: {exception_type}")
        print(
            f"File name: {exception_traceback.tb_frame.f_code.co_filename}",
        )
        print(f"Line number: {exception_traceback.tb_lineno}")
        print(f"Error -> {str(error)}")


def driivz_payment_initialization(session):
    """this function initializes payment for session"""
    sessions = ChargingSession.objects.filter(id=session.id)
    try:
        remove_session_cache(session)
        try:
            response = get_session_details(session.emp_session_id)
            if response is None:
                return None
        except requests.exceptions.ConnectionError as error:
            print("Failed to connect to CPO due to->", error)
            return None
        is_force_stopped = NO
        if session.feedback is None and session.rating == 0:
            is_force_stopped = YES
        if response.status_code == 200:
            content = response.json()
            if content[TRANSACTION_STATUS] == BILLED:
                session_data = {
                    "cardNumber": content["cardNumber"],
                    "connectorId": content["connectorId"],
                    "transactionId": content["id"],
                    "transactionStatus": content["transactionStatus"],
                    "accountNumber": content["accountNumber"],
                    "chargeTime": content["chargeTime"],
                    "totalEnergy": content["totalEnergy"],
                    "startOn": content["startedOn"],
                    "stopOn": content["stoppedOn"],
                    "cost": content["cost"],
                    "chargePower": content["chargePower"],
                    "chargePointId": content["chargerId"],
                }
                sessions.update(
                    charging_data=array_to_string_converter([session_data]),
                    is_force_stopped=is_force_stopped,
                    total_cost=amount_formatter(
                        content["cost"]["total"]
                        if "total" in content["cost"]
                        else (
                            content["cost"]["estimated"]
                            if "estimated" in content["cost"]
                            else None
                        )
                    ),
                )
                check_3ds_trigger_for_user(
                    session.user_id,
                    session_id=session
                )
                print(
                    "DRIIVZ running state check -> user session \
                            is closed"
                )
                # due_amount = None
                # if session.preauth_status == "collected":
                #     due_amount = get_user_due_amount_for_session(
                #         session.user_id, session.id
                #     )
                #     if not due_amount:
                #         LOGGER.info(
                #             "Charging session cost not found in charging data"
                #         )
                #         return None
                # session_amount = (
                #     round(float(due_amount))
                #     if due_amount
                #     else amount_formatter(
                #         content["cost"]["total"]
                #         if "total" in content["cost"]
                #         else content["cost"]["estimated"]
                #         if "estimated" in content["cost"]
                #         else None
                #     )
                # )
                session_amount = amount_formatter(
                    content["cost"]["total"]
                    if "total" in content["cost"]
                    else (
                        content["cost"]["estimated"]
                        if "estimated" in content["cost"]
                        else None
                    )
                )
                session_amount_for_screening = (
                    Decimal(
                        filter_function_for_base_configuration(
                            SESSION_AMOUNT_FOR_SCREENING,
                            DEFAULT_SESSION_AMOUNT_FOR_SCREENING,
                        )
                    )
                    # * 100
                )
                if (
                    session_amount >= session_amount_for_screening
                    or ("corruptedReasons" in content)
                ):
                    sessions.update(
                        session_status="completed",
                        paid_status=ON_HOLD,
                    )
                    send_hold_session_email(
                        sessions.first(),
                        session_data,
                        filter_function_for_base_configuration(
                            EMAIL_ID_FOR_SCREENING, ""
                        ),
                        filter_function_for_base_configuration(
                            MFG_ADMIN_USERNAME_FOR_SCREENING,
                            DEFAULT_MFG_ADMIN_USERNAME_FOR_SCREENING,
                        ),
                    )
                else:
                    if session_amount is None:
                        print(
                            "Charging session cost not fount in charging data"
                        )
                        return None
                    payment_status = make_session_payment_function(
                        session.id,
                        session.payment_id,
                        session_amount,
                        config("DJANGO_APP_PAYMENT_CURRENCY"),
                        session.payment_type,
                    )
                    sessions.update(
                        session_status="completed",
                        payment_response=payment_status[1],
                    )
        if response.status_code != 200:
            try:
                sessions.update(
                    session_status="completed",
                    is_force_stopped=is_force_stopped,
                    charging_data=array_to_string_converter(
                        [json.loads(response.content)]
                    ),
                )
            except JSONDecodeError:
                sessions.update(
                    session_status="completed",
                    is_force_stopped=is_force_stopped,
                    charging_data=array_to_string_converter(
                        ["Driivz session API failed."]
                    ),
                )

    except ValueError as error:
        # driivz payment failed
        print(f"Driivz payment failed for session id -> {session.id}")
        print(f"Error {str(error)}")


def driivz_payment_initialization_ocpi(session):
    """this function initializes payment for session"""
    print("Started running parallely")
    sessions = OCPISessions.objects.filter(id=session.id)
    try:
        remove_session_cache(session)
        cdr_data = get_cdr_details(sessions.first())
        if cdr_data.first() is None:
            session.is_cdr_valid = False
            session.save()
            return None
        if cdr_data.last() is not None and json.loads(cdr_data.last().total_cost)["incl_vat"] == 0:
            session.is_cdr_valid = False
            session.save()
            return None
        is_force_stopped = NO
        if session.feedback is None and session.rating == 0:
            is_force_stopped = YES
        # if json.loads(response.content)["status_code"] == 200:
        charge_detail_record = cdr_data#json.loads(response.content)["data"]
        total_energy = 0
        total_time = 0
        total_power = 0
        #check 0 whether we are replacing the object or adding it
        cdr_common_data = cdr_data.first()
        amount_data = json.loads(cdr_common_data.total_cost)
        for cdr in charge_detail_record:
            for obj in json.loads(model_to_dict(cdr)["charging_periods"])[0]['dimensions']:
                match obj['type']:
                    case "ENERGY":
                        total_energy = obj['volume']
                    case "TIME":
                        total_time = obj['volume']
                    case "POWER":
                        total_power = obj['volume']
        # if content[TRANSACTION_STATUS] == BILLED:
        # if not cdr_common_data:
        #     cdr_common_data = session
        cost_data = {
            "currency": session.currency,
            "total": amount_data["incl_vat"] if cdr_common_data else session.total_cost_incl
        }
        session_data = {
            "connectorId": session.connector_id_id if cdr_common_data else session.connector_id_id,
            "transactionId": session.session_id,
            "transactionStatus": session.status,
            "accountNumber": json.loads(cdr_common_data.cdr_token)["uid"] if cdr_common_data else session.user_account_number,
            "chargeTime": format(total_time,".2f"),
            "totalEnergy": format(total_energy,".2f"),
            "startOn": session.start_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
            "stopOn": session.end_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
            "cost": cost_data,#cdr_common_data.total_cost["incl_vat"] if cdr_common_data else session.total_cost_incl,
            "chargePower": format(total_power,".2f"),
        }
        sessions.update(
            charging_data=array_to_string_converter([session_data]),
            is_force_stopped=is_force_stopped,
            is_cdr_valid = True
        )
        
        check_3ds_trigger_for_user(
            session.user_id,
            session_id=session
        )
        print(
            "DRIIVZ running state check -> user session \
                    is closed"
        )
        session_amount = amount_formatter(
            amount_data["incl_vat"] if cdr_common_data else session.total_cost_incl#content["total_cost"]
        )
        session_amount_for_screening = (
            Decimal(
                filter_function_for_base_configuration(
                    SESSION_AMOUNT_FOR_SCREENING,
                    DEFAULT_SESSION_AMOUNT_FOR_SCREENING,
                )
            )
            # * 100
        )
        if (
            session_amount is not None and session_amount >= session_amount_for_screening
        ):
            sessions.update(
                session_status="completed",
                paid_status=ON_HOLD,
            )
            send_hold_session_email(
                sessions.first(),
                session_data,
                filter_function_for_base_configuration(
                    EMAIL_ID_FOR_SCREENING, ""
                ),
                filter_function_for_base_configuration(
                    MFG_ADMIN_USERNAME_FOR_SCREENING,
                    DEFAULT_MFG_ADMIN_USERNAME_FOR_SCREENING,
                ),
            )
        else:
            if session_amount is None:
                print(
                    "Charging session cost not fount in charging data"
                )
                return None
            payment_status = make_session_payment_function_ocpi(
                session.id,
                session.payment_id,
                session_amount,
                config("DJANGO_APP_PAYMENT_CURRENCY"),
                session.payment_type,
            )
            sessions.update(
                session_status="completed",
                payment_response=payment_status[1],
            )
        # if response.status_code != 201:
        #     try:
        #         sessions.update(
        #             session_status="completed",
        #             is_force_stopped=is_force_stopped,
        #             charging_data=array_to_string_converter(
        #                 [json.loads(response.content)]
        #             ),
        #         )
        #     except JSONDecodeError:
        #         sessions.update(
        #             session_status="completed",
        #             is_force_stopped=is_force_stopped,
        #             charging_data=array_to_string_converter(
        #                 ["Driivz session API failed."]
        #             ),
        #         )

    except Exception as error:
        traceback.print_exc()
        # driivz payment failed
        print(f"Driivz payment failed for session id -> {session.id}")
        print(f"Error {str(error)}")


#This function is unused
#code kept for future reference
def session_cron_job_function():
    """this function initiates cron job of session payments"""

    # SWARCO sessions
    swarco_sessions = ChargingSession.objects.filter(
        ~Q(end_time=None),
        ~Q(paid_status="paid"),
        session_status__in=CRON_JOB_SESSION_STATUSES,
        back_office=SWARCO,
    ).filter(
        end_time__lte=timezone_util.localtime(timezone_util.now())
        - timedelta(minutes=CRON_JOB_TIME_INTERVAL)
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(
            swarco_payment_initialization,
            list(swarco_sessions),
        )

    driivz_sessions = ChargingSession.objects.filter(
        ~Q(end_time=None),
        ~Q(paid_status__in=["paid", "On Hold"]),
        ~Q(preauth_status="collected"),
        session_status__in=CRON_JOB_SESSION_STATUSES,
        back_office=DRIIVZ,
    )
    user_ids = []
    filtered_driivz_session = []
    available_issuances = 0
    active_costa_loyalty = Loyalty.objects.filter(
        loyalty_type=COSTA_COFFEE,
        status=ACTIVE,
        deleted=NO,
        valid_from_date__lte=timezone_util.localtime(timezone_util.now()),
        valid_to_date__gte=timezone_util.localtime(timezone_util.now()),
    ).first()
    if active_costa_loyalty and active_costa_loyalty.number_of_total_issuances:
        available_issuances = (
            active_costa_loyalty.number_of_total_issuances
            if active_costa_loyalty.number_of_issued_vouchers is None
            else active_costa_loyalty.number_of_total_issuances
            - active_costa_loyalty.number_of_issued_vouchers
        )
    for driivz_session in driivz_sessions:
        if (
            driivz_session.user_id.id not in user_ids
        ):
            user_ids.append(driivz_session.user_id.id)
            filtered_driivz_session.append(driivz_session)
        if available_issuances and len(filtered_driivz_session) >= available_issuances:
            break
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(
            driivz_payment_initialization,
            filtered_driivz_session,
        )
    print("*******************end of cron job*********************")

def ocpi_session_cron_job_function():
    """this function initiates cron job of session payments"""
    print("started running on a new thread")
    ocpi_sessions = OCPISessions.objects.filter(
        ~Q(end_datetime=None),
        ~Q(paid_status__in=["paid", "On Hold"]),
        ~Q(preauth_status="collected"),
        # is_cdr_valid=None,
        session_status__in=CRON_JOB_SESSION_STATUSES,
    )
    user_ids = []
    filtered_ocpi_sessions = []
    available_issuances = 0
    active_costa_loyalty = Loyalty.objects.filter(
        loyalty_type=COSTA_COFFEE,
        status=ACTIVE,
        deleted=NO,
        valid_from_date__lte=timezone_util.localtime(timezone_util.now()),
        valid_to_date__gte=timezone_util.localtime(timezone_util.now()),
        visibility__in=[REGISTERED_USERS, ALL_USERS],
    ).first()
    if active_costa_loyalty and active_costa_loyalty.number_of_total_issuances:
        available_issuances = (
            active_costa_loyalty.number_of_total_issuances
            if active_costa_loyalty.number_of_issued_vouchers is None
            else active_costa_loyalty.number_of_total_issuances
            - active_costa_loyalty.number_of_issued_vouchers
        )
    for ocpi_session in ocpi_sessions:
        print("session : ",ocpi_session)
        if (
            ocpi_session.user_id.id not in user_ids
        ):
            user_ids.append(ocpi_session.user_id.id)
            filtered_ocpi_sessions.append(ocpi_session)
        if available_issuances and len(filtered_ocpi_sessions) >= available_issuances:
            break
    print("users are : ",user_ids)
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(
            driivz_payment_initialization_ocpi,
            filtered_ocpi_sessions,
        )
    print("*******************end of cron job*********************")


#This function is unused
#code kept for future reference
class AzureFunctionCRONJobAPI(APIView):
    """cronjonb API"""

    @classmethod
    def post(cls, cron_job_request):
        """post method to initialize cron job api"""
        try:
            secret_key_azure = cron_job_request.data.get("secret_key", None)
            if secret_key_azure is None:
                return SECRET_KEY_NOT_PROVIDED
            if not handler.verify(
                secret_key_azure, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
            ):
                return SECRET_KEY_IN_VALID

            start_time = threading.Thread(
                target=session_cron_job_function,
                daemon=True
            )
            start_time.start()

            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Cron job initiated.",
                }
            )

        except COMMON_ERRORS:
            return API_ERROR_OBJECT


class AzureFunctionCRONJobAPIOCPI(APIView):
    """cronjonb API"""

    @classmethod
    def post(cls, cron_job_request):
        """post method to initialize cron job api"""
        try:
            print("Inside payment cron job")
            secret_key_azure = cron_job_request.data.get("secret_key", None)
            if secret_key_azure is None:
                return SECRET_KEY_NOT_PROVIDED
            if not handler.verify(
                secret_key_azure, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
            ):
                return SECRET_KEY_IN_VALID

            start_time = threading.Thread(
                target=ocpi_session_cron_job_function,
                daemon=True
            )
            start_time.start()

            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Cron job initiated.",
                }
            )

        except COMMON_ERRORS:
            return API_ERROR_OBJECT

