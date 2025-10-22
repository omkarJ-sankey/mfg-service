"""charging session helper functions"""
# Date - 31/01/2022

# File details-
#   Author          - Manish Pawar
#   Description     - This file contains helper functions
#                       for charging session APIs.
#   Name            - chrging session helper functions
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 20/07/2025


# These are all the imports that we are exporting from
# different module's from project or library.
import json
import uuid
import requests
# pylint:disable=import-error
from decouple import config
import traceback
# from square.client import Client
from rest_framework import status
from rest_framework.response import Response
from sharedServices.gift_card_common_functions import (
    get_user_gift_card_details,
)
from sharedServices.model_files.charging_session_models import ChargingSession
from sharedServices.model_files.app_user_models import Profile
from sharedServices.model_files.config_models import BaseConfigurations

from sharedServices.common import (
    array_to_string_converter,
    string_to_array_converter,
)
from sharedServices.common_session_functions import (
    create_payment_with_auto_deduct,
    return_payment_error_message,
    add_failed_payment_amount_in_user_account,
    get_user_total_due_amount,
    get_pre_auth_expiry_time,
    send_charging_payment_mail,
    send_old_charging_payment_mail,
    driivz_get_session_details,

)
from sharedServices.common_session_payment_functions import (
    save_transaction_data_and_send_mail
    # combined_payment_function,
    # partial_payment_function,
    # update_and_complete_payment,
)
from sharedServices.payments_helper_function import make_request
from sharedServices.constants import POST_REQUEST
from sharedServices.error_codes import PAYMENT_ERROR_CODES
from sharedServices.constants import (
    YES,
    ERROR_CONST,
    CODE_CONST,
    COMMON_ERRORS,
)

from .swarco_apis import (
    swarco_start_session_function,
    swarco_stop_session_function,
    swarco_force_stop_session_function,
)
from .driivz_apis import (
    drrivz_start_session_function,
    drrivz_stop_session_function,
    drrivz_force_stop_session_function,
)
from .app_level_constants import (
    SWARCO,
    DRIIVZ,
    WALLET_TRANSACTIONS,
    # NON_WALLET_TRANSACTIONS,
    CHARGING_SESSION,
    # PARTIAL,
    COMBINED,
    NON_WALLET,
)

from sharedServices.model_files.ocpi_sessions_models import OCPISessions

# client_session = Client(
#     access_token=config("DJANGO_PAYMENT_ACCESS_TOKEN"),
#     environment=config("DJANGO_PAYMENT_ENV"),
# )


# payments_api = client_session.payments


