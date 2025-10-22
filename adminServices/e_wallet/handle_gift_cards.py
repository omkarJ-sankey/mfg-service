"""gift card helper functions"""
# Date - 11/08/2021

# File details-
#   Author          - Manish Pawar
#   Description     - This file contains gift card helper functions.
#   Name            - Gift card helper functions
#   Modified by     - Manish Pawar
#   Modified date   - 30/11/2022


# These are all the imports that we are exporting from
# different module's from project or library.
import json
import uuid
import math
from decouple import config
from datetime import timedelta

from django.utils import timezone

# from square.client import Client

# pylint:disable=import-error
from sharedServices.models import TransactionsTracker
from sharedServices.common import (
    array_to_string_converter,
)
from sharedServices.models import MFGUserEV
from sharedServices.payments_helper_function import make_request
from sharedServices.constants import (
    POST_REQUEST,
)
from sharedServices.constants import (
    # CREATE_PAYMENT_PROCESS_FAILED,
    WALLET_TRANSACTION_FOR_CONST,
    LOAD_WALLET_TRANSACTION_FOR_CONST,
    ACTIVATE_WALLET_TRANSACTION_FOR_CONST,
    ERROR_CONST,
    CODE_CONST,
    WALLET_ADMIN_CREDIT_TEMPLATE_ID,
    # WALLET_ADMIN_WITHDRAWL_TEMPLATE_ID,
    YES,
)
from sharedServices.error_codes import PAYMENT_ERROR_CODES

from sharedServices.gift_card_common_functions import (
    ACTIVE_GIFT_CARD_STATE,
    LOAD_GIFT_CARD,
    ACTIVATE_GIFT_CARD,
    GIFT_CARD_STATE_TYPES,
    LOCATION_ID,
    NOT_PROPER_GIFT_CARD_STATE,
)
from sharedServices.gift_card_common_functions import (
    create_customer_gift_card,
    retrieve_gift_card_status,
    send_add_credited_amount_email,
    get_user_gift_card_details,
)
from .app_level_constants import PROCESSED_BY_ADMIN


# client = Client(
#     access_token=config("DJANGO_PAYMENT_ACCESS_TOKEN"),
#     environment=config("DJANGO_PAYMENT_ENV"),
# )

# gift_cards = client.gift_cards
# gift_cards_activity = client.gift_card_activities
# payments_api = client.payments


def get_user_wallet_balance_details(
    user,
    amount,
    wallet_credit=True,
):
    """this function retunrns wallet amount details of user"""
    gift_card_data = get_user_gift_card_details(
        user.get_customer_id(), user.id
    )
    if gift_card_data["status"] is False:
        return {
            "msg": gift_card_data["message"],
            "status": gift_card_data["status"],
        }
    operated_amount = float(amount)
    previous_amount = float(gift_card_data["data"]["wallet_balance"])
    updated_amount = (
        previous_amount + operated_amount
        if wallet_credit
        else previous_amount - operated_amount
    )
    return (operated_amount, previous_amount, updated_amount)


def send_wallet_transaction_email(
    user,
    operated_amount,
    previous_amount,
    updated_amount,
    template_id=WALLET_ADMIN_CREDIT_TEMPLATE_ID,
):
    """this function sends email of wallet transaction"""
    send_add_credited_amount_email(
        user,
        None,
        operated_amount,
        previous_amount,
        updated_amount,
        credited_from_admin=True,
        template_id=template_id,
    )


