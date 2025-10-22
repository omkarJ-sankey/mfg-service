"""charging session helper functions"""
# Date - 31/01/2022

# File details-
#   Author          - Manish Pawar
#   Description     - This file contains helper functions
#                       for charging session APIs.
#   Name            - chrging session helper functions
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 29/07/2025


# These are all the imports that we are exporting from
# different module's from project or library.
import json
import uuid
from datetime import datetime
import pytz
import sys, os
from decimal import Decimal
# from square.client import Client
from django.utils import timezone
from simplejson import JSONDecodeError
from decouple import config
from django.forms.models import model_to_dict
import traceback


# pylint:disable=import-error
from sharedServices.gift_card_common_functions import (
    get_user_gift_card_details,
)
from .model_files.station_models import Stations
from .model_files.transaction_models import (
    Transactions,
    TransactionsTracker,
)
from .model_files.charging_session_models import ChargingSession
from .model_files.app_user_models import Profile

from .common import (
    array_to_string_converter,
    string_to_array_converter,
    get_cdr_details
)
from .common_session_functions import (
    send_charging_payment_mail,
    create_payment_with_auto_deduct,
    add_failed_payment_amount_in_user_account,
    get_user_due_amount_for_session,
    return_payment_error_message,
    generate_payment_for_missed_sessions,
    custom_round_function,
    validate_session_id,
    send_old_charging_payment_mail
)
from .payments_helper_function import make_request
from .constants import (
    YES,
    SESSION_FAILED_TEMPLATE_ID,
    REDEEM_WALLET_TRANSACTION_FOR_CONST,
    COMMON_ERRORS,
    WALLET_TRANSACTIONS,
    CHARGING_SESSION,
    POST_REQUEST,
    PUT_REQUEST,
    NON_WALLET_TRANSACTIONS,
    COMBINED,
    PARTIAL,
    DRIIVZ,
    SWARCO
)

from .common_session_functions import (
    get_session_details,
    amount_formatter,
    validate_payment_id
)

from sharedServices.model_files.ocpi_sessions_models import OCPISessions


def get_driivz_account_number_for_user(mfg_user):
    """this function returns user driivz account number"""
    user_driivz_account_number = (
        Profile.objects.filter(user=mfg_user).first().driivz_account_number
    )
    return user_driivz_account_number if user_driivz_account_number else None


def send_session_payment_status_email(
    charging_session,
    payment_result,
    payment_success_mail=True,
    is_ocpi = True
):
    """this function sends session payment
    data in successful as well as failed scenario
    """
    try:
        if payment_success_mail:
            if is_ocpi:
                send_session_summary_mail = send_charging_payment_mail(
                    charging_session.first().id, payment_result
                )
            else:
                send_session_summary_mail = send_old_charging_payment_mail(
                    charging_session.first().id, payment_result
                )
        else:
            due_amount = get_user_due_amount_for_session(
                charging_session.first().user_id, charging_session.first().id
            )
            if due_amount:
                if is_ocpi:
                    send_session_summary_mail = send_charging_payment_mail(
                        charging_session.first().id,
                        template_id=SESSION_FAILED_TEMPLATE_ID,
                        due_amount=due_amount,
                    )
                else:
                    send_session_summary_mail = send_old_charging_payment_mail(
                        charging_session.first().id,
                        template_id=SESSION_FAILED_TEMPLATE_ID,
                        due_amount=due_amount,
                    )
            else:
                return None

        if send_session_summary_mail:
            charging_session.update(mail_status="sent")
            (
                print(
                    f"'Receipt email' sent to user -> \
                        {charging_session.first().user_id}"
                )
                if payment_success_mail
                else print(
                    f"'Failed payment email' sent to user -> \
                        {charging_session.first().user_id}"
                )
            )

        if not send_session_summary_mail:
            (
                print(
                    f"'Receipt email' failed for user -> \
                        {charging_session.first().user_id}"
                )
                if payment_success_mail
                else print(
                    f"'Failed payment email' failed for user -> \
                        {charging_session.first().user_id}"
                )
            )
    except COMMON_ERRORS as error_helper:
        print(
            f"sending payment mail function fail , 'Error cause'-> {error_helper}",
        )


def save_transaction_data_and_send_mail(
    charging_session,
    payment_result,
    paid_status="paid",
    send_success_email=True,
    paid_amount=None,
    is_ocpi_session = True,
):
    """this function saves transaction data and sends mail"""

    payment_data = payment_result["payment"]
    charging_session.update(
        payment_id=payment_data["id"],
        payment_response=array_to_string_converter([payment_result]),
        paid_status=paid_status,
        # total_cost=payment_data["total_money"]["amount"],
        payment_completed_at=datetime.strptime(
            payment_data["card_details"]["card_payment_timeline"][
                "captured_at"
            ],
            "%Y-%m-%dT%H:%M:%S.%fZ",
        ).replace(tzinfo=pytz.UTC),
    )
    transaction = Transactions.objects.create(
        station_id=Stations.objects.filter(
            id=charging_session.first().station_id.id
        ).first(),
        payment_id=payment_data["id"],
        order_id=payment_data["order_id"],
        transaction_id=payment_data["order_id"],
        transaction_amount=paid_amount
        if paid_amount
        else payment_data["total_money"]["amount"],
        transaction_currency=payment_data["total_money"]["currency"],
        created_date=timezone.now(),
        payment_for=CHARGING_SESSION,
        payment_for_reference_id=charging_session.first().id,
        customer_id=payment_data["customer_id"],
        payment_response=array_to_string_converter([payment_result]),
        is_ocpi_session = is_ocpi_session,
    )
    if not transaction:
        return False
    if send_success_email:
        send_session_payment_status_email(charging_session, payment_result,is_ocpi = is_ocpi_session)
    return True


