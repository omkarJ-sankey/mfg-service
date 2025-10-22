"""driivz apis"""
# Date - 16/02/2022

# File details-
#   Author          - Manish Pawar
#   Description     - This file contains driivz API to start or stop session.
#   Name            - Driivz functions
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 27/09/2025


# These are all the imports that we are exporting from
# different module's from project or library.

import json
import math
import pytz
from decimal import Decimal
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from decouple import config

from django.utils import timezone
from django.db.models import Q, F

from rest_framework import status

# pylint:disable=import-error

from sharedServices.gift_card_common_functions import get_user_gift_card_details
from sharedServices.common import (
    redis_connection, 
    string_to_array_converter,
    filter_function_for_base_configuration
)
from sharedServices.common_session_payment_functions import (
    get_driivz_account_number_for_user,
)
from sharedServices.common_session_functions import (
    get_session_details
)
from sharedServices.model_files.app_user_models import Profile

from sharedServices.model_files.config_models import BaseConfigurations
from sharedServices.model_files.charging_session_models import (
    ChargingSession,
    ThreeDSTriggerLogs,
    ThreeDSCheckLogs
)
from sharedServices.model_files.loyalty_models import Loyalty, UserLoyaltyTransactions
from sharedServices.constants import (
    SESSION_CLOSED,
    WALLET_TRANSACTIONS,
    DRIIVZ_PLAN_CODE,
    REQUEST_API_TIMEOUT,
    ON_CONST,
    DRIIVZ,
    TOTAL_ENERGY,
    NO,
    GENERIC_OFFERS,
    PATCH_REQUEST,
    FREE_LOYALTY,
    YES,
    PURCHASED,
)
from sharedServices.driivz_api_gateway_functions import (
    get_driivz_api_gateway_dms_ticket
)
from sharedServices.sentry_tracers import traced_request
from ..auths.auth_utils import (
    auth_register_mfg_user_with_drrivz_v4,
)
from ..loyalty.v4_apis import get_user_offers

from .app_level_constants import (
    CARD_ID,
    DRIIVZ,
    DRRIVZ_USER_ACCOUNT_NUMBER,
    DRRIVZ_USER_VIRTUAL_CARD_ID,
    DRRIVZ_USER_VIRTUAL_CARD_NUMBER,
    DRIIVZ_CURRENCY,
    DRIIVZ_PLAN_ID,
    RUNNING,
    DRIIVZ_CHECK_FORCE_STOP_CONDITIONS,
)

from sharedServices.model_files.ocpi_tokens_models import OCPITokens


from sharedServices.model_files.ocpi_sessions_models import OCPISessions
from sharedServices.model_files.ocpi_locations_models import OCPILocation,OCPIEVSE,OCPIConnector

def get_required_fields_to_register_driivz_user():
    """this function returns required fields to register DRIIVZ user"""
    return {
        "currency": BaseConfigurations.objects.filter(
            base_configuration_key=DRIIVZ_CURRENCY
        )
        .first()
        .base_configuration_value,
        "planCode": BaseConfigurations.objects.filter(
            base_configuration_key=DRIIVZ_PLAN_CODE
        )
        .first()
        .base_configuration_value,
        "planId": int(
            BaseConfigurations.objects.filter(
                base_configuration_key=DRIIVZ_PLAN_ID
            )
            .first()
            .base_configuration_value
        ),
    }


def return_customer_data(mfg_user):
    """this function returns customer data to registet with DRIIVZ"""

    decrypter = Fernet(mfg_user.key)
    return {
        "email": decrypter.decrypt(mfg_user.encrypted_email).decode(),
        "first_name": decrypter.decrypt(mfg_user.first_name).decode(),
        "last_name": decrypter.decrypt(mfg_user.last_name).decode(),
        "phone": decrypter.decrypt(mfg_user.encrypted_email).decode(),
    }


def session_register_mfg_user_with_drrivz(mfg_user):
    """this function registers MFG app user with DRIIVZ"""
    customer_data = return_customer_data(mfg_user)
    response_data = auth_register_mfg_user_with_drrivz_v4(
        customer_data["first_name"],
        customer_data["last_name"],
        customer_data["email"],
        customer_data["phone"],
        False
    )
    if (
        DRRIVZ_USER_ACCOUNT_NUMBER in response_data and
        DRRIVZ_USER_VIRTUAL_CARD_ID in response_data and
        DRRIVZ_USER_VIRTUAL_CARD_NUMBER in response_data
    ):
        Profile.objects.filter(user=mfg_user).update(
            driivz_account_number=response_data[DRRIVZ_USER_ACCOUNT_NUMBER],
            driivz_virtual_card_id=response_data[DRRIVZ_USER_VIRTUAL_CARD_ID],
            driivz_virtual_card_number=response_data[
                DRRIVZ_USER_VIRTUAL_CARD_NUMBER
            ],
        )
        return response_data
    return None


def update_user_wallet_balance(user):
    """this function sets user wallet balance in cache and database"""
    gift_card_data = get_user_gift_card_details(
        user.get_customer_id(), user.id
    )
    if (
        gift_card_data
        and gift_card_data["status"] is False
        and gift_card_data["message"]
    ):
        print(
            f"failed to get user gift card details for user -> {user.id} \
                with message -> {gift_card_data['message']}"
        )
        return None
    amount = gift_card_data["data"]["wallet_balance"]
    redis_connection.set(str(user.user_profile.driivz_account_number), amount)
    Profile.objects.filter(user=user).update(wallet_balance=amount)


