"""giftcard apis"""
# Date - 11/08/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on APIs related to customer.
#   Name            - Customer API
#   Modified by     - Manish Pawar
#   Modified date   - 12/08/2021


# These are all the imports that we are exporting from
# different module's from project or library.

# import concurrent.futures
# import threading
# from datetime import timedelta
import json
import uuid
import math
# from decouple import config
# from square.client import Client

# from passlib.hash import django_pbkdf2_sha256 as handler

# from django.conf import settings
from django.utils import timezone

# from django.db.models import Q, Sum

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

# pylint:disable=import-error
from sharedServices.common import (
    handle_concurrent_user_login,
    array_to_string_converter,
)
# from sharedServices.email_common_functions import (
#     email_sender,
# )
# from sharedServices.model_files.config_models import (
#     BaseConfigurations
# )
from sharedServices.model_files.app_user_models import Profile, MFGUserEV
from sharedServices.model_files.transaction_models import TransactionsTracker
from sharedServices.model_files.config_models import BaseConfigurations
from sharedServices.payments_helper_function import make_request
from sharedServices.constants import (
    POST_REQUEST,
)
from sharedServices.gift_card_common_functions import (
    create_customer_gift_card,
    send_add_credited_amount_email,
    retrieve_gift_card_status,
    get_user_gift_card_details,
    ACTIVE_GIFT_CARD_STATE,
    LOAD_GIFT_CARD,
    ACTIVATE_GIFT_CARD,
    GIFT_CARD_STATE_TYPES,
    NOT_PROPER_GIFT_CARD_STATE,
    LOCATION_ID,
)
from sharedServices.constants import (
    CREATE_PAYMENT_PROCESS_FAILED,
    WALLET_TRANSACTION_FOR_CONST,
    LOAD_WALLET_TRANSACTION_FOR_CONST,
    ACTIVATE_WALLET_TRANSACTION_FOR_CONST,
    # REDEEM_WALLET_TRANSACTION_FOR_CONST,
    ERROR_CONST,
    CODE_CONST,
    NO,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    # SECRET_KEY_NOT_PROVIDED,
    # SECRET_KEY_IN_VALID,
)
from sharedServices.error_codes import PAYMENT_ERROR_CODES
from backendServices.backend_app_constants import (
    MULTIPLE_LOGIN,
    UNAUTHORIZED,
)
from .app_level_constants import MAX_BALANCE_IN_WALLET


# DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET = settings.DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET

# client = Client(
#     access_token=config("DJANGO_PAYMENT_ACCESS_TOKEN"),
#     environment=config("DJANGO_PAYMENT_ENV"),
# )

# gift_cards = client.gift_cards
# gift_cards_activity = client.gift_card_activities
# payments_api = client.payments