def save_wallet_transaction_details(*args):
    (
        payment_customer_id,
        payment_id,
        payment_for_type,
        payment_for_subtype,
        payment_status,
        payment_response,
        payment_date,
        created_date,
        updated_date,
        user_id,
        transaction_amount,
        driivz_account_number,
    ) = args
    create_wallet_transaction_instance = TransactionsTracker.objects.create(
        payment_customer_id=payment_customer_id,
        payment_id=payment_id,
        payment_for_type=payment_for_type,
        payment_for_subtype=payment_for_subtype,
        payment_status=payment_status,
        payment_response=payment_response,
        payment_date=payment_date,
        created_date=created_date,
        updated_date=updated_date,
        user_id=user_id,
        transaction_amount=transaction_amount,
        driivz_account_number=driivz_account_number,
    )
    if not create_wallet_transaction_instance:
        print(
            "failed to track wallet transaction for Successful payment"
            if payment_status == "Successful"
            else "failed to track wallet transaction for Unsuccessful payment"
        )


def update_and_complete_payment(
    *args,
    admin_side_payment=False,
    is_payment_id_expired=False,
    payment_id_validation=None,
    is_ocpi = True
):
    try:
        (
            amount,
            currency,
            payment_id,
            session_user,
            charging_session,
            session_id,
            transaction_type,
        ) = args
        if not is_payment_id_expired:
            update_body = {}
            update_body["payment"] = {
                "amount_money": {"amount": amount, "currency": currency}
            }

            update_body["idempotency_key"] = str(uuid.uuid1())
            result = make_request(
                PUT_REQUEST,
                f"/payments/{payment_id}",
                charging_session.first().user_id.id,
                data=update_body,
                module="Square update payment API (Payment cronjob)",
            )

            if result.status_code != 200 or not "payment" in json.loads(
                result.content
            ):
                # update API failed
                print(
                    f"{charging_session.first().id} -> "
                    + f"Payment update api failed for user -> {session_user.id}"
                )
                add_failed_payment_amount_in_user_account(
                    session_user,
                    due_or_paid_amount=amount,
                    reference_id=session_id,
                    amount_due_for=CHARGING_SESSION,
                    payment_source=transaction_type,
                    have_due_amount=YES,
                    is_ocpi=is_ocpi
                )
                if not admin_side_payment:
                    send_session_payment_status_email(
                        charging_session,
                        json.loads(result.content),
                        payment_success_mail=False,
                        is_ocpi=is_ocpi
                    )
                return [
                    False,
                    [
                        return_payment_error_message(
                            result.content, "Payment update api failed"
                        ),
                        array_to_string_converter(
                            [json.loads(result.content)]
                        ),
                    ]
                    if admin_side_payment
                    else array_to_string_converter(
                        [json.loads(result.content)]
                    ),
                ]
            print(
                f"{charging_session.first().id} -> "
                + f"Payment update api successful for user -> {session_user.id}"
            )
        if is_payment_id_expired and payment_id_validation:
            payment_result = generate_payment_for_missed_sessions(
                payment_id_validation[0:3]
                + [
                    charging_session.first().user_id.customer_id,
                    amount,
                    charging_session,
                ],
                admin_screen_payment=False,
                is_ocpi=is_ocpi
            )
            if isinstance(payment_result, str):
                add_failed_payment_amount_in_user_account(
                    session_user,
                    due_or_paid_amount=amount,
                    reference_id=session_id,
                    amount_due_for=CHARGING_SESSION,
                    payment_source=transaction_type,
                    have_due_amount=YES,
                    is_ocpi=is_ocpi
                )
                return [
                    False,
                    [
                        f"Failed to process payment of {amount} due to : {payment_result}",
                        array_to_string_converter([payment_result]),
                    ],
                ]
            response_data = payment_result
        else:
            body = {}
            # complete payment call
            payment_result = make_request(
                POST_REQUEST,
                f"/payments/{payment_id}/complete",
                charging_session.first().user_id.id,
                data=body,
                module="Square complete payment API (Payment cronjob)",
            )
            response_data = json.loads(payment_result.content)

        if payment_result.status_code != 200 or "payment" not in response_data:
            print(
                f"{charging_session.first().id}->"
                + f"Payment complete api failed for user -> {session_user.id}"
            )
            add_failed_payment_amount_in_user_account(
                session_user,
                due_or_paid_amount=amount,
                reference_id=session_id,
                amount_due_for=CHARGING_SESSION,
                payment_source=transaction_type,
                have_due_amount=YES,
                is_ocpi=is_ocpi
            )
            if not admin_side_payment:
                send_session_payment_status_email(
                    charging_session,
                    response_data,
                    payment_success_mail=False,
                    is_ocpi=is_ocpi
                )

            # complete APi failed
            return [
                False,
                [
                    f"Failed to process payment of {amount} due to error: "
                    + f"{return_payment_error_message(response_data,'Failed to generate payment for expired session')}",
                    array_to_string_converter([response_data]),
                ]
                if admin_side_payment
                else array_to_string_converter([response_data]),
            ]
        add_failed_payment_amount_in_user_account(
            session_user, session_id, response_data["payment"]["id"], amount,is_ocpi=is_ocpi
        )
        print(
            f"{charging_session.first().id} -> Card payment "
            + f"successfully completed for user with id {session_user.id}"
        )
        transaction = save_transaction_data_and_send_mail(
            charging_session,
            response_data,
            is_ocpi_session=is_ocpi
        )
        if transaction:
            print(
                f"{charging_session.first().id} -> Successfully inserted "
                + f"payment in DB for user -> {session_user.id}"
            )
            return [
                True,
                [
                    "Payment processed successfully",
                    array_to_string_converter([response_data]),
                ]
                if admin_side_payment
                else array_to_string_converter([response_data]),
            ]

        print(
            f"{charging_session.first().id} -> Failed to create "
            + f"transaction in DB for user -> {session_user.id}"
        )
        return [
            False,
            [
                "Payment processed successfully but failed to create transaction in database.",
                array_to_string_converter(
                    [response_data]
                    + ["Failed to create transaction in database."]
                ),
            ]
            if admin_side_payment
            else array_to_string_converter(
                [response_data] + ["Failed to create transaction in database."]
            ),
        ]
    except Exception as error:
        exception_message = str(error)
        exception_type, exception_object, exception_traceback = sys.exc_info()
        filename = os.path.split(
            exception_traceback.tb_frame.f_code.co_filename
        )[1]
        print(
            f"{exception_message} {exception_type} {filename}, Line {exception_traceback.tb_lineno}"
        )