def start_or_stop_session_with_driivz_api_gateway(
    connector_id,
    dms_ticket,
    mfg_user,
    action="start"
):
    """this function requests DRIIVZ API gateway to start or stop user session"""
    payload = json.dumps({
        CARD_ID: mfg_user.user_profile.driivz_virtual_card_id,
        "reason": "PAY_PER_USE" if action =="start" else "MAX_CHARGE_DURATION_REACHED"
    })

    return traced_request(
        "POST" if action == "start" else PATCH_REQUEST,
        (
            config(
                "DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL"
            ) + "/api-gateway/v1/chargers/connectors/"
            + connector_id
            + f"/remote-operations/{action}-transaction"
        ),
        headers={
            "Content-Type": "application/json",
            "dmsTicket": dms_ticket
        },
        data=payload,
        timeout=REQUEST_API_TIMEOUT,
    )

def update_wallet_and_get_promotions_data(*args):
    (
        back_office,
        mfg_user,
        station,
        _,
        payment_id,
        payment_failure_object,
    ) = args
    if payment_id == WALLET_TRANSACTIONS:
        update_user_wallet_balance(mfg_user)

    user_token = OCPITokens.objects.filter(user_id_id = mfg_user.id)

    return {
        "status_code": "200",
        "status": True,
        "message": "Successfully started session",
        "data": {
            **{
                "account_number": user_token.first().uid,
                "back_office": back_office,
                "dynamic_api_call_time": int(
                    filter_function_for_base_configuration(
                        "dynamic_api_call_time",
                        30000
                    )
                ),
                "session_api_call_time": int(
                    filter_function_for_base_configuration(
                        "session_api_call_time",
                        15000
                    )
                ),
                "offers": [
                    {
                        "id": offer["id"],
                        "image": offer["image"],
                        "offer_type": offer["offer_type"] == GENERIC_OFFERS
                    }
                    for offer in list((
                        Loyalty.objects.filter(
                            ~Q(image=None),
                            Q(
                                number_of_total_issuances__isnull=False,
                                number_of_issued_vouchers__isnull=False,
                                number_of_total_issuances__gt=0,
                                number_of_issued_vouchers__gt=0,
                                number_of_issued_vouchers__lt=F('number_of_total_issuances'),
                            ) |
                            Q(
                                Q(number_of_total_issuances__isnull=True) |
                                Q(number_of_issued_vouchers__isnull=True) |
                                Q(number_of_total_issuances__lte=0) |
                                Q(number_of_issued_vouchers__lte=0)
                            ),
                            station_available_loyalties__station_id=station,
                            station_available_loyalties__deleted=NO,
                            deleted=NO,
                            status="Active",
                            valid_from_date__lte=timezone.localtime(timezone.now()),
                            valid_to_date__gte=timezone.localtime(timezone.now()),
                            display_on_charging_screen=True,
                            visibility__in=[None,"All Users","Registered Users"]
                            # number_of_issued_vouchers__lt=F('number_of_total_issuances')
                        )
                        .values("id", "image", "offer_type")
                        .distinct()
                    ))
                ]
            },
            **payment_failure_object,
        },
    }


def start_driivz_session_api_call(*args):
    """this function starts driivz session"""
    (
        mfg_user,
        station,
        connector,
        payment_id,
        payment_failure_object,
    ) = args
    if payment_id == WALLET_TRANSACTIONS:
        update_user_wallet_balance(mfg_user)

    
    
    # auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket()
    # user_token = OCPITokens.objects.filter(user_id_id = mfg_user.id)
    # if auth_response is not None and auth_response.status_code != 200:
    #     print(
    #         "Failed to start driivz session for user -> "
    #         f"{mfg_user.id} as driivz auth api failed"
    #     )
    #     return {
    #         "status_code": auth_response.status_code,
    #         "status": False,
    #         "message": "Failed to start session",
    #         "data": payment_failure_object,
    #     }
    # response = start_or_stop_session_with_driivz_api_gateway(
    #     connector.connector_id,
    #     dms_ticket,
    #     mfg_user,
    # )
    # if response.status_code == 403:
    #     auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket(
    #         generate_token=True
    #     )
        # if auth_response is not None and auth_response.status_code != 200:
        #     print(
        #         "Failed to start driivz session for user -> "
        #         f"{mfg_user.id} as driivz API gateway AUTH api failed"
        #     )
        #     return {
        #         "status_code": auth_response.status_code,
        #         "status": False,
        #         "message": "Failed to start session",
        #         "data": payment_failure_object,
        #     }
        # response = start_or_stop_session_with_driivz_api_gateway(
        #     connector.connector_id,
        #     dms_ticket,
        #     mfg_user
        # )
    # if response.status_code != 200:
    #     response_data = json.loads(response.content)
    #     return {
    #         "status_code": response.status_code,
    #         "status": False,
    #         "message": (
    #             response_data["errors"][0]["message"]
    #             if "errors" in response_data and len(response_data["errors"]) else
    #             "Failed to start session, try after some time."
    #         ),
    #     }
    return {
        "status_code": response.status_code,
        "status": True,
        "message": "Successfully started session",
        "data": {
            **{
                "account_number": get_driivz_account_number_for_user(
                    mfg_user
                ),
                "back_office": DRIIVZ,
                "dynamic_api_call_time": int(
                    filter_function_for_base_configuration(
                        "dynamic_api_call_time",
                        30000
                    )
                ),
                "session_api_call_time": int(
                    filter_function_for_base_configuration(
                        "session_api_call_time",
                        15000
                    )
                ),
                "offers": get_user_offers(mfg_user, station)
            },
            **payment_failure_object,
        },
    }


