"""gift card common functions"""
# Date - 11/08/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file contains gift card common functions.
#   Name            - Gift card common functions
#   Modified by     - Manish Pawar
#   Modified date   - 30/11/2022


# These are all the imports that we are exporting from
# different module's from project or library.
import json
import uuid
from datetime import datetime
import pytz
from decouple import config
from decimal import Decimal
# from square.client import Client
from cryptography.fernet import Fernet

from django.utils import timezone
from rest_framework import status

# pylint:disable=import-error
from sharedServices.email_common_functions import email_sender
from sharedServices.model_files.app_user_models import Profile
from sharedServices.payments_helper_function import make_request
from sharedServices.constants import (
    ERROR_CONST,
    CODE_CONST,
    WALLET_CREDIT_TEMPLATE_ID,
    POST_REQUEST,
)
from sharedServices.error_codes import PAYMENT_ERROR_CODES

# client = Client(
#     access_token=config("DJANGO_PAYMENT_ACCESS_TOKEN"),
#     environment=config("DJANGO_PAYMENT_ENV"),
# )

# gift_cards = client.gift_cards
# gift_cards_activity = client.gift_card_activities
# payments_api = client.payments

ACTIVE_GIFT_CARD_STATE = "ACTIVE"
PENDING_GIFT_CARD_STATE = "PENDING"

LOAD_GIFT_CARD = "LOAD"
ACTIVATE_GIFT_CARD = "ACTIVATE"

GIFT_CARD = "gift_card"

GIFT_CARD_STATE_TYPES = [PENDING_GIFT_CARD_STATE, ACTIVE_GIFT_CARD_STATE]

LOCATION_ID = config("DJANGO_PAYMENT_LOCATION_ID")
FAILED_TO_CREATE_GIFT_CARD = "Failed to create wallet entry"

NOT_PROPER_GIFT_CARD_STATE = (
    "Not able to get required state of a gift card for payment."
)


# function to generate card and link it to customer
def create_customer_gift_card(customer_id, user):
    """create gift card for customer"""
    # create customer gift card API call
    result = make_request(
        POST_REQUEST,
        "/gift-cards",
        user.id,
        module="Square create gift card API",
        data={
            "idempotency_key": str(uuid.uuid1()),
            "location_id": LOCATION_ID,
            GIFT_CARD: {"type": "DIGITAL"},
        },
    )
    response_data = json.loads(result.content)
    if result.status_code != 200:
        return PAYMENT_ERROR_CODES.get(
            response_data[ERROR_CONST][0][CODE_CONST]
        )
    if GIFT_CARD in response_data:
        gift_card_response = response_data[GIFT_CARD]
        # link customer to gift card
        link_customer_result = make_request(
            POST_REQUEST,
            f'/gift-cards/{gift_card_response["id"]}/link-customer',
            user.id,
            module="Square link gift card API",
            data={"customer_id": customer_id},
        )
        response_data = json.loads(link_customer_result.content)
        if link_customer_result.status_code != 200:
            return PAYMENT_ERROR_CODES.get(
                response_data[ERROR_CONST][0][CODE_CONST]
            )
        if GIFT_CARD in response_data:
            link_customer_response = response_data[GIFT_CARD]
            if (
                customer_id in link_customer_response["customer_ids"]
                and gift_card_response["id"] == link_customer_response["id"]
            ):
                Profile.objects.filter(user__customer_id=customer_id).update(
                    user_gift_card_id=gift_card_response["id"],
                    user_gift_card_gan=gift_card_response["gan"],
                )
                return None
    return FAILED_TO_CREATE_GIFT_CARD


def retrieve_gift_card_from_gan_api_call(gift_card_gan, user_id):
    """this function is used to get details of user gif card"""
    return make_request(
        POST_REQUEST,
        "/gift-cards/from-gan",
        user_id,
        module="Square retrieve card with gan API",
        data={"gan": gift_card_gan},
    )


def retrieve_gift_card_status(gift_card_gan, user_id):
    """this function returns status of gift card eg. ACTIVE"""
    result = retrieve_gift_card_from_gan_api_call(gift_card_gan, user_id)
    response_data = json.loads(result.content)
    if result.status_code != 200:
        return PAYMENT_ERROR_CODES.get(
            response_data[ERROR_CONST][0][CODE_CONST]
        )
    if GIFT_CARD in response_data:
        return response_data[GIFT_CARD]["state"]
    return None


def send_add_credited_amount_email(
    gift_card_request,
    payment_response,
    amount_credited,
    previous_amount,
    current_amount,
    credited_from_admin=False,
    template_id=WALLET_CREDIT_TEMPLATE_ID,
):
    """send add credited amount email"""
    if credited_from_admin:
        user = gift_card_request
    else:
        user = gift_card_request.user
    decrypter = Fernet(user.key)
    to_emails = [
        (
            decrypter.decrypt(user.encrypted_email).decode(),
            decrypter.decrypt(user.first_name).decode(),
        )
    ]
    if credited_from_admin:
        payment_created_date = timezone.localtime(timezone.now())
        card_last_4 = None
    else:
        payment_created_date = timezone.localtime(
            datetime.strptime(
                payment_response["payment"]["updated_at"],
                "%Y-%m-%dT%H:%M:%S.%fZ",
            ).replace(tzinfo=pytz.UTC)
        )
        card_last_4 = payment_response["payment"]["card_details"]["card"][
            "last_4"
        ]

    email_sender(
        template_id,
        to_emails,
        {
            "amount_credited": format(amount_credited, ".2f"),
            "previous_amount": format(previous_amount, ".2f"),
            "current_amount": format(current_amount, ".2f"),
            "payment_card": f"**** **** **** { card_last_4 }",
            "payment_date": (
                payment_created_date.date().strftime("%d/%m/%Y")
                + " "
                + payment_created_date.time().strftime("%H:%M:%S")
            ),
        },
    )


def get_user_gift_card_details(customer_id, user_id):
    """this function retrives user gift card info"""
    user_profile = Profile.objects.filter(
        user__customer_id=customer_id
    ).first()
    result = retrieve_gift_card_from_gan_api_call(
        user_profile.user_gift_card_gan, user_id
    )
    response_data = json.loads(result.content)
    if result.status_code != 200:
        print(
            "Failed to get user gift card for user with id ->",
            user_id,
            "Error ->",
            PAYMENT_ERROR_CODES.get(response_data[ERROR_CONST][0][CODE_CONST]),
        )
        return {
            "status_code": status.HTTP_501_NOT_IMPLEMENTED,
            "status": False,
            "message": PAYMENT_ERROR_CODES.get(
                response_data[ERROR_CONST][0][CODE_CONST]
            ),
        }
    balance_money_object = response_data[GIFT_CARD]["balance_money"]
    return {
        "status_code": status.HTTP_200_OK,
        "status": True,
        "data": {
            "wallet_balance": (
                format(Decimal(str(balance_money_object["amount"])) / 100, ".2f")
            ),
            "gift_card_id": response_data[GIFT_CARD]["id"],
        },
    }