def collect_payment_from_wallet(
    *args,
    admin_side_payment=False,
    send_failed_payment_email=True,
    is_ocpi = True,
):
    try:
        [
            amount,
            currency,
            session_user,
            charging_session,
            session_id,
            transaction_type,
        ] = args
        transaction_type = WALLET_TRANSACTIONS
        user_gift_card_details = get_user_gift_card_details(
            session_user.customer_id, session_user.id
        )
        if user_gift_card_details["status"] is False:
            print(f'{user_gift_card_details["message"]}')
            add_failed_payment_amount_in_user_account(
                session_user,
                due_or_paid_amount=amount,
                reference_id=session_id,
                amount_due_for=CHARGING_SESSION,
                payment_source=transaction_type,
                have_due_amount=YES,
                is_ocpi=is_ocpi,
            )
            return [
                False,
                [
                    user_gift_card_details["message"],
                    array_to_string_converter(
                        [user_gift_card_details["message"]]
                    ),
                ]
                if admin_side_payment
                else array_to_string_converter(
                    [user_gift_card_details["message"]]
                ),
            ]
        payment_result = create_payment_with_auto_deduct(
            {
                "amount_money": {"amount": amount, "currency": currency},
                "source_id": (user_gift_card_details["data"]["gift_card_id"]),
            },
            session_user.customer_id,
            charging_session.first(),
            admin_screen_payment=False,
            is_ocpi=is_ocpi
        )
        if "error" in payment_result or "payment" not in payment_result:
            print(
                f"Wallet payment failed for user -> {session_user.id} and \
                    session id -> {session_id}"
            )
            print(f"Response -> {payment_result}")
            add_failed_payment_amount_in_user_account(
                session_user,
                due_or_paid_amount=amount,
                reference_id=session_id,
                amount_due_for=CHARGING_SESSION,
                payment_source=transaction_type,
                have_due_amount=YES,
                is_ocpi=is_ocpi,
            )
            save_wallet_transaction_details(
                session_user.customer_id,
                WALLET_TRANSACTIONS,
                "Wallet",
                REDEEM_WALLET_TRANSACTION_FOR_CONST,
                "Unsuccessful",
                array_to_string_converter([payment_result]),
                timezone.now(),
                timezone.now(),
                timezone.now(),
                session_user,
                amount,
                int(get_driivz_account_number_for_user(session_user)),
            )
            if send_failed_payment_email and not admin_side_payment:
                send_session_payment_status_email(
                    charging_session,
                    payment_result,
                    payment_success_mail=False,
                    is_ocpi=is_ocpi
                )

            # complete API failed
            return [
                False,
                [
                    return_payment_error_message(
                        payment_result,
                        "Failed to process the session payment through wallet",
                    ),
                    array_to_string_converter([payment_result]),
                ]
                if admin_side_payment
                else array_to_string_converter([payment_result]),
            ]
        add_failed_payment_amount_in_user_account(
            session_user, session_id, payment_result["payment"]["id"], amount,is_ocpi=is_ocpi,
        )
        print(
            f"{charging_session.first().id} -> Wallet payment "
            + f"completed for user with id{session_user.id}"
        )
        ChargingSession.objects.filter(id=session_id).update(
            deducted_voucher_amount=str(amount)
        )
        save_wallet_transaction_details(
            session_user.customer_id,
            payment_result["payment"]["id"],
            "Wallet",
            REDEEM_WALLET_TRANSACTION_FOR_CONST,
            "Successful",
            array_to_string_converter([payment_result]),
            timezone.now(),
            timezone.now(),
            timezone.now(),
            session_user,
            amount,
            int(get_driivz_account_number_for_user(session_user)),
        )
        transaction = save_transaction_data_and_send_mail(
            charging_session,
            payment_result,
        )
        if transaction:
            print(
                f"{charging_session.first().id} -> Successfully inserted payment "
                + f"in DB for user -> {session_user.id}"
            )
            return [
                True,
                [
                    f"Wallet Payment of GBP {amount} processed successfully",
                    array_to_string_converter([payment_result]),
                ]
                if admin_side_payment
                else array_to_string_converter([payment_result]),
            ]

        print(
            f"{charging_session.first().id} -> Failed to create transaction "
            + f"in DB for user -> {session_user.id}"
        )
        return [
            False,
            [
                f"Wallet Payment of GBP {amount} processed successfully but failed to"
                + " create transaction in database.",
                array_to_string_converter(
                    [payment_result]
                    + ["Failed to create transaction in database."]
                ),
            ]
            if admin_side_payment
            else array_to_string_converter(
                [payment_result]
                + ["Failed to create transaction in database."]
            ),
        ]
    except Exception as error:
        exception_message = str(error)
        exception_type, exception_object, exception_traceback = sys.exc_info()
        filename = os.path.split(
            exception_traceback.tb_frame.f_code.co_filename
        )[1]
        print(
            f"{exception_message} {exception_type} {filename}, Line {exception_traceback.tb_lineno}"
        )