def stop_driivz_session_api_call(mfg_user, session_id):
    """this function stops driivz session"""

    charging_session = ChargingSession.objects.filter(
        user_id=mfg_user, emp_session_id=session_id
    )
    success_response = {
        "status_code": 200,
        "status": True,
        "message": "Successfully stopped session",
        "data": {
            "emp_session_id": charging_session.first().emp_session_id,
            "account_number": get_driivz_account_number_for_user(mfg_user),
            "back_office": DRIIVZ,
        },
    }
    auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket()
    if auth_response is not None and auth_response.status_code != 200:
        print(
            "Failed to stop driivz session for user -> "
            f"{mfg_user.id} as driivz auth api failed"
        )
        return {
            "status_code": auth_response.status_code,
            "status": False,
            "message": "Failed to stop session"
        }
    session_data_response = get_session_details(
        charging_session.first().emp_session_id
    )
    if session_data_response.status_code != 200:
        return {
            "status_code": status.HTTP_400_BAD_REQUEST,
            "status": False,
            "message": "Failed to get session details",
        }
    content = json.loads(session_data_response.content)["data"][0]
    if (
        "transactionStatus" in content
        and content["transactionStatus"] in DRIIVZ_CHECK_FORCE_STOP_CONDITIONS
        and str(content["accountNumber"])
        == get_driivz_account_number_for_user(mfg_user)
    ):
        if charging_session.first().session_status == RUNNING:
            charging_session.update(
                session_status="closed",
                end_time=timezone.localtime(timezone.now()),
            )
        return success_response
    response = start_or_stop_session_with_driivz_api_gateway(
        charging_session.first().connector_id.connector_id,
        dms_ticket,
        mfg_user,
        action="stop"
    )
    if response.status_code == 403:
        auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket(
            generate_token=True
        )
        if auth_response is not None and auth_response.status_code != 200:
            print(
                "Failed to stop driivz session for user -> "
                f"{mfg_user.id} as driivz API gateway AUTH api failed"
            )
            return {
                "status_code": auth_response.status_code,
                "status": False,
                "message": "Failed to stop session",
            }
        response = start_or_stop_session_with_driivz_api_gateway(
            charging_session.first().connector_id.connector_id,
            dms_ticket,
            mfg_user,
            action="stop"
        )
    if response.status_code == 200:
        print(
            f"successfully stopped charging session where \
                session id = {session_id} , user = {mfg_user.id} "
        )
        charging_session.update(
            session_status="closed",
            end_time=timezone.localtime(timezone.now()),
        )
        return success_response
    print(
        f"Failed to stop charging session where \
                session id = {session_id} , user = {mfg_user.id} "
    )
    return {
        "status_code": response.status_code,
        "status": False,
        "message": "Failed to stop session.",
    }




def stop_session_api_call(mfg_user, session_id):
    """this function stops driivz session"""

    charging_session = OCPISessions.objects.filter(
        user_id=mfg_user, emp_session_id=session_id
    )
    success_response = {
        "status_code": 200,
        "status": True,
        "message": "Successfully stopped session",
        "data": {
            "emp_session_id": charging_session.first().emp_session_id,
            "account_number": get_driivz_account_number_for_user(mfg_user),
            "back_office": DRIIVZ,
        },
    }
    auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket()
    if auth_response is not None and auth_response.status_code != 200:
        print(
            "Failed to stop driivz session for user -> "
            f"{mfg_user.id} as driivz auth api failed"
        )
        return {
            "status_code": auth_response.status_code,
            "status": False,
            "message": "Failed to stop session"
        }
    session_data_response = get_session_details(
        charging_session.first().emp_session_id
    )
    if session_data_response.status_code != 200:
        return {
            "status_code": status.HTTP_400_BAD_REQUEST,
            "status": False,
            "message": "Failed to get session details",
        }
    content = json.loads(session_data_response.content)["data"][0]
    if (
        "transactionStatus" in content
        and content["transactionStatus"] in DRIIVZ_CHECK_FORCE_STOP_CONDITIONS
        and str(content["accountNumber"])
        == get_driivz_account_number_for_user(mfg_user)
    ):
        if charging_session.first().session_status == RUNNING:
            charging_session.update(
                session_status="closed",
                end_time=timezone.localtime(timezone.now()),
            )
        return success_response
    response = start_or_stop_session_with_driivz_api_gateway(
        charging_session.first().connector_id.connector_id,
        dms_ticket,
        mfg_user,
        action="stop"
    )
    if response.status_code == 403:
        auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket(
            generate_token=True
        )
        if auth_response is not None and auth_response.status_code != 200:
            print(
                "Failed to stop driivz session for user -> "
                f"{mfg_user.id} as driivz API gateway AUTH api failed"
            )
            return {
                "status_code": auth_response.status_code,
                "status": False,
                "message": "Failed to stop session",
            }
        response = start_or_stop_session_with_driivz_api_gateway(
            charging_session.first().connector_id.connector_id,
            dms_ticket,
            mfg_user,
            action="stop"
        )
    if response.status_code == 200:
        print(
            f"successfully stopped charging session where \
                session id = {session_id} , user = {mfg_user.id} "
        )
        charging_session.update(
            session_status="closed",
            end_time=timezone.localtime(timezone.now()),
        )
        return success_response
    print(
        f"Failed to stop charging session where \
                session id = {session_id} , user = {mfg_user.id} "
    )
    return {
        "status_code": response.status_code,
        "status": False,
        "message": "Failed to stop session.",
    }




def drrivz_start_session_function(args):
    """this function initializes the user sessions for DRIIVZ"""
    (
        back_office,
        start_session_request,
        station,
        _,
        connector,
        _,
        payment_id,
        _,
        _,
        payment_failure_object,
        _
    ) = args
    # if start_session_request.user.user_profile.driivz_account_number is None:
    #     drrivz_auth_response = session_register_mfg_user_with_drrivz(
    #         start_session_request.user
    #     )
    #     if drrivz_auth_response is not None:
    #         print(
    #             f"Failed to register user -> {start_session_request.user.id} with DRIIVZ"
    #         )
    #         return {
    #             "status_code": status.HTTP_400_BAD_REQUEST,
    #             "status": False,
    #             "message": "User registration with third party service failed",
    #             "data": payment_failure_object,
    #         }
    return update_wallet_and_get_promotions_data(
        back_office,
        start_session_request.user,
        station,
        connector,
        payment_id,
        payment_failure_object,
    )