# this function is called when user wants to add amount to his
# his wallet
def gift_card_activity_handler(
    gift_card_request, amount_credited, previous_amount
):
    """function to add amount to customers wallet"""
    customer_id = gift_card_request.user.get_customer_id()
    pay_body = gift_card_request.data
    user_profile = Profile.objects.filter(
        user__customer_id=customer_id
    ).first()
    if user_profile.user_gift_card_id is None:
        create_gift_card_status = create_customer_gift_card(
            customer_id,
            gift_card_request.user
        )
        if create_gift_card_status is not None:
            print(
                "Failed to generate gift card/"
                + f" of user with id -> {user_profile.user.id},"
                + " due to ->",
                create_gift_card_status,
            )
            return create_gift_card_status

    # creating user payment
    pay_body["customer_id"] = customer_id
    pay_body["idempotency_key"] = str(uuid.uuid1())
    pay_body["autocomplete"] = True
    cost_data = pay_body["amount_money"]
    cost_data["amount"] = math.ceil(cost_data["amount"] * 100)
    pay_body["amount_money"] = cost_data
    create_payment_result = make_request(
        POST_REQUEST,
        f'/payments',
        gift_card_request.user.id,
        module="Square create gift card payment API",
        data=pay_body
    )
    create_payment_response_data = json.loads(create_payment_result.content)
    if create_payment_result.status_code != 200:
        print(
            "Create payment for gift card failed "
            + f" for user with id -> {user_profile.user.id},"
            + " due to ->",
            create_payment_response_data[ERROR_CONST][0][CODE_CONST],
        )
        return PAYMENT_ERROR_CODES.get(
            create_payment_response_data[ERROR_CONST][0][CODE_CONST]
        )
    if (
        "payment" in create_payment_response_data
    ):
        # updating or adding amount to gift card
        gift_card_state = retrieve_gift_card_status(
            user_profile.user_gift_card_gan,
            user_profile.user.id
        )
        if (
            gift_card_state is None or
            gift_card_state not in GIFT_CARD_STATE_TYPES
        ):
            return NOT_PROPER_GIFT_CARD_STATE

        gift_card_activity_type = ACTIVATE_GIFT_CARD
        activity_details_text = "activate_activity_details"
        if gift_card_state == ACTIVE_GIFT_CARD_STATE:
            gift_card_activity_type = LOAD_GIFT_CARD
            activity_details_text = "load_activity_details"

        transaction_tracker_objects = TransactionsTracker()
        transaction_tracker_objects.user_id = MFGUserEV.objects.filter(
            customer_id=customer_id
        ).first()
        transaction_tracker_objects.payment_customer_id = customer_id
        transaction_tracker_objects.payment_id = create_payment_response_data[
            "payment"
        ]["id"]
        transaction_tracker_objects.payment_for_type = (
            WALLET_TRANSACTION_FOR_CONST
        )
        transaction_tracker_objects.payment_for_subtype = (
            LOAD_WALLET_TRANSACTION_FOR_CONST
            if gift_card_state == ACTIVE_GIFT_CARD_STATE
            else ACTIVATE_WALLET_TRANSACTION_FOR_CONST
        )
        transaction_tracker_objects.payment_status = "Successful"
        transaction_tracker_objects.payment_response = (
            array_to_string_converter([create_payment_response_data])
        )
        transaction_tracker_objects.payment_date = timezone.now()
        transaction_tracker_objects.created_date = timezone.now()

        result = make_request(
            POST_REQUEST,
            f'/gift-cards/activities',
            user_profile.user.id,
            module="Square create gift card activity API",
            data={
                "idempotency_key": str(uuid.uuid1()),
                "gift_card_activity": {
                    "type": gift_card_activity_type,
                    "location_id": LOCATION_ID,
                    "gift_card_id": user_profile.user_gift_card_id,
                    f"{activity_details_text}": {
                        "amount_money": {
                            "amount": pay_body["amount_money"]["amount"],
                            "currency": pay_body["amount_money"]["currency"],
                        },
                        "buyer_payment_instrument_ids": [
                            create_payment_response_data["payment"]["id"]
                        ],
                    },
                },
            },
        )
        response_data = json.loads(result.content)
        transaction_tracker_objects.reference_response = (
            array_to_string_converter([response_data])
        )
        if result.status_code != 200:
            print(
                "Add credits in gift card failed "
                + f" for user with id -> {user_profile.user.id},"
                + " due to ->",
                response_data[ERROR_CONST][0][CODE_CONST],
            )
            transaction_tracker_objects.reference_current_status = (
                "Unsuccessful"
            )
            transaction_tracker_objects.save()
            return PAYMENT_ERROR_CODES.get(
                response_data[ERROR_CONST][0][CODE_CONST]
            )
        transaction_tracker_objects.transaction_amount = pay_body[
            "amount_money"
        ]["amount"]
        transaction_tracker_objects.reference_current_status = "Successful"
        transaction_tracker_objects.save()
        send_add_credited_amount_email(
            gift_card_request,
            create_payment_response_data,
            amount_credited,
            previous_amount,
            amount_credited + previous_amount,
        )
        return None
    return CREATE_PAYMENT_PROCESS_FAILED