def combined_payment_function(
    session_id,
    payment_id,
    amount,
    currency,
    charging_session,
    session_user,
    transaction_type,
    admin_side_payment=False,
    payment_id_validation=None,
    is_ocpi = True
):
    print(
        f"{charging_session.first().id} -> "
        + f"Combined payment started for user -> {session_user.id}"
    )
    is_error_or_gpay_apple_pay = False
    is_payment_id_expired = False
    if admin_side_payment and payment_id_validation is not None:
        if isinstance(payment_id_validation, str):
            is_error_or_gpay_apple_pay = True
        if isinstance(payment_id_validation, list):
            is_payment_id_expired = True
    user_gift_card_details = get_user_gift_card_details(
        session_user.customer_id, session_user.id
    )
    wallet_amount = Decimal(user_gift_card_details["data"]["wallet_balance"])
    if custom_round_function(wallet_amount * 100) >= amount:
        payment_result = collect_payment_from_wallet(
            amount,
            currency,
            session_user,
            charging_session,
            session_id,
            transaction_type,
            admin_side_payment=admin_side_payment,
            send_failed_payment_email=False,
            is_ocpi = is_ocpi
        )
        if (
            payment_result[0] is False
            and get_user_due_amount_for_session(
                session_user, charging_session.first().id
            )
            is not None
        ):
            if is_error_or_gpay_apple_pay:
                return [
                    False,
                    [
                        return_payment_error_message(
                            payment_result,
                            f"Cannot reprocess this session because : "
                            + f"{payment_id_validation}",
                        ),
                        array_to_string_converter(
                            [
                                "Cannot reprocess this session because : "
                                + f"{payment_id_validation}"
                            ]
                        ),
                    ],
                ]
            print(
                f"{charging_session.first().id} -> Wallet payment failed and "
                + "payment type is combined, so redirecting to card payment"
            )
            return update_and_complete_payment(
                amount,
                currency,
                payment_id,
                session_user,
                charging_session,
                session_id,
                transaction_type,
                admin_side_payment=admin_side_payment,
                is_payment_id_expired=is_payment_id_expired,
                payment_id_validation=payment_id_validation,
                is_ocpi = is_ocpi
            )
        return payment_result

    elif wallet_amount > 0 and custom_round_function(wallet_amount * 100) < amount:
        payment_result = create_payment_with_auto_deduct(
            {
                "amount_money": {
                    "amount": custom_round_function(wallet_amount * 100),
                    "currency": currency,
                },
                "source_id": (user_gift_card_details["data"]["gift_card_id"]),
            },
            session_user.customer_id,
            charging_session.first(),
            admin_screen_payment=False,
            is_ocpi = is_ocpi
        )
        if "errors" not in payment_result and "payment" in payment_result:
            save_wallet_transaction_details(
                session_user.customer_id,
                payment_result["payment"]["id"],
                "Wallet",
                REDEEM_WALLET_TRANSACTION_FOR_CONST,
                "Successful",
                array_to_string_converter([payment_result]),
                timezone.now(),
                timezone.now(),
                timezone.now(),
                session_user,
                custom_round_function(wallet_amount * 100),
                int(get_driivz_account_number_for_user(session_user)),
            )
            if is_ocpi:
                OCPISessions.objects.filter(id=session_id).update(
                    deducted_voucher_amount=str(custom_round_function(wallet_amount * 100))
                )
            else:
                ChargingSession.objects.filter(id=session_id).update(
                    deducted_voucher_amount=str(custom_round_function(wallet_amount * 100))
                )
            amount -= custom_round_function(wallet_amount * 100)
            print(
                f"{charging_session.first().id} payment amount "
                + "updated for combined payment after wallet transaction success"
            )
            # here we have to save the transaction data in TransactionTracker and Transaction
            add_failed_payment_amount_in_user_account(
                session_user,
                due_or_paid_amount=amount,
                reference_id=session_id,
                amount_due_for=CHARGING_SESSION,
                payment_source=transaction_type,
                have_due_amount=YES,
                is_ocpi=is_ocpi,
            )

            transaction = save_transaction_data_and_send_mail(
                charging_session,
                payment_result,
                paid_status="unpaid",
                send_success_email=False,
            )
            if not transaction:
                print(
                    "failed to store transaction data for combined payment wallet transaction"
                )
            if is_error_or_gpay_apple_pay:
                return [
                    False,
                    [
                        f"Deducted GBP {custom_round_function(wallet_amount * 100)} from voucher, "
                        + f"Remaining amount was not processed due to : {payment_id_validation} ",
                        array_to_string_converter([payment_result]),
                    ],
                ]
        else:
            print("wallet payment failed , redirecting to card payment")
            if is_error_or_gpay_apple_pay:
                return [
                    False,
                    [
                        f"Voucher payment failed and Failed to process session "
                        + f"payment due to : {payment_id_validation}",
                        array_to_string_converter([payment_result]),
                    ],
                ]
            save_wallet_transaction_details(
                session_user.customer_id,
                WALLET_TRANSACTIONS,
                "Wallet",
                REDEEM_WALLET_TRANSACTION_FOR_CONST,
                "Unsuccessful",
                array_to_string_converter([payment_result]),
                timezone.now(),
                timezone.now(),
                timezone.now(),
                session_user,
                custom_round_function(wallet_amount * 100),
                int(get_driivz_account_number_for_user(session_user)),
            )

        return update_and_complete_payment(
            amount,
            currency,
            payment_id,
            session_user,
            charging_session,
            session_id,
            transaction_type,
            admin_side_payment=admin_side_payment,
            is_payment_id_expired=is_payment_id_expired,
            payment_id_validation=payment_id_validation,
        )
    else:
        if is_error_or_gpay_apple_pay:
            return [
                False,
                [
                    "Cannot reprocess this session because :"
                    + f"{payment_id_validation}",
                    array_to_string_converter(
                        [
                            "Cannot reprocess this session because :"
                            + f"{payment_id_validation}"
                        ]
                    ),
                ],
            ]
        return update_and_complete_payment(
            amount,
            currency,
            payment_id,
            session_user,
            charging_session,
            session_id,
            transaction_type,
            admin_side_payment=admin_side_payment,
            is_payment_id_expired=is_payment_id_expired,
            payment_id_validation=payment_id_validation,
        )