def drrivz_stop_session_function(args):
    """this function stops sessions for DRIIVZ"""
    (stop_session_request, _, session_id) = args
    if stop_session_request.user.user_profile.driivz_account_number is None:
        print(
            f"Failed to get driivz_account_number for user ->\
                  {stop_session_request.user.id} "
        )
        return {
            "status_code": status.HTTP_403_FORBIDDEN,
            "status": False,
            "message": "Failed to get third party account details.",
        }
    return stop_driivz_session_api_call(
        stop_session_request.user,
        session_id
    )


def drrivz_force_stop_session_function(args):
    """this function forcely stops sessions for DRIIVZ"""

    force_stop_session = args[0]
    response_data = {}
    response_data["status_code"] = "Stopped"
    response_data["emp_session_id"] = force_stop_session.data["emp_session_id"]
    response_data["account_number"] = (
        get_driivz_account_number_for_user(force_stop_session.user),
    )
    return {
        "status_code": status.HTTP_200_OK,
        "status": True,
        "message": SESSION_CLOSED,
        "data": response_data,
    }


def get_kwh_from_charging_data(session):
    """this function returns kwh from charging data"""
    charging_data = string_to_array_converter(
        session.charging_data
    )[0]
    if (
        # session.back_office == DRIIVZ
        # and 
        TOTAL_ENERGY in charging_data
    ):
        return Decimal(
            str(charging_data[TOTAL_ENERGY])
        )
    return 0


def enabled_3ds_based_on_kwh_cosumptions(
    user_id,
    days,
    last_completed_cycle,
    config_last_updated_on_date
):
    """enables 3ds based on kwh consumptions"""
    # sessions = ChargingSession.objects.filter(
    #     user_id_id=user_id,
    #     session_status__in=["completed", "closed"],
    #     start_time__gte=(
    #         timezone.localtime(timezone.now()) -
    #         timedelta(
    #             days=int(days)
    #         )
    #     )
    # )
    ocpi_sessions = OCPISessions.objects.filter(
        user_id_id=user_id,
        session_status__in=["completed", "closed"],
        start_datetime__gte=(
            timezone.now() -
            timedelta(
                days=int(days)
            )
        )
    )
    if config_last_updated_on_date:
        ocpi_sessions = ocpi_sessions.filter(
            start_datetime__gte=timezone.localtime(
                datetime.strptime(
                    config_last_updated_on_date, '%d/%m/%Y %H:%M'
                ).replace(tzinfo=pytz.UTC)
            )
        )
    if last_completed_cycle:
        ocpi_sessions = ocpi_sessions.filter(
            start_datetime__gte=timezone.localtime(last_completed_cycle.updated_date)
        )
    return sum(
        get_kwh_from_charging_data(ocpi_session)
        for ocpi_session in ocpi_sessions if ocpi_session.charging_data
    )


def enabled_3ds_based_on_number_of_transactions(
    user_id,
    days,
    last_completed_cycle,
    config_last_updated_on_date
):
    """enables 3ds based on number of transactions"""
    sessions = ChargingSession.objects.filter(
        user_id_id=user_id,
        session_status__in=["completed", "closed"],
        start_time__gte=(
            timezone.localtime(timezone.now()) -
            timedelta(
                days=int(days)
            )
        )
    )
    ocpi_sessions = OCPISessions.objects.filter(
        user_id_id=user_id,
        session_status__in=["completed", "closed"],
        start_datetime__gte=(
            timezone.now() -
            timedelta(
                days=int(days)
            )
        )
    )
    if config_last_updated_on_date:
        sessions = sessions.filter(
            start_time__gte=timezone.localtime(
                datetime.strptime(
                    config_last_updated_on_date, '%d/%m/%Y %H:%M'
                ).replace(tzinfo=pytz.UTC)
            )
        )
        ocpi_sessions = ocpi_sessions.filter(
            start_datetime__gte=timezone.localtime(
                datetime.strptime(
                    config_last_updated_on_date, '%d/%m/%Y %H:%M'
                ).replace(tzinfo=pytz.UTC)
            )
        )
    if last_completed_cycle:
        sessions = sessions.filter(
            start_time__gte=timezone.localtime(last_completed_cycle.updated_date)
        )
        ocpi_sessions = ocpi_sessions.filter(
            start_datetime__gte=timezone.localtime(last_completed_cycle.updated_date)
        )
    return sessions.count() + ocpi_sessions.count()