def handle_user_due_payment(
    handle_user_due_payment_request,
):
    """this function handles user due payment"""
    try:
        due_session_data = Profile.objects.filter(
            user=handle_user_due_payment_request.user
        ).first()
        if due_session_data is None:
            return {
                "status_code": status.HTTP_404_NOT_FOUND,
                "status": False,
                "message": "User due payment data not found.",
            }
        session_reference_id = handle_user_due_payment_request.data.get(
            "session_reference_id", None
        )
        user_due_session_amount = get_user_total_due_amount(
            handle_user_due_payment_request.user,
            session_reference_id=session_reference_id
        )
        if (
            user_due_session_amount is None
            or user_due_session_amount == 0
            or str(user_due_session_amount).isnumeric() is False
        ):
            return {
                "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                "status": False,
                "message": "No due amount for user.",
            }
        # used for app receipts due payments
        due_payment_session_data = []
        due_payment_session_ids = []
        for session_data in string_to_array_converter(
            due_session_data.due_amount_data
        ):
            if (
                session_reference_id is None and
                int(session_data["amount"]) > 0
                and session_data["amount_due_for"] == CHARGING_SESSION
            ) or session_reference_id and str(session_reference_id) == str(session_data["reference_id"]):
                due_payment_session_data.append(
                    {
                        "session_db_id": session_data["reference_id"],
                        "session_due_amount": int(session_data["amount"]),
                    }
                )
                due_payment_session_ids.append(session_data["reference_id"])
        payment_source_id = handle_user_due_payment_request.data.get(
            "payment_source_id", None
        )
        if payment_source_id is None:
            return {
                "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                "status": False,
                "message": (
                    "Failed to process payment, try after some time.",
                ),
            }
        is_ocpi = True
        charging_sessions = OCPISessions.objects.filter(
            id__in=due_payment_session_ids
        )
        if charging_sessions.first() is None:
            charging_sessions = ChargingSession.objects.filter(
                id__in=due_payment_session_ids
            )
            is_ocpi = False
            charging_session  = charging_sessions.first()
            #calling driivz api to handle missing keys in old sessions
            try:
                response = driivz_get_session_details(charging_session.emp_session_id)
                if response is None:
                    return None
            except requests.exceptions.ConnectionError as error:
                print("Failed to connect to drrivz due to->", error)
                return None
            if response.status_code == status.HTTP_200_OK:
                content = json.loads(response.content)["data"][0]
                # if content[TRANSACTION_STATUS] == BILLED:
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
                charging_session.charging_data=array_to_string_converter([session_data])
                charging_sessions.update(charging_data=array_to_string_converter([session_data]))
            charging_session = ChargingSession.objects.get(id=charging_session.id)
        if not charging_sessions.first():
            print(
                f"Due session data not found for session(s) -> \
                    {due_payment_session_ids} for user -> \
                        {handle_user_due_payment_request.user.id}"
            )
            return {
                "status_code": status.HTTP_404_NOT_FOUND,
                "status": False,
                "message": "Session data not found for due payment.",
            }
        print(
            f"Due payment process started for user -> \
                {handle_user_due_payment_request.user.id}"
        )

        payment_result = create_payment_with_auto_deduct(
            {
                "amount_money": {
                    "amount": user_due_session_amount,
                    "currency": config("DJANGO_APP_PAYMENT_CURRENCY"),
                },
                "source_id": payment_source_id,
            },
            handle_user_due_payment_request.user.customer_id,
            charging_sessions.first(),
            admin_screen_payment=False,
            is_ocpi = is_ocpi
        )
        if "errors" in payment_result or "payment" not in payment_result:
            print(
                f"Failed to process due payment for user -> \
                    {handle_user_due_payment_request.user.id} , \
                        payment_response -> {payment_result}"
            )
            return {
                "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                "status": False,
                "message": return_payment_error_message(
                    payment_result, "Failed to process payment."
                ),
            }
        print(
            f"Due amount payment successful for user -> \
                {handle_user_due_payment_request.user.id}"
        )
        for charging_session in due_payment_session_data:
            add_failed_payment_amount_in_user_account(
                handle_user_due_payment_request.user,
                charging_session["session_db_id"],
                payment_result["payment"]["id"],
                charging_session["session_due_amount"],
                is_ocpi = is_ocpi
            )
            transaction = save_transaction_data_and_send_mail(
                charging_sessions,
                payment_result,
                paid_amount=charging_session["session_due_amount"],
                send_success_email=False
            )
            if transaction is False:
                print(
                    f"Failed to save payment transaction details for \
                    sesion -> {charging_session['session_db_id']}"
                )
        for charging_session in charging_sessions:
            if is_ocpi:
                send_charging_payment_mail(charging_session.id,payment_result)
            else:
                send_old_charging_payment_mail(charging_session.id,payment_result)
        return None
    except COMMON_ERRORS as error:
        print(
            f"Failed to process due amount for user -> \
                {handle_user_due_payment_request.user.id} due to error -> \
                    {error}"
        )
        return {
            "status_code": status.HTTP_501_NOT_IMPLEMENTED,
            "status": False,
            "message": "Failed to process payment, try after some time.",
        }


def return_invalid_backoffice_response(*_):
    """this function returns response for invalid backoffice"""
    return {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "status": False,
        "message": "Invalid back office provided.",
    }


def start_session_back_office_selector(*args):
    """this function calls start session api of a particular
    back office"""

    # switcher = {
    #     SWARCO: swarco_start_session_function,
    #     DRIIVZ: drrivz_start_session_function,
    # }
    # func = switcher.get(back_office, return_invalid_backoffice_response)
    return drrivz_start_session_function(list(args))




def start_session_function(back_office, *args):
    drrivz_start_session_function(back_office, *args)
    return None


def stop_session_back_office_selector(back_office, *args):
    """this function calls stop session api of a particular
    back office"""
    switcher = {
        SWARCO: swarco_stop_session_function,
        DRIIVZ: drrivz_stop_session_function,
    }
    func = switcher.get(back_office, return_invalid_backoffice_response)
    return func(list(args))


def force_stop_session_back_office_selector(back_office, *args):
    """this function calls start session api of a particular
    back office"""
    switcher = {
        SWARCO: swarco_force_stop_session_function,
        DRIIVZ: drrivz_force_stop_session_function,
    }
    func = switcher.get(back_office, return_invalid_backoffice_response)
    return func(list(args))