def partial_payment_function(
    session_id,
    amount,
    currency,
    charging_session,
    session_user,
    transaction_type,
    admin_side_payment=False,
    is_ocpi=True
):
    print(f"Partial payment Started for user ==> {session_user.id}")
    user_gift_card_details = get_user_gift_card_details(
        session_user.customer_id, session_user.id
    )
    wallet_amount = float(user_gift_card_details["data"]["wallet_balance"])
    if wallet_amount <= 0:
        print("payment cannot be proccessed due to empty wallet")
        add_failed_payment_amount_in_user_account(
            session_user,
            due_or_paid_amount=amount,
            reference_id=session_id,
            amount_due_for=CHARGING_SESSION,
            payment_source=transaction_type,
            have_due_amount=YES,
            is_ocpi=is_ocpi,
        )
        if not admin_side_payment:
            send_session_payment_status_email(
                charging_session,
                None,
                payment_success_mail=False,
                is_ocpi = is_ocpi
            )
        return [
            False,
            [
                "Cannot start partial payment as wallet has zero balance",
                array_to_string_converter(
                    ["Cannot start partial payment as wallet has zero balance"]
                ),
            ]
            if admin_side_payment
            else array_to_string_converter(
                ["Cannot start partial payment as wallet has zero balance"]
            ),
        ]
    elif custom_round_function(wallet_amount * 100) < amount:
        payment_result = create_payment_with_auto_deduct(
            {
                "amount_money": {
                    "amount": (wallet_amount * 100),
                    "currency": currency,
                },
                "source_id": (user_gift_card_details["data"]["gift_card_id"]),
            },
            session_user.customer_id,
            charging_session.first(),
            admin_screen_payment=False,
        )
        if "errors" not in payment_result and "payment" in payment_result:
            print(
                f"Partial payment successful for user -> \
                    {session_user.id}"
            )
            if is_ocpi:
                OCPISessions.objects.filter(id=session_id).update(
                    deducted_voucher_amount=str(wallet_amount * 100)
                )
            else:
                ChargingSession.objects.filter(id=session_id).update(
                    deducted_voucher_amount=str(wallet_amount * 100)
                )
            save_wallet_transaction_details(
                session_user.customer_id,
                payment_result["payment"]["id"],
                "Wallet",
                REDEEM_WALLET_TRANSACTION_FOR_CONST,
                "Successful",
                array_to_string_converter([payment_result]),
                timezone.now(),
                timezone.now(),
                timezone.now(),
                session_user,
                custom_round_function(wallet_amount * 100),
                int(get_driivz_account_number_for_user(session_user)),
            )
            amount -= custom_round_function(wallet_amount * 100)
            print("due amount updated")
            add_failed_payment_amount_in_user_account(
                session_user,
                due_or_paid_amount=amount,
                reference_id=session_id,
                amount_due_for=CHARGING_SESSION,
                payment_source=transaction_type,
                have_due_amount=YES,
                is_ocpi=is_ocpi,
            )
            print(
                f"added updated due amount to DB for user -> {session_user.id}"
            )
            transaction = save_transaction_data_and_send_mail(
                charging_session,
                payment_result,
                paid_status="unpaid",
                send_success_email=False,
                is_ocpi_session = is_ocpi
            )
            if not transaction:
                print(
                    f"wallet transaction data of Combined payment not added\
                          to DB for user -> {session_user.id}"
                )
            send_session_payment_status_email(
                charging_session,
                payment_result,
                payment_success_mail=False,
                is_ocpi = is_ocpi
            )
            return [
                True,
                [
                    "Only partial amount deducted as wallet does not have full payable amount",
                    array_to_string_converter([payment_result]),
                ]
                if admin_side_payment
                else array_to_string_converter([payment_result]),
            ]
        else:
            print(
                f"{charging_session.first().id} -> Partial Payment failed "
                + f"for user -> {session_user.id}"
            )
            add_failed_payment_amount_in_user_account(
                session_user,
                due_or_paid_amount=amount,
                reference_id=session_id,
                amount_due_for=CHARGING_SESSION,
                payment_source=transaction_type,
                have_due_amount=YES,
                is_ocpi=is_ocpi,
            )
            print(f"due amount set in DB for user -> {session_user.id}")
            save_wallet_transaction_details(
                session_user.customer_id,
                WALLET_TRANSACTIONS,
                "Wallet",
                REDEEM_WALLET_TRANSACTION_FOR_CONST,
                "Unsuccessful",
                array_to_string_converter([payment_result]),
                timezone.now(),
                timezone.now(),
                timezone.now(),
                session_user,
                custom_round_function(wallet_amount * 100),
                int(get_driivz_account_number_for_user(session_user)),
            )
            send_session_payment_status_email(
                charging_session,
                payment_result,
                payment_success_mail=False,
                is_ocpi = is_ocpi
            )
            return [
                False,
                [
                    return_payment_error_message(
                        payment_result, "Failed to process the session payment"
                    ),
                    array_to_string_converter([payment_result]),
                ]
                if admin_side_payment
                else array_to_string_converter([payment_result]),
            ]
    else:
        return collect_payment_from_wallet(
            amount,
            currency,
            session_user,
            charging_session,
            session_id,
            transaction_type,
            admin_side_payment=admin_side_payment,
            is_ocpi=is_ocpi
        )