def handle_kwh_within_x_days(user, last_completed_cycle, three_ds_config):
    account_creation_days = (timezone.localtime(timezone.now()).timestamp() - user.timestamp.timestamp()) / 86400
    if (
        three_ds_config.get('kwh_consumed_within__condition_checkbox') == ON_CONST and
        account_creation_days <= float(three_ds_config.get("kwh_consumed_within__x_days__number_of_days", 0))
    ):
        total_kwh = enabled_3ds_based_on_kwh_cosumptions(
            user.id,
            three_ds_config.get("kwh_consumed_within__x_days__number_of_days", 0),
            last_completed_cycle,
            config_last_updated_on_date=three_ds_config.get("kwh_consumed_within__last_updated_on_date")
        )
        trigger_value = float(three_ds_config.get("kwh_consumed_within__trigger_value", 0))
        n = float(three_ds_config.get("kwh_consumed_within__x_days__number_of_next_transactions", 0))
        print(f"[DEBUG] kwh_within_x_days: total_kwh={total_kwh}, trigger_value={trigger_value}, n={n}")
        if trigger_value == 0:
            if total_kwh <= n and n > 0:
                return {
                    "n": n,
                    "reason_for_3ds": "X kWh within X days of account creation. Trigger 3DS for next X Transactions",
                    "reason_for_3ds_kwh": total_kwh,
                    "reason_for_3ds_days": three_ds_config.get("kwh_consumed_within__x_days__number_of_days", 0),
                    "reason_for_3ds_transactions": n,
                    "configuration_set_by_admin_for_3ds": f"{trigger_value} kWh within {three_ds_config.get('kwh_consumed_within__x_days__number_of_days', 0)} days of account creation. Trigger 3DS for next {n} Transactions",
                    "configuration_set_by_admin_for_3ds_kwh": trigger_value,
                    "configuration_set_by_admin_for_3ds_days": three_ds_config.get("kwh_consumed_within__x_days__number_of_days", 0),
                    "configuration_set_by_admin_for_3ds_transactions": n,
                }
        else:
            if total_kwh >= trigger_value and n > 0:
                return {
                    "n": n,
                    "reason_for_3ds": "X kWh within X days of account creation. Trigger 3DS for next X Transactions",
                    "reason_for_3ds_kwh": total_kwh,
                    "reason_for_3ds_days": three_ds_config.get("kwh_consumed_within__x_days__number_of_days", 0),
                    "reason_for_3ds_transactions": n,
                    "configuration_set_by_admin_for_3ds": f"{trigger_value} kWh within {three_ds_config.get('kwh_consumed_within__x_days__number_of_days', 0)} days of account creation. Trigger 3DS for next {n} Transactions",
                    "configuration_set_by_admin_for_3ds_kwh": trigger_value,
                    "configuration_set_by_admin_for_3ds_days": three_ds_config.get("kwh_consumed_within__x_days__number_of_days", 0),
                    "configuration_set_by_admin_for_3ds_transactions": n,
                }
        print(f"[DEBUG] kwh_within_x_days: Not triggering 3DS for current session (n={n}, total_kwh={total_kwh}, trigger_value={trigger_value})")
    return None

def handle_txn_within_x_days(user, last_completed_cycle, three_ds_config):
    account_creation_days = (timezone.localtime(timezone.now()).timestamp() - user.timestamp.timestamp()) / 86400
    if (
        three_ds_config.get('total_transactions_within__condition_checkbox') == ON_CONST and
        account_creation_days <= float(three_ds_config.get("total_transactions_within__x_days__number_of_days", 0))
    ):
        num_tx = enabled_3ds_based_on_number_of_transactions(
            user.id,
            three_ds_config.get("total_transactions_within__x_days__number_of_days", 0),
            last_completed_cycle,
            config_last_updated_on_date=three_ds_config.get("total_transactions_within__last_updated_on_date")
        )
        trigger_value = float(three_ds_config.get("total_transactions_within__trigger_value", 0))
        n = float(three_ds_config.get("total_transactions_within__x_days__number_of_next_transactions", 0))
        print(f"[DEBUG] txn_within_x_days: num_tx={num_tx}, trigger_value={trigger_value}, n={n}")
        if trigger_value == 0:
            if num_tx <= n and n > 0:
                return {
                    "n": n,
                    "reason_for_3ds": "X transaction within X days of account creation. Trigger 3DS for next X Transactions",
                    "reason_for_3ds_kwh": num_tx,
                    "reason_for_3ds_days": three_ds_config.get("total_transactions_within__x_days__number_of_days", 0),
                    "reason_for_3ds_transactions": n,
                    "configuration_set_by_admin_for_3ds": f"{trigger_value} transaction within {three_ds_config.get('total_transactions_within__x_days__number_of_days', 0)} days of account creation. Trigger 3DS for next {n} Transactions",
                    "configuration_set_by_admin_for_3ds_kwh": trigger_value,
                    "configuration_set_by_admin_for_3ds_days": three_ds_config.get("total_transactions_within__x_days__number_of_days", 0),
                    "configuration_set_by_admin_for_3ds_transactions": n,
                }
        else:
            if num_tx == trigger_value and n > 0:
                return {
                    "n": n,
                    "reason_for_3ds": "X transaction within X days of account creation. Trigger 3DS for next X Transactions",
                    "reason_for_3ds_kwh": num_tx,
                    "reason_for_3ds_days": three_ds_config.get("total_transactions_within__x_days__number_of_days", 0),
                    "reason_for_3ds_transactions": n,
                    "configuration_set_by_admin_for_3ds": f"{trigger_value} transaction within {three_ds_config.get('total_transactions_within__x_days__number_of_days', 0)} days of account creation. Trigger 3DS for next {n} Transactions",
                    "configuration_set_by_admin_for_3ds_kwh": trigger_value,
                    "configuration_set_by_admin_for_3ds_days": three_ds_config.get("total_transactions_within__x_days__number_of_days", 0),
                    "configuration_set_by_admin_for_3ds_transactions": n,
                }
        print(f"[DEBUG] txn_within_x_days: Not triggering 3DS for current session (n={n}, num_tx={num_tx}, trigger_value={trigger_value})")
    return None