class AddCreditsInWallet(APIView):
    """add amount in wallet"""

    permission_classes = [IsAuthenticated]

    @classmethod
    def post(cls, gift_card_request):
        """add amount in wallet"""
        try:
            if not gift_card_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                gift_card_request.user.id, gift_card_request.auth
            ):
                return MULTIPLE_LOGIN
            if (
                "amount_money" in gift_card_request.data
                and "amount" in gift_card_request.data["amount_money"]
            ):
                gift_card_data = get_user_gift_card_details(
                    gift_card_request.user.get_customer_id(),
                    gift_card_request.user.id,
                )
                if gift_card_data["status"] is False:
                    return Response(gift_card_data)
                max_amount_balance = MAX_BALANCE_IN_WALLET
                max_amount_balance_in_db = BaseConfigurations.objects.filter(
                    base_configuration_key="wallet_maximum_balance_amount"
                ).first()
                if max_amount_balance_in_db:
                    max_amount_balance = float(
                        max_amount_balance_in_db.base_configuration_value
                    )
                if (
                    float(gift_card_data["data"]["wallet_balance"])
                    + float(gift_card_request.data["amount_money"]["amount"])
                ) > max_amount_balance:
                    return Response(
                        {
                            "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                            "status": False,
                            "message": (
                                "Can't amend additional amount "
                                + "in Wallet as maximum limit i.e. "
                                + f"£{format(float(max_amount_balance), '.2f')} "
                                + "has been reached."
                            ),
                        }
                    )
            gift_card_activity_status = gift_card_activity_handler(
                gift_card_request,
                float(gift_card_request.data["amount_money"]["amount"]),
                float(gift_card_data["data"]["wallet_balance"]),
            )
            if gift_card_activity_status is not None:
                return Response(
                    {
                        "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                        "status": False,
                        "message": gift_card_activity_status,
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Amount credited successfully",
                }
            )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT


# def get_user_wallet_transaction(user):
#     """this function return transactions of user that
#         can be used for refunf process"""
#     return TransactionsTracker.objects.filter(
#         ~Q(refund_status__in = ["Pending", "Completed"]),
#         payment_status = "Successful",
#         reference_current_status = "Successful",
#         user_id = user,
#         payment_date__gte = (
#             timezone.now() - timedelta(days=365)
#         ),
#     )


# def refund_payment_function(
#         payment_id,
#         transaction_amount
#     ):
#     """this is the common function to call refund API"""
#     return client.refunds.refund_payment(
#         body = {
#             "idempotency_key": str(uuid.uuid1()),
#             "amount_money": {
#                 "amount": transaction_amount,
#                 "currency": config("DJANGO_APP_PAYMENT_CURRENCY")
#             },
#             "payment_id": payment_id,
#             "reason": "Wallet refund"
#         }
#     )


# def redeem_amount_from_gift_card(
#     gift_card_id,
#     transaction_amount
# ):
#     return client.gift_card_activities.create_gift_card_activity(
#         body = {
#             "idempotency_key": str(uuid.uuid1()),
#             "gift_card_activity": {
#                 "type": "REDEEM",
#                 "location_id": LOCATION_ID,
#                 "gift_card_id": gift_card_id,
#                 "redeem_activity_details": {
#                     "amount_money": {
#                         "amount": transaction_amount,
#                         "currency": config("DJANGO_APP_PAYMENT_CURRENCY")
#                     }
#                 }
#             }
#         }
#     )


# class RefundWalletPayment(APIView):
#     """refund wallet credited money"""

#     permission_classes = [IsAuthenticated]
#     @classmethod
#     def get(cls, refund_request):
#         """refund wallet credited money"""
#         if not refund_request.auth:
#             return UNAUTHORIZED