def make_session_payment_function(
    session_id, payment_id, amount, currency, payment_type,is_ocpi = False
):
    """make session payment"""
    try:
        charging_session = ChargingSession.objects.filter(id=session_id)
        if charging_session.first() is None:
            return [
                False,
                array_to_string_converter(
                    [
                        "Failed to get session data "
                        + "with respect to provided session id."
                    ]
                ),
            ]
        session_user = charging_session.first().user_id
        print(f"Starting Payment process for user -> {session_user.id}")
        transaction_type = NON_WALLET_TRANSACTIONS
        if payment_type == COMBINED:
            return combined_payment_function(
                session_id,
                payment_id,
                amount,
                currency,
                charging_session,
                session_user,
                transaction_type,
            )
        elif payment_id == WALLET_TRANSACTIONS and payment_type == PARTIAL:
            transaction_type = WALLET_TRANSACTIONS
            return partial_payment_function(
                session_id,
                amount,
                currency,
                charging_session,
                session_user,
                transaction_type,
                is_ocpi = False
            )
        else:
            print(
                f"Non-wallet payment started for user => {session_user.id}"
            )
            return update_and_complete_payment(
                amount,
                currency,
                payment_id,
                session_user,
                charging_session,
                session_id,
                transaction_type,
                is_ocpi = is_ocpi
            )

    except COMMON_ERRORS as error:
        print(
            f"Exception occured during session payment for session id \
                -> {session_id}"
        )
        print(f"Exception -> {error}")