def handle_txn_rolling(user, last_completed_cycle, three_ds_config):
    if three_ds_config.get('total_transactions__condition_checkbox') == ON_CONST:
        num_tx = enabled_3ds_based_on_number_of_transactions(
            user.id,
            three_ds_config.get("total_transactions__in_x_days__number_of_days", 0),
            last_completed_cycle,
            config_last_updated_on_date=three_ds_config.get("kwh_consumed__last_updated_on_date")
        )
        trigger_value = float(three_ds_config.get("total_transactions__trigger_value", 0))
        n = float(three_ds_config.get("total_transactions__in_x_days__number_of_next_transactions", 0))
        print(f"[DEBUG] txn_rolling: num_tx={num_tx}, trigger_value={trigger_value}, n={n}")
        if trigger_value == 0:
            if num_tx <= n and n > 0:
                return {
                    "n": n,
                    "reason_for_3ds": "X transaction in X days. Trigger 3DS for next X Transactions",
                    "reason_for_3ds_kwh": num_tx,
                    "reason_for_3ds_days": three_ds_config.get("total_transactions__in_x_days__number_of_days", 0),
                    "reason_for_3ds_transactions": n,
                    "configuration_set_by_admin_for_3ds": f"{trigger_value} transaction in {three_ds_config.get('total_transactions__in_x_days__number_of_days', 0)} days. Trigger 3DS for next {n} Transactions",
                    "configuration_set_by_admin_for_3ds_kwh": trigger_value,
                    "configuration_set_by_admin_for_3ds_days": three_ds_config.get("total_transactions__in_x_days__number_of_days", 0),
                    "configuration_set_by_admin_for_3ds_transactions": n,
                }
        else:
            if num_tx == trigger_value and n > 0:
                return {
                    "n": n,
                    "reason_for_3ds": "X transaction in X days. Trigger 3DS for next X Transactions",
                    "reason_for_3ds_kwh": num_tx,
                    "reason_for_3ds_days": three_ds_config.get("total_transactions__in_x_days__number_of_days", 0),
                    "reason_for_3ds_transactions": n,
                    "configuration_set_by_admin_for_3ds": f"{trigger_value} transaction in {three_ds_config.get('total_transactions__in_x_days__number_of_days', 0)} days. Trigger 3DS for next {n} Transactions",
                    "configuration_set_by_admin_for_3ds_kwh": trigger_value,
                    "configuration_set_by_admin_for_3ds_days": three_ds_config.get("total_transactions__in_x_days__number_of_days", 0),
                    "configuration_set_by_admin_for_3ds_transactions": n,
                }
        print(f"[DEBUG] txn_rolling: Not triggering 3DS for current session (n={n}, num_tx={num_tx}, trigger_value={trigger_value})")
    return None

def handle_kwh_rolling(user, last_completed_cycle, three_ds_config):
    if three_ds_config.get('kwh_consumed__condition_checkbox') == ON_CONST:
        total_kwh = enabled_3ds_based_on_kwh_cosumptions(
            user.id,
            three_ds_config.get("kwh_consumed__in_x_days__number_of_days", 0),
            last_completed_cycle,
            config_last_updated_on_date=three_ds_config.get("total_transactions__last_updated_on_date")
        )
        trigger_value = float(three_ds_config.get("kwh_consumed__trigger_value", 0))
        n = float(three_ds_config.get("kwh_consumed__in_x_days__number_of_next_transactions", 0))
        print(f"[DEBUG] kwh_rolling: total_kwh={total_kwh}, trigger_value={trigger_value}, n={n}")
        if trigger_value == 0:
            if total_kwh <= n and n > 0:
                return {
                    "n": n,
                    "reason_for_3ds": "X kWh consumed in X days. Trigger 3DS for next X Transactions",
                    "reason_for_3ds_kwh": total_kwh,
                    "reason_for_3ds_days": three_ds_config.get("kwh_consumed__in_x_days__number_of_days", 0),
                    "reason_for_3ds_transactions": n,
                    "configuration_set_by_admin_for_3ds": f"{trigger_value} kWh consumed in {three_ds_config.get('kwh_consumed__in_x_days__number_of_days', 0)} days. Trigger 3DS for next {n} Transactions",
                    "configuration_set_by_admin_for_3ds_kwh": trigger_value,
                    "configuration_set_by_admin_for_3ds_days": three_ds_config.get("kwh_consumed__in_x_days__number_of_days", 0),
                    "configuration_set_by_admin_for_3ds_transactions": n,
                }
        else:
            if total_kwh >= trigger_value and n > 0:
                return {
                    "n": n,
                    "reason_for_3ds": "X kWh consumed in X days. Trigger 3DS for next X Transactions",
                    "reason_for_3ds_kwh": total_kwh,
                    "reason_for_3ds_days": three_ds_config.get("kwh_consumed__in_x_days__number_of_days", 0),
                    "reason_for_3ds_transactions": n,
                    "configuration_set_by_admin_for_3ds": f"{trigger_value} kWh consumed in {three_ds_config.get('kwh_consumed__in_x_days__number_of_days', 0)} days. Trigger 3DS for next {n} Transactions",
                    "configuration_set_by_admin_for_3ds_kwh": trigger_value,
                    "configuration_set_by_admin_for_3ds_days": three_ds_config.get("kwh_consumed__in_x_days__number_of_days", 0),
                    "configuration_set_by_admin_for_3ds_transactions": n,
                }
        print(f"[DEBUG] kwh_rolling: Not triggering 3DS for current session (n={n}, total_kwh={total_kwh}, trigger_value={trigger_value})")
    return None

def handle_no_3ds(user, config, three_ds_status, session_id):
    print(f"[DEBUG] H 1 No 3DS trigger scenario for user: {user.id}")
    return False