def gift_card_activity_handler(*args):
    """credit amount in user gift card"""
    (user, profile, amount, pay_body, assignee, expiry_days) = args
    customer_id = user.get_customer_id()
    if profile.user_gift_card_id is None:
        create_gift_card_status = create_customer_gift_card(
            customer_id,
            profile.user
        )
        if create_gift_card_status is not None:
            print(
                "Failed to generate gift card/"
                + f" of user with id -> {profile.user.id},"
                + " due to ->",
                create_gift_card_status,
            )
            return {"msg": create_gift_card_status, "status": False}
    pay_body["customer_id"] = customer_id
    pay_body["idempotency_key"] = str(uuid.uuid1())
    pay_body["autocomplete"] = True
    cost_data = pay_body["amount_money"]
    cost_data["amount"] = math.ceil(cost_data["amount"] * 100)
    pay_body["amount_money"] = cost_data
    transaction_id = str(uuid.uuid1())
    # updating or adding amount to gift card
    gift_card_state = retrieve_gift_card_status(
        profile.user_gift_card_gan,
        profile.user.id,
    )
    if (
        gift_card_state is None or
        gift_card_state not in GIFT_CARD_STATE_TYPES
    ):
        return {
            "msg": NOT_PROPER_GIFT_CARD_STATE,
            "status": False
        }

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
    transaction_tracker_objects.payment_id = transaction_id
    transaction_tracker_objects.payment_for_type = WALLET_TRANSACTION_FOR_CONST
    transaction_tracker_objects.payment_for_subtype = (
        LOAD_WALLET_TRANSACTION_FOR_CONST
        if gift_card_state == ACTIVE_GIFT_CARD_STATE
        else ACTIVATE_WALLET_TRANSACTION_FOR_CONST
    )
    transaction_tracker_objects.processed_by = PROCESSED_BY_ADMIN
    transaction_tracker_objects.payment_status = "Successful"
    transaction_tracker_objects.payment_date = timezone.localtime(
        timezone.now()
    )
    transaction_tracker_objects.created_date = timezone.localtime(
        timezone.now()
    )
    transaction_tracker_objects.driivz_account_number = (
        profile.driivz_account_number
    )
    transaction_tracker_objects.assigned_by = assignee
    transaction_tracker_objects.comments = pay_body["description"]
    (
        operated_amount,
        previous_amount,
        updated_amount,
    ) = get_user_wallet_balance_details(
        user,
        amount,
    )
    result = make_request(
        POST_REQUEST,
        f'/gift-cards/activities',
        profile.user.id,
        module="Square create gift card activity API",
        data={
            "idempotency_key": str(uuid.uuid1()),
            "gift_card_activity": {
                "type": gift_card_activity_type,
                "location_id": LOCATION_ID,
                "gift_card_id": profile.user_gift_card_id,
                f"{activity_details_text}": {
                    "amount_money": {
                        "amount": pay_body["amount_money"]["amount"],
                        "currency": pay_body["amount_money"]["currency"],
                    },
                    "buyer_payment_instrument_ids": [transaction_id],
                },
            },
        },
    )
    transaction_tracker_objects.reference_response = array_to_string_converter(
        [json.loads(result.content)]
    )
    if result.status_code != 200:
        error_data = json.loads(result.content)
        print(
            "Add credits in gift card failed "
            + f" for user with id -> {profile.user.id},"
            + " due to ->",
            error_data[ERROR_CONST][0][CODE_CONST],
        )
        transaction_tracker_objects.reference_current_status = "Unsuccessful"
        transaction_tracker_objects.save()
        return {
            "msg": PAYMENT_ERROR_CODES.get(
                error_data[ERROR_CONST][0][CODE_CONST])
            ,
            "status": False
        }
    transaction_tracker_objects.transaction_amount = pay_body[
        "amount_money"
    ]["amount"]
    transaction_tracker_objects.reference_current_status = "Successful"
    
    transaction_tracker_objects.user_updated_balance = str(
        updated_amount
    )
    transaction_tracker_objects.expiry_date = timezone.localtime(
        timezone.now()
    ) + timedelta(days=int(expiry_days))

    send_wallet_transaction_email(
        user,
        operated_amount,
        previous_amount,
        updated_amount
    )
    transaction_tracker_objects.save()
    return {
        "msg": "payment created successfully.",
        "status": True,
        "payment_id": transaction_id
    }


def get_wallet_amount_details_for_user(transaction, user):
    """this function returns wallet amount details of user"""
    (
        # operated_amount,
        # previous_amount,
        _,
        _,
        updated_amount
    ) = get_user_wallet_balance_details(
        transaction.first().user_id,
        float(transaction.first().transaction_amount) / 100,
        wallet_credit=False,
    )
    result = make_request(
        POST_REQUEST,
        '/gift-cards/activities',
        transaction.first().user_id.id,
        module="Square create gift card activity API",
        data={
            "idempotency_key": str(uuid.uuid1()),
            "gift_card_activity": {
                "type": "REDEEM",
                "location_id": LOCATION_ID,
                "gift_card_id": (
                    transaction.first().user_id.user_profile.user_gift_card_id
                ),
                f"redeem_activity_details": {
                    "amount_money": {
                        "amount": transaction.first().transaction_amount,
                        "currency": config("DJANGO_APP_PAYMENT_CURRENCY"),
                    },
                    "reference_id": transaction.first().payment_id,
                },
            },
        },
    )
    if result.status_code != 200:
        error_data = json.loads(result.content)
        return PAYMENT_ERROR_CODES.get(
            error_data[ERROR_CONST][0][CODE_CONST]
        )
    # send_wallet_transaction_email(
    #     transaction.first().user_id,
    #     operated_amount,
    #     previous_amount,
    #     updated_amount,
    #     template_id=WALLET_ADMIN_WITHDRAWL_TEMPLATE_ID
    # )
    transaction.update(
        user_updated_balance=str(updated_amount),
        is_withdrawn=YES,
        updated_date=timezone.localtime(timezone.now()),
        updated_by=user.full_name,
    )
    return None