def make_session_payment_function_ocpi(
    session_id, payment_id, amount, currency, payment_type
):
    """make session payment"""
    try:
        charging_session = OCPISessions.objects.filter(id=session_id)
        if charging_session.first() is None:
            return [
                False,
                array_to_string_converter(
                    [
                        "Failed to get session data "
                        + "with respect to provided session id."
                    ]
                ),
            ]
        session_user = charging_session.first().user_id
        print(f"Starting Payment process for user -> {session_user.id}")
        transaction_type = NON_WALLET_TRANSACTIONS
        if payment_type == COMBINED:
            return combined_payment_function(
                session_id,
                payment_id,
                amount,
                currency,
                charging_session,
                session_user,
                transaction_type,
                is_ocpi = True
            )
        elif payment_id == WALLET_TRANSACTIONS and payment_type == PARTIAL:
            transaction_type = WALLET_TRANSACTIONS
            return partial_payment_function(
                session_id,
                amount,
                currency,
                charging_session,
                session_user,
                transaction_type,
                is_ocpi = True
            )
        else:
            print(
                f"Non-wallet payment started for user => {session_user.id}"
            )
            return update_and_complete_payment(
                amount,
                currency,
                payment_id,
                session_user,
                charging_session,
                session_id,
                transaction_type,
                is_ocpi = True
            )

    except COMMON_ERRORS as error:
        print(
            f"Exception occured during session payment for session id \
                -> {session_id}"
        )
        print(f"Exception -> {error}")


def handle_session_invalid_cdr_payment(session_id):
    """this function handles payment of unpaid sessions"""
    try:
        session_exists = session_id
        cdr_data = get_cdr_details(session_id)

        if cdr_data.last() is None:
            return None

        
        # session_response = get_session_details(session_id)
        session = session_exists#OCPISessions.objects.filter(id = session_id).first()
        if session is not None and cdr_data.last() is not None and json.loads(cdr_data.last().total_cost)["incl_vat"] != 0 :
            if session.paid_status == "paid":
                return [
                    False,
                    "Session already paid. Cannot be re-processed.",
                ]
            
                    
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
            OCPISessions.objects.filter(id = session_id.id).update(
                charging_data=array_to_string_converter([session_data]),
                is_cdr_valid = True
            )

            # if cdr_data.last() is not None and json.loads(cdr_data.last().total_cost)["incl_vat"] == 0:
            #     return [
            #         False,
            #         "Session cannot be re-processed.",
            #     ]
            
        # if (
        #     session_response is None or
        #     (session_response and session_response.status_code != 200)
        # ):
        #     return [
        #         False,
        #             "Unable to get session details,"
        #             + " please try after some time.",
        #         ]
            # session_data = json.loads(session_response.content)
            session_data = session_exists
            # session_not_valid = validate_session_id(session_data)
            # if session_not_valid:
            #     return session_not_valid
            # session_exists.update(
            #     charging_data=array_to_string_converter([session_data])
            # )
            payment_response = complete_session_payment(
                session_exists, False  # validate payment id status
            )
            if payment_response:
                return payment_response
        # if session_exists.first() is None:
        #     # if session not in db then fetch data from drrivz
        #     # and start payment process
        #     if (
        #         session_response is None or
        #         (session_response and session_response.status_code != 200)
        #     ):
        #         return ["Session ID not found.", False]
        #     session_data = json.loads(session_response.content)
        #     session_not_valid = validate_session_id(session_data)
        #     if session_not_valid:
        #         return session_not_valid
        #     connector_info = StationConnector.objects.filter(
        #         connector_id=session_data["connectorId"]
        #     ).first()
        #     if connector_info is None:
        #         return [
        #             False,
        #             "Payment Authorisation not found for session. "
        #             + "Please contact customer directly for payment."
        #             + " Account: "
        #             + str(session_data["accountNumber"])
        #             + ", Session: "
        #             + str(session_data["transactionId"])
        #             + ".",
        #         ]
        #     if (
        #         connector_info.station_id is None
        #         or connector_info.charge_point_id is None
        #     ):
        #         return [
        #             False,
        #             "Payment Authorisation not found for session. "
        #             + "Please contact customer directly for payment."
        #             + " Account: "
        #             + str(session_data["accountNumber"])
        #             + ", Session: "
        #             + str(session_data["transactionId"])
        #             + ".",
        #         ]
        #     # submit session details in session table
        #     start_time = datetime.strptime(
        #         session_data["startOn"].split(".")[0], "%Y-%m-%dT%H:%M:%S"
        #     ).replace(tzinfo=pytz.UTC)
        #     end_time = datetime.strptime(
        #         session_data["stopOn"].split(".")[0], "%Y-%m-%dT%H:%M:%S"
        #     ).replace(tzinfo=pytz.UTC)
        #     start_time_minute = start_time.minute
        #     session_check = ChargingSession.objects.filter(
        #         user_account_number=session_data["accountNumber"],
        #         session_status__in=["rejected", "start"],
        #         connector_id=connector_info,
        #         start_time__date=start_time.date(),
        #         start_time__hour=start_time.hour,
        #         start_time__minute__in=[
        #             start_time_minute - 2,
        #             start_time_minute - 1,
        #             start_time_minute,
        #             start_time_minute + 1,
        #             start_time_minute + 2,
        #         ],
        #     ).order_by("-start_time")
        #     if session_check.first() is None:
        #         return [
        #             False,
        #             "Payment Authorisation not found for session. "
        #             + "Please contact customer directly for payment."
        #             + " Account: "
        #             + str(session_data["accountNumber"])
        #             + ", Session: "
        #             + str(session_data["transactionId"])
        #             + ".",
        #         ]
        #     session = ChargingSession.objects.filter(
        #         id=session_check.first().id
        #     )
        #     session.update(
        #         emp_session_id=session_data["transactionId"],
        #         end_time=timezone.localtime(end_time),
        #         charging_data=array_to_string_converter([session_data]),
        #     )
        #     # if session_data["transactionStatus"] != BILLED:
        #     #     session.update(
        #     #         session_status="completed",
        #     #     )
        #     #     return [
        #     #         False,
        #     #         "Session payment is not completed because,"
        #     #         + " session status is not BILLED.",
        #     #     ]
        #     payment_response = complete_session_payment(
        #         session, True  # validate payment id status
        #     )
        #     if payment_response:
        #         return payment_response
        return [
            True,
            "Payment re-processed successfully.",
        ]
    except Exception as error:#ConnectionError as error:
        traceback.print_exc()
        print(f"Session payment process failed due to ->{str(error)}")
        return [
            False,
            "Something went wrong while processing payment,"
            + "Please try after sometime.",
        ]