def pre_auth_payment(
    pay_body,
    start_session_request,
    payment_failure_object,
    is_combined_payment=False,
):
    """pre auth payment"""
    pay_body["customer_id"] = start_session_request.user.get_customer_id()
    pay_body["idempotency_key"] = str(uuid.uuid1())
    pay_body["autocomplete"] = False
    pay_body["delay_duration"] = get_pre_auth_expiry_time()
    create_payment_result = make_request(
        POST_REQUEST,
        "/payments",
        start_session_request.user.id,
        module="Square create payment API",
        data=pay_body,
    )
    reponse_data = json.loads(create_payment_result.content)
    if create_payment_result.status_code != 200:
        print(
            "Failed to pre auth payment in start session for user id->"
            + f"{start_session_request.user.id}",
        )
        print(
            "Error"
            + f"{PAYMENT_ERROR_CODES.get(reponse_data[ERROR_CONST][0][CODE_CONST])}",
        )
        return Response(
            {
                "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                "status": False,
                "message": "An error occurred while authorizing the payment method.",
                "data": payment_failure_object,
            }
        )
    if "errors" not in reponse_data and "payment" in reponse_data:
        print(
            f"Card pre auth successfull in start session for user -> {start_session_request.user.id}"
        )
        pay_response = reponse_data["payment"]
        return [
            str(pay_response["id"]),
            (
                "Wallet and Card"
                if pay_response["card_details"]["entry_method"] == "ON_FILE"
                and is_combined_payment
                else "Wallet and Google/Apple Pay"
                if pay_response["card_details"]["entry_method"] == "KEYED"
                and is_combined_payment
                else "Card"
                if pay_response["card_details"]["entry_method"] == "ON_FILE"
                else "Google/Apple Pay"
            ),
            (COMBINED if is_combined_payment else NON_WALLET),
        ]
    print(
        f"Failed to pre auth payment in start session for user id-> {start_session_request.user.id}"
    )
    return Response(
        {
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "status": False,
            "message": "Something went wrong",
            "data": payment_failure_object,
        }
    )


def handle_start_session_pre_auth(
    start_session_request, payment_failure_object, session_id
):
    """this function handles start session pre auth"""
    is_combined_payment = start_session_request.data.get(
        "is_combined_payment", None
    )
    is_wallet_payment = start_session_request.data.get(
        "is_wallet_payment", None
    )

    if Profile.objects.filter(
        user=start_session_request.user,
        have_amount_due=YES,
    ).first():
        return Response(
            {
                "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                "status": False,
                "message": "Please pay the due amount",
            }
        )
    if is_combined_payment:
        payment_body = start_session_request.data.get("payment_body", None)
        if payment_body is None or payment_body is False:
            return Response(
                {
                    "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                    "status": False,
                    "message": "Payment declined.",
                    "data": payment_failure_object,
                }
            )
        payment_body=json.loads(payment_body)
        payment_body["reference_id"] = str(session_id)
        payment_id_checker = pre_auth_payment(
            payment_body,
            start_session_request,
            payment_failure_object,
            is_combined_payment,
        )
        return payment_id_checker
    if is_wallet_payment:
        user_gift_card_details = get_user_gift_card_details(
            start_session_request.user.customer_id,
            start_session_request.user.id,
        )
        if user_gift_card_details["status"] is False:
            return Response(
                {
                    "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                    "status": False,
                    "message": user_gift_card_details["message"],
                }
            )
        wallet_amount = float(user_gift_card_details["data"]["wallet_balance"])
        pre_auth_money = float(
            BaseConfigurations.objects.filter(
                base_configuration_key="wallet_preauthorize_money_ev"
            )
            .first()
            .base_configuration_value
        )
        if wallet_amount < pre_auth_money:
            return Response(
                {
                    "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                    "status": False,
                    "message": (
                        "Not sufficient balance in wallet to initiate session."
                    ),
                }
            )
        return [WALLET_TRANSACTIONS, "Wallet", "Partial"]
    else:
        payment_body = start_session_request.data.get("payment_body", None)
        if payment_body is None or payment_body is False:
            return Response(
                {
                    "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                    "status": False,
                    "message": "Payment declined.",
                    "data": payment_failure_object,
                }
            )
        payment_body["reference_id"] = str(session_id)
        payment_id_checker = pre_auth_payment(
            payment_body, start_session_request, payment_failure_object
        )
        return payment_id_checker