def check_3ds_trigger_for_user(user, three_ds_status=True, session_id=None, is_ocpi = True):
    print("[DEBUG] Entered 3Ds trigger function for user:", user.id)

    if user.user_profile.user_specific_3ds_set_by_admin:
        user_specific_3ds_configurations = json.loads(user.user_profile.user_specific_3ds_configurations)
        print(f"[DEBUG] User-specific 3DS config for user {user.id}: {user_specific_3ds_configurations}")
        if (
            user_specific_3ds_configurations.get("status") == "Active" and
            user_specific_3ds_configurations.get("triggered_3ds_for_all_transactions")
        ):
            print(f"[DEBUG] User-specific 3DS is active and triggered for all transactions for user {user.id}")
            if is_ocpi:
                if ThreeDSCheckLogs.objects.filter(ocpi_session_id=session_id).first() is None:
                    print(f"[DEBUG] Creating user-specific 3DS trigger log for session: {session_id}")
                    ThreeDSCheckLogs.objects.create(
                        three_ds_trigger_log_id=ThreeDSTriggerLogs.objects.create(
                            user_id = user,
                            reason_for_3ds = 'Trigger 3DS for all transactions (User Specific)',
                            reason_for_3ds_kwh = 'NA',
                            reason_for_3ds_days = 'NA',
                            reason_for_3ds_transactions = 'NA',
                            configuration_set_by_admin_for_3ds = 'Trigger 3DS for all transactions (User Specific)',
                            configuration_set_by_admin_for_3ds_kwh = 'NA',
                            configuration_set_by_admin_for_3ds_days = 'NA',
                            configuration_set_by_admin_for_3ds_transactions = 'NA',
                            remaining_3ds_check_transaction = 0,
                            status = "Completed",
                            created_date = timezone.localtime(timezone.now()),
                            updated_date = timezone.localtime(timezone.now()),
                        ),
                        ocpi_session_id=session_id,
                        status="Successful" if three_ds_status else "Failed",
                        created_date=timezone.localtime(timezone.now()),
                    )
            else:
                if ThreeDSCheckLogs.objects.filter(session_id=session_id).first() is None:
                    print(f"[DEBUG] Creating user-specific 3DS trigger log for session: {session_id}")
                    ThreeDSCheckLogs.objects.create(
                        three_ds_trigger_log_id=ThreeDSTriggerLogs.objects.create(
                            user_id = user,
                            reason_for_3ds = 'Trigger 3DS for all transactions (User Specific)',
                            reason_for_3ds_kwh = 'NA',
                            reason_for_3ds_days = 'NA',
                            reason_for_3ds_transactions = 'NA',
                            configuration_set_by_admin_for_3ds = 'Trigger 3DS for all transactions (User Specific)',
                            configuration_set_by_admin_for_3ds_kwh = 'NA',
                            configuration_set_by_admin_for_3ds_days = 'NA',
                            configuration_set_by_admin_for_3ds_transactions = 'NA',
                            remaining_3ds_check_transaction = 0,
                            status = "Completed",
                            created_date = timezone.localtime(timezone.now()),
                            updated_date = timezone.localtime(timezone.now()),
                        ),
                        session_id=session_id,
                        status="Successful" if three_ds_status else "Failed",
                        created_date=timezone.localtime(timezone.now()),
                    )
            return None

    user_current_3ds_cycle = ThreeDSTriggerLogs.objects.filter(
        user_id=user,
        status__in=["Triggered", "Running"]
    )
    last_completed_cycle = ThreeDSTriggerLogs.objects.filter(
        user_id=user,
        status="Completed"
    ).last()
    print(f"[DEBUG] Current 3DS cycles for user {user.id}: {user_current_3ds_cycle}")
    print(f"[DEBUG] Last completed 3DS cycle for user {user.id}: {last_completed_cycle}")
    if user_current_3ds_cycle.last():
        if is_ocpi:
            print(f"[DEBUG] Found active 3DS cycle for user {user.id}, decrementing remaining_3ds_check_transaction")
            if not ThreeDSCheckLogs.objects.filter(ocpi_session_id=session_id, three_ds_trigger_log_id=user_current_3ds_cycle.last()).exists():
                ThreeDSCheckLogs.objects.create(
                    three_ds_trigger_log_id=user_current_3ds_cycle.last(),
                    ocpi_session_id=session_id,
                    status="Successful" if three_ds_status else "Failed",
                    created_date=timezone.localtime(timezone.now())
                )
            else:
                print(f"[DEBUG] Skipping duplicate ThreeDSCheckLogs for session_id={session_id} and cycle={user_current_3ds_cycle.last().id}")
        else:
            print(f"[DEBUG] Found active 3DS cycle for user {user.id}, decrementing remaining_3ds_check_transaction")
            if not ThreeDSCheckLogs.objects.filter(session_id=session_id, three_ds_trigger_log_id=user_current_3ds_cycle.last()).exists():
                ThreeDSCheckLogs.objects.create(
                    three_ds_trigger_log_id=user_current_3ds_cycle.last(),
                    session_id=session_id,
                    status="Successful" if three_ds_status else "Failed",
                    created_date=timezone.localtime(timezone.now())
                )
            else:
                print(f"[DEBUG] Skipping duplicate ThreeDSCheckLogs for session_id={session_id} and cycle={user_current_3ds_cycle.last().id}")
        if three_ds_status:
            if user_current_3ds_cycle.last().remaining_3ds_check_transaction - 1 <= 0:
                print(f"[DEBUG] Completing 3DS cycle for user {user.id}")
                user_current_3ds_cycle.update(
                    status="Completed",
                    remaining_3ds_check_transaction=0,
                    updated_date = timezone.localtime(timezone.now())
                )
                Profile.objects.filter(
                    user_id=user
                ).update(
                    is_3ds_check_active=False
                )
            else:
                print(f"[DEBUG] Decremented remaining_3ds_check_transaction for user {user.id} to {user_current_3ds_cycle.last().remaining_3ds_check_transaction - 1}")
                user_current_3ds_cycle.update(
                    status="Running",
                    remaining_3ds_check_transaction=(
                        user_current_3ds_cycle.last().remaining_3ds_check_transaction - 1
                    )
                )
        return None

    three_ds_config_db = BaseConfigurations.objects.filter(
        base_configuration_key="3ds_configurations"
    ).first()
    if not three_ds_config_db or not three_ds_config_db.base_configuration_value:
        print(f"[DEBUG] No 3DS config found for user: {user.id}")
        return False
    three_ds_config = json.loads(three_ds_config_db.base_configuration_value)

    if three_ds_config.get('trigger_three_ds_for_all_transaction_checkbox') == ON_CONST:
        print(f"[DEBUG] Global-all 3DS is active for user {user.id}")
        ThreeDSCheckLogs.objects.create(
            three_ds_trigger_log_id=ThreeDSTriggerLogs.objects.create(
                user_id = user,
                reason_for_3ds = 'Trigger 3DS for all transactions',
                reason_for_3ds_kwh = 'NA',
                reason_for_3ds_days = 'NA',
                reason_for_3ds_transactions = 'NA',
                configuration_set_by_admin_for_3ds = 'Trigger 3DS for all transactions',
                configuration_set_by_admin_for_3ds_kwh = 'NA',
                configuration_set_by_admin_for_3ds_days = 'NA',
                configuration_set_by_admin_for_3ds_transactions = 'NA',
                remaining_3ds_check_transaction = 0,
                status = "Completed",
                created_date = timezone.localtime(timezone.now()),
                updated_date = timezone.localtime(timezone.now())
            ),
            ocpi_session_id=session_id,
            status="Successful" if three_ds_status else "Failed",
            created_date=timezone.localtime(timezone.now()),
        )
        return None

    scenarios = []
    kwh_within_x_days_result = handle_kwh_within_x_days(user, last_completed_cycle, three_ds_config)
    if kwh_within_x_days_result:
        scenarios.append(kwh_within_x_days_result)
    txn_within_x_days_result = handle_txn_within_x_days(user, last_completed_cycle, three_ds_config)
    if txn_within_x_days_result:
        scenarios.append(txn_within_x_days_result)
    kwh_rolling_result = handle_kwh_rolling(user, last_completed_cycle, three_ds_config)
    if kwh_rolling_result:
        scenarios.append(kwh_rolling_result)
    txn_rolling_result = handle_txn_rolling(user, last_completed_cycle, three_ds_config)
    if txn_rolling_result:
        scenarios.append(txn_rolling_result)

    if scenarios:
        best = max(scenarios, key=lambda x: x["n"])
        print(f"[DEBUG] Scenario selected for user {user.id}: {best}")
        if best["n"] > 0:
            print(f"[DEBUG] Creating new 3DS cycle for user {user.id} with n={best['n']}")
            Profile.objects.filter(user_id=user.id).update(
                is_3ds_check_active=True
            )
            ThreeDSTriggerLogs.objects.create(
                user_id=user,
                reason_for_3ds=best["reason_for_3ds"],
                reason_for_3ds_kwh=best["reason_for_3ds_kwh"],
                reason_for_3ds_days=best["reason_for_3ds_days"],
                reason_for_3ds_transactions=best["reason_for_3ds_transactions"],
                configuration_set_by_admin_for_3ds=best["configuration_set_by_admin_for_3ds"],
                configuration_set_by_admin_for_3ds_kwh=best["configuration_set_by_admin_for_3ds_kwh"],
                configuration_set_by_admin_for_3ds_days=best["configuration_set_by_admin_for_3ds_days"],
                configuration_set_by_admin_for_3ds_transactions=best["configuration_set_by_admin_for_3ds_transactions"],
                remaining_3ds_check_transaction=best["n"],
                status="Triggered",
                created_date=timezone.localtime(timezone.now())
            )
    else:
        print(f"[DEBUG] No 3DS scenario triggered for user {user.id}")
    return None