def complete_session_payment(session, validate_payment_status,is_ocpi = True):
    """complete session payment"""
    try:
        session = OCPISessions.objects.filter(id = session.id)
        payment_id = session.first().payment_id
        payment_type = session.first().payment_type
        session_data = string_to_array_converter(
            session.first().charging_data
        )[0]
        cdr_data = get_cdr_details(session.first().id)
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
            session_cost = amount_formatter(json.loads(cdr_data.last().total_cost)["incl_vat"])
        if payment_id == WALLET_TRANSACTIONS and payment_type == PARTIAL:
            payment_result = partial_payment_function(
                session.first().id,
                session_cost,
                config("DJANGO_APP_PAYMENT_CURRENCY"),
                session,
                session.first().user_id,
                WALLET_TRANSACTIONS,
                admin_side_payment=True,
            )
            session.update(
                payment_response=payment_result[1][1],
            )
            return [payment_result[0], payment_result[1][0]]
        else:
            payment_id_validation = validate_payment_id(
                payment_id, validate_payment_status, session.first().user_id.id
            )
            if (
                not session_cost or session_cost <= 0
            ) and session.first().preauth_status != "collected":
                session_cost = amount_formatter(json.loads(cdr_data.last().total_cost)["incl_vat"])
            else:
                print()
                session_cost = amount_formatter(
                    json.loads(cdr_data.last().total_cost)["incl_vat"]
                )
                # ) - int(float((payment_id_validation[3])))
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
                    return [
                        False,
                        "Unable to process payment: "
                        + str(payment_response)
                        + ". Please contact customer directly for payment"
                        + " Account: "
                        + str(session_data["accountNumber"])
                        + ", Session: "
                        + str(session_data["transactionId"])
                        + ".",
                    ]
                if isinstance(payment_id_validation, list):
                    # payment id is invalid or expired
                    # print("payment_id_validation0 ",payment_id_validation[0])
                    # print("payment_id_validation1 ",payment_id_validation[1])
                    # print("payment_id_validation2 ",payment_id_validation[2])
                    # print("customer_id ",customer_id)
                    # print("session_cost : ",session_cost)
                    # print("session_cost : ",session)
                    payment_response = generate_payment_for_missed_sessions(
                        payment_id_validation[0],payment_id_validation[1],payment_id_validation[2],
                        customer_id, session_cost, session
                    )
                    if isinstance(payment_response, str):
                        return [
                            False,
                            "Unable to process payment: "
                            + str(payment_response)
                            + ". Please contact customer directly for payment"
                            + " Account: "
                            + str(session_data["accountNumber"])
                            + ", Session: "
                            + str(session_data["transactionId"])
                            + ".",
                        ]
                    print("payment completed")
                    total_cost = payment_response["payment"]["total_money"][
                        "amount"
                    ]
                    add_failed_payment_amount_in_user_account(
                        session.first().user_id,
                        session.first().id,
                        payment_response["payment"]["id"],
                        session_cost,
                        is_ocpi=is_ocpi,
                    )
                    session.update(
                        payment_response=array_to_string_converter(
                            [payment_response]
                        ),
                        payment_id=payment_response["payment"]["id"],
                        total_cost_incl=total_cost,
                        paid_status="paid",
                    )
                    if send_charging_payment_mail(
                        session_uid, payment_response,config("DJANGO_APP_CHARGING_SESSION_PAYMENT_MAIL_TEMPLATE_ID")
                    ):
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
        traceback.print_exc()
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