#         if not handle_concurrent_user_login(
#             refund_request.user.id,
#             refund_request.auth
#         ):
#             return MULTIPLE_LOGIN
#         user_wallet_transactions = get_user_wallet_transaction(
#             refund_request.user
#         )
#         return Response(
#             {
#                 "status_code": status.HTTP_200_OK,
#                 "status": True,
#                 "message": "Refundable amount fetch successfully.",
#                 "data": {
#                     "refundable_amount":(
#                         user_wallet_transactions.aggregate(
#                             Sum('transaction_amount')
#                         )['transaction_amount__sum']
#                     )
#                 }
#             }
#         )

#     @classmethod
#     def post(cls, refund_request):
#         """refund wallet credited money"""
#         if not refund_request.auth:
#             return UNAUTHORIZED

#         if not handle_concurrent_user_login(
#             refund_request.user.id,
#             refund_request.auth
#         ):
#             return MULTIPLE_LOGIN

#         user_profile_entry = Profile.objects.filter(
#             user = refund_request.user
#         ).first()
#         refund_amount = refund_request.data.get("refund_amount" ,None)
#         if not refund_amount:
#             return Response(
#                 {
#                     "status_code": status.HTTP_406_NOT_ACCEPTABLE,
#                     "status": False,
#                     "message": "Refund amount must be greater than"+
#                     " zero and below your available refundable amount."
#                 }
#             )
#         user_wallet_transactions = get_user_wallet_transaction(
#             refund_request.user
#         )
#         user_refundable_amount = user_wallet_transactions.aggregate(
#             Sum('transaction_amount')
#         )[
#             'transaction_amount__sum'
#         ]
#         if (
#             int(refund_amount) >
#             user_refundable_amount
#         ):
#             return Response(
#                 {
#                     "status_code": status.HTTP_406_NOT_ACCEPTABLE,
#                     "status": False,
#                     "message": (
#                         "Refund amount exceeds available "+
#                         "refundable amount"
#                     )
#                 }
#             )
#         # following code is to check whether there is some
#         # row with higher transaction amount than requested refund amount
#         transaction_with_greater_amount = user_wallet_transactions.filter(
#             transaction_amount__gte = int(refund_amount)
#         )
#         if (
#             user_refundable_amount != int(refund_amount) and
#             transaction_with_greater_amount.first()
#         ):
#             # transaction with greater transaction amount
#             # than requested refund value found
#             print(
#                 "transaction with greater transaction amount"
#                 " than requested refund value found"
#             )
#             single_transaction = TransactionsTracker.objects.filter(
#                 id = transaction_with_greater_amount.first().id
#             )
#             single_transaction_result = refund_payment_function(
#                 single_transaction.first().payment_id,
#                 int(refund_amount)
#             )

#             if (
#                 single_transaction_result.is_success() and
#                 "refund" in single_transaction_result.body
#             ):
#                 single_transaction.update(
#                     refund_reference_id = single_transaction_result.body[
#                         'refund'
#                     ]['id'],
#                     refund_status = "Pending",
#                     refund_amount = int(refund_amount),
#                     refund_response = array_to_string_converter(
#                         single_transaction_result.body
#                     ),
#                     refund_initiated_date = timezone.now()
#                 )
#                 reedem_activity_result = redeem_amount_from_gift_card(
#                     user_profile_entry.user_gift_card_id,
#                     int(refund_amount)
#                 )

#                 single_transaction.update(
#                     payment_for_subtype = (
#                         REDEEM_WALLET_TRANSACTION_FOR_CONST
#                     ),
#                     reference_response = array_to_string_converter(
#                         reedem_activity_result.body
#                     )
#                 )
#                 if reedem_activity_result.is_success():
#                     single_transaction.update(
#                         reference_current_status = "Successful"
#                     )
#                 if reedem_activity_result.is_error():
#                     single_transaction.update(
#                         reference_current_status = "Unsuccessful"
#                     )
#                 return Response(
#                     {
#                         "status_code": status.HTTP_200_OK,
#                         "status": True,
#                         "message": "Refund request accepted successfully.",
#                     }
#                 )
#             elif single_transaction_result.is_error():
#                 print(
#                     "refund payment request failed for user with id -> ",
#                     refund_request.user.id
#                 )
#                 print(single_transaction_result.errors)