def handle_user_specific_3ds(user, config, three_ds_status, session_id):
    print(f"[DEBUG] B 1 Entered handle_user_specific_3ds for user: {user.id}")
    try:
        user_specific_3ds_config = json.loads(user.user_profile.user_specific_3ds_configurations)
    except Exception as e:
        print(f"[DEBUG] B 2 Failed to parse user-specific 3DS config: {e}")
        return None
    if (
        user_specific_3ds_config.get("status") == "Active" and
        user_specific_3ds_config.get("triggered_3ds_for_all_transactions")
    ):
        print(f"[DEBUG] B 3 User-specific 3DS is active and triggered for all transactions.")
        if ThreeDSCheckLogs.objects.filter(session_id=session_id).first() is None:
            print(f"[DEBUG] B 4 Creating user-specific 3DS trigger log for session: {session_id}")
            trigger_log = ThreeDSTriggerLogs.objects.create(
                user_id=user,
                reason_for_3ds='Trigger 3DS for all transactions (User Specific)',
                reason_for_3ds_kwh='NA',
                reason_for_3ds_days='NA',
                reason_for_3ds_transactions='NA',
                configuration_set_by_admin_for_3ds='Trigger 3DS for all transactions (User Specific)',
                configuration_set_by_admin_for_3ds_kwh='NA',
                configuration_set_by_admin_for_3ds_days='NA',
                configuration_set_by_admin_for_3ds_transactions='NA',
                remaining_3ds_check_transaction=0,
                status="Completed",
                created_date=timezone.localtime(timezone.now()),
                updated_date=timezone.localtime(timezone.now()),
            )
            ThreeDSCheckLogs.objects.create(
                three_ds_trigger_log_id=trigger_log,
                session_id=session_id,
                status="Successful" if three_ds_status else "Failed",
                created_date=timezone.localtime(timezone.now())
            )
    return None

def handle_global_all_3ds(user, config, three_ds_status, session_id):
    print(f"[DEBUG] C 1 Entered handle_global_all_3ds for user: {user.id}")
    trigger_log = ThreeDSTriggerLogs.objects.create(
        user_id=user,
        reason_for_3ds='Trigger 3DS for all transactions',
        reason_for_3ds_kwh='NA',
        reason_for_3ds_days='NA',
        reason_for_3ds_transactions='NA',
        configuration_set_by_admin_for_3ds='Trigger 3DS for all transactions',
        configuration_set_by_admin_for_3ds_kwh='NA',
        configuration_set_by_admin_for_3ds_days='NA',
        configuration_set_by_admin_for_3ds_transactions='NA',
        remaining_3ds_check_transaction=0,
        status="Completed",
        created_date=timezone.localtime(timezone.now()),
        updated_date=timezone.localtime(timezone.now())
    )
    print(f"[DEBUG] C 2 Created global all 3DS trigger log for session: {session_id}")
    ThreeDSCheckLogs.objects.create(
        three_ds_trigger_log_id=trigger_log,
        session_id=session_id,
        status="Successful" if three_ds_status else "Failed",
        created_date=timezone.localtime(timezone.now())
    )
    return None