#         # Iterate over transaction to process refund
#         amount_refunded = 0
#         requsted_refund_amount = int(refund_amount)
#         for iterating_transactions in (
#             user_wallet_transactions.order_by('-transaction_amount')
#         ):
#             iterating_transaction = TransactionsTracker.objects.filter(
#                 id = iterating_transactions.id
#             )
#             transaction_amount = (
#                 iterating_transaction.first().transaction_amount
#             )
#             if transaction_amount > refund_amount:
#                 transaction_amount = refund_amount
#             iterating_transaction_result = refund_payment_function(
#                 iterating_transaction.first().payment_id,
#                 transaction_amount
#             )
#             if iterating_transaction_result.is_success():
#                 iterating_transaction.update(
#                     refund_reference_id = iterating_transaction_result.body[
#                         'refund'
#                     ]['id'],
#                     refund_status = "Pending",
#                     refund_amount = transaction_amount,
#                     refund_response = array_to_string_converter(
#                         iterating_transaction_result.body
#                     ),
#                     refund_initiated_date = timezone.now(),
#                     reference_current_status = "Successful"
#                 )

#                 refund_amount -= transaction_amount
#                 amount_refunded += transaction_amount

#                 reedem_activity_result = redeem_amount_from_gift_card(
#                     user_profile_entry.user_gift_card_id,
#                     transaction_amount
#                 )

#                 iterating_transaction.update(
#                     payment_for_subtype = (
#                         REDEEM_WALLET_TRANSACTION_FOR_CONST
#                     ),
#                     reference_response = array_to_string_converter(
#                         reedem_activity_result.body
#                     )
#                 )
#                 if reedem_activity_result.is_success():
#                     iterating_transaction.update(
#                         reference_current_status = "Successful"
#                     )
#                 if reedem_activity_result.is_error():
#                     iterating_transaction.update(
#                         reference_current_status = "Unsuccessful"
#                     )
#             elif iterating_transaction_result.is_error():
#                 print(
#                     "refund payment request failed for user with id -> ",
#                     refund_request.user.id
#                 )
#                 print(iterating_transaction_result.errors)

#             if not refund_amount:
#                 break
#         if amount_refunded != requsted_refund_amount:
#             return Response(
#                 {
#                     "status_code": status.HTTP_200_OK,
#                     "status": True,
#                     "message": (
#                         "Refund request accepted for amount "+
#                         str(amount_refunded)+ " "+
#                         config("DJANGO_APP_PAYMENT_CURRENCY")+
#                         ", Please contact MFG customer "+
#                         "care for more details."
#                     ),
#                 }
#             )
#         return Response(
#             {
#                 "status_code": status.HTTP_200_OK,
#                 "status": True,
#                 "message": "Refund request accepted successfully.",
#             }
#         )


# def get_payment_refund_status(transaction):
#     """get status of refund"""
#     transaction_object = TransactionsTracker.objects.filter(
#         id=transaction.id
#     )
#     result = client.refunds.get_payment_refund(
#         refund_id = transaction.refund_reference_id
#     )
#     decrypter = Fernet(transaction.user_id.key)
#     to_emails = [
#         (
#             decrypter.decrypt(
#                 transaction.user_id.encrypted_email
#             ).decode(),
#             decrypter.decrypt(
#                 transaction.user_id.first_name
#             ).decode(),
#         )
#     ]
#     dynamic_data = {
#         "user_name": decrypter.decrypt(
#             transaction.user_id.first_name
#         ).decode(),
#         "full_name": (
#             decrypter.decrypt(
#                 transaction.user_id.first_name
#             ).decode()+" "+
#             decrypter.decrypt(
#                 transaction.user_id.last_name
#             ).decode()
#         ),
#         "refund_initiated_date": (
#             transaction.refund_initiated_date.date().strftime(
#                     "%d/%m/%Y"
#             )+ " " +
#             transaction.refund_initiated_date.time().strftime(
#                 "%H:%M:%S"
#             )
#         ),
#         "refund_amount": transaction.refund_amount,
#         "message": "",
#     }
#     if (
#         result.is_success() and
#         "refund" in result.body
#     ):
#         response = result.body["refund"]
#         dynamic_data['status'] = response['status']
#         if response['status'] == "PENDING":
#             return None
#         if response['status'] == "COMPLETED":
#             transaction_object.update(
#                 refund_completed_date = timezone.now(),
#                 refund_status = "Completed"
#             )
#             email_sender(
#                 None,
#                 to_emails,
#                 dynamic_data
#             )
#             return None
#         transaction_object.update(
#             refund_status = (
#                 "Rejected"
#                 if response['status'] == "REJECTED"
#                 else "Failed"
#             )
#         )
#         gift_card_load_result = gift_cards_activity.\
#             create_gift_card_activity(
#             body = {
#                 "idempotency_key": str(uuid.uuid1()),
#                 "gift_card_activity": {
#                     "type": LOAD_GIFT_CARD,
#                     "location_id": LOCATION_ID,
#                     "gift_card_id": (
#                         transaction.user_id.profile.user_gift_card_id
#                     ),
#                     f"load_activity_details": {
#                         "amount_money": {
#                             "amount": transaction.refund_amount,
#                             "currency": config("DJANGO_APP_PAYMENT_CURRENCY")
#                         },
#                         "buyer_payment_instrument_ids": [
#                             transaction.payment_id
#                         ]
#                     }
#                 }
#             }
#         )
#         transaction_object.update(
#             payment_for_subtype = (
#                 LOAD_GIFT_CARD
#             ),
#             reference_response = array_to_string_converter(
#                 gift_card_load_result.body
#             )
#         )
#         if gift_card_load_result.is_success():
#             transaction_object.update(
#                 reference_current_status = "Successful"
#             )
#         if gift_card_load_result.is_error():
#             transaction_object.update(
#                 reference_current_status = "Unsuccessful"
#             )
#         mfg_customer_care = BaseConfigurations.objects.filter(
#             base_configuration_key="mfg_customer_care"
#         ).first().base_configuration_value
#         dynamic_data["message"] = (
#             "Plese call customer service at "+
#             mfg_customer_care
#         )
#         email_sender(
#             None,
#             to_emails,
#             dynamic_data
#         )
#     return None


# def check_refund_payment_statuses():
#     """this function is used to check and update status of refunds"""
#     refund_transaction = TransactionsTracker.objects.filter(
#         ~Q(refund_reference_id=None),
#         refund_status="Pending"
#     )

#     with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
#         executor.map(
#             get_payment_refund_status,
#             list(refund_transaction),
#         )


# class RefundPaymentsCheckerCronjob(APIView):
#     """cronjonb API to check refund status"""

#     @classmethod
#     def post(cls, cron_job_request):
#         """post method to initialize cron job api"""
#         secret_key_azure = cron_job_request.data.get("secret_key", None)
#         if secret_key_azure is None:
#             return SECRET_KEY_NOT_PROVIDED
#         if not handler.verify(
#               secret_key_azure,
#               DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
#         ):
#             return SECRET_KEY_IN_VALID

#         start_time = threading.Thread(
#             target=check_refund_payment_statuses,,
#             daemon=True
#         )
#         start_time.start()

#         return Response(
#             {
#                 "status_code": status.HTTP_200_OK,
#                 "status": False,
#                 "message": "Cron job initiated.",
#             }
#         )
