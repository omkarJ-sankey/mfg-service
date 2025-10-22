"""cards API"""
# Date - 12/08/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on APIs related to customer.
#   Name            - Cards API
#   Modified by     - Manish Pawar
#   Modified date   - 31/03/2023


# These are all the imports that we are exporting from
# different module's from project or library.
import json
import uuid

# from decouple import config

# from square.client import Client

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

# pylint:disable=import-error
from sharedServices.common import (
    handle_concurrent_user_login,
    decrypt_user_mail
)
from sharedServices.common_session_functions import (
    get_user_total_due_amount,
)
from backendServices.charging_sessions.driivz_apis import check_3ds_trigger_for_user

from sharedServices.model_files.app_user_models import Profile
from sharedServices.model_files.config_models import BaseConfigurations
from sharedServices.payments_helper_function import make_request
from sharedServices.constants import (
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    YES,
    POST_REQUEST,
    GET_REQUEST,
    ON_CONST
)
from backendServices.backend_app_constants import (
    MULTIPLE_LOGIN,
    UNAUTHORIZED,
    DATA_NOT_FOUND,
    DATA_INVALID,
    SERVER_ERROR,
)

from backendServices.payment.customerapis import CreateCustomerApi
# from sharedServices.gift_card_common_functions import (
#     create_customer_gift_card,
#     get_user_gift_card_details,
# )

# client = Client(
#     access_token=config("DJANGO_PAYMENT_ACCESS_TOKEN"),
#     environment=config("DJANGO_PAYMENT_ENV"),
# )
# cards_api = client.cards


class CustomersListCardsApi(APIView):
    """customer card list"""

    permission_classes = [IsAuthenticated]

    @classmethod
    def get(cls, list_cards_request):
        """get customer cards"""
        try:
            cards_list_result = make_request(
                GET_REQUEST,
                "/cards?include_disabled=false",
                list_cards_request.user.id,
                module="Square list cards API",
            )
            if cards_list_result.status_code != 200:
                return DATA_INVALID
            cards_data = json.loads(cards_list_result.content)
            if "cards" in cards_data:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "successfully loaded cards\
                                for all customers",
                        "data": {"cardsdata": cards_data["cards"]},
                    }
                )
            return DATA_NOT_FOUND
        except Exception as error:
            print(
                "Failed to cards for "
                + f"user with id ->{list_cards_request.user.id}"
                + "due to exception -> "
            )
            print(error)
            return SERVER_ERROR


class RetrieveCustomerCardsApi(APIView):
    """retrieve customer cards"""

    permission_classes = [IsAuthenticated]

    @classmethod
    def get(cls, retrieve_customer_request):
        """get customer cards"""
        try:
            if not retrieve_customer_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                retrieve_customer_request.user.id,
                retrieve_customer_request.auth,
            ):
                return MULTIPLE_LOGIN
            customer_id = retrieve_customer_request.user.get_customer_id()
            if not customer_id:
                user_name = retrieve_customer_request.user.username
                customer_req_body = {
                    "given_name": user_name,
                    "reference_id": user_name,
                    "email_address": decrypt_user_mail(
                        retrieve_customer_request.user
                    ),
                }
                customer_data = CreateCustomerApi.post(customer_req_body)
                if customer_data.data["status_code"] == status.HTTP_200_OK:
                    customer_id = customer_data.data["customersdata"]["id"]
                    # response=create_customer_gift_card(
                    #     customer_id,
                    #     retrieve_customer_request.user
                    # )
                    # print("***********************",response)
                    # return response
                else:
                    return DATA_INVALID
            # if (
            #     retrieve_customer_request.user.user_profile.user_gift_card_id
            #     is None
            # ):
            #     gift_card_creation = create_customer_gift_card(
            #         customer_id,
            #         retrieve_customer_request.user
            #     )
            #     if gift_card_creation is not None:
            #         return Response(
            #             {
            #                 "status_code": status.HTTP_501_NOT_IMPLEMENTED,
            #                 "status": False,
            #                 "messgae": gift_card_creation
            #             }
            #         )
            default_payment_method = (
                retrieve_customer_request.user.user_profile.default_payment_method
            )
            two_factor_auth_done = (
                retrieve_customer_request.user.user_profile.two_factor_done
            )
            three_ds_config_db = BaseConfigurations.objects.filter(
                base_configuration_key="3ds_configurations"
            ).first()
            # print(f"[DEBUG] three_ds_config_db: {three_ds_config_db}")
            should_check_3ds = False
            if three_ds_config_db and three_ds_config_db.base_configuration_value:
                three_ds_config = json.loads(three_ds_config_db.base_configuration_value)
                if (
                    (str(three_ds_config.get("kwh_consumed_within__trigger_value", None)) == "0" and
                     str(three_ds_config.get("kwh_consumed_within__condition_checkbox", None)) == "on")
                    or
                    (str(three_ds_config.get("total_transactions_within__trigger_value", None)) == "0" and
                     str(three_ds_config.get("total_transactions_within__condition_checkbox", None)) == "on")
                ):
                    should_check_3ds = True
                    print("[DEBUG] should_check_3ds set to True based on 3DS configurations")
            if should_check_3ds:
                check_3ds_trigger_for_user(
                    retrieve_customer_request.user,
                    three_ds_status=False
                )
            if default_payment_method is None:
                default_payment_method = 0
            # gift_card_data = get_user_gift_card_details(
            #     customer_id, retrieve_customer_request.user.id
            # )
            # if gift_card_data["status"] is False:
            #     return Response(gift_card_data)
            listing_card_api_response = make_request(
                GET_REQUEST,
                f"/cards?customer_id={customer_id}&include_disabled=false&sort_order=ASC",
                retrieve_customer_request.user.id,
                module="Square retrieve user cards API",
            )
            if listing_card_api_response.status_code != 200:
                return DATA_INVALID
            cards_data = json.loads(listing_card_api_response.content)
            cards = []
            user_due_session_amount = get_user_total_due_amount(
                retrieve_customer_request.user
            )
            if "cards" in cards_data:
                cards = [
                    {
                        **card,
                        **{
                            "card_index": card_index,
                            "is_default": (
                                card_index == int(default_payment_method)
                            ),
                        },
                    }
                    for card_index, card in enumerate(cards_data["cards"])
                ]
            due_amount = 0
            have_due_amount = False
            is_3ds_check_active = retrieve_customer_request.user.user_profile.is_3ds_check_active
            if (
                user_due_session_amount is not None
                and user_due_session_amount != 0
                and str(user_due_session_amount).isnumeric()
            ):
                have_due_amount = True
                due_amount = format(
                    float(str(user_due_session_amount)) / 100, ".2f"
                )
            three_ds_configurations_from_db = BaseConfigurations.objects.filter(
                base_configuration_key="3ds_configurations"
            ).first()
            if (
                three_ds_configurations_from_db and
                three_ds_configurations_from_db.base_configuration_value
            ):
                three_ds_configurations = json.loads(
                    three_ds_configurations_from_db.base_configuration_value
                )
                if (
                    'trigger_three_ds_for_all_transaction_checkbox' in three_ds_configurations and
                    three_ds_configurations['trigger_three_ds_for_all_transaction_checkbox'] == ON_CONST
                ):
                    is_3ds_check_active = True
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "successfully loaded cards for a customer",
                    "customercardsdata": cards,
                    "gift_card_data": None,
                    "is_pay_as_go_default": (
                        int(default_payment_method) == -2
                    ),
                    "is_prepared_default": (int(default_payment_method) == -1),
                    "have_due_amount": have_due_amount,
                    "due_amount": due_amount,
                    "two_factor_auth_done": bool(
                        two_factor_auth_done and two_factor_auth_done == YES
                    ),
                    "is_3ds_check_active": is_3ds_check_active,
                }
            )
        except Exception as error:
            print(
                "Internal server error in retrieve cards API for "
                + f"user with id ->{retrieve_customer_request.user.id}"
            )
            print(error)
            return SERVER_ERROR


class AddDefaultPaymentMethod(APIView):
    """add default payment method"""

    permission_classes = [IsAuthenticated]

    @classmethod
    def post(cls, add_default_payment_method):
        """add default paymennt method"""
        try:
            if not add_default_payment_method.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                add_default_payment_method.user.id,
                add_default_payment_method.auth,
            ):
                return MULTIPLE_LOGIN
            default_payment_method = add_default_payment_method.data.get(
                "default_payment_method", None
            )
            if default_payment_method is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": ("Default payment method not provided."),
                    }
                )
            customer_id = add_default_payment_method.user.get_customer_id()
            if not customer_id:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            "Not able to add default payment method "
                            + "because payment account is not created."
                        ),
                    }
                )

            prev_default_payment_method = (
                add_default_payment_method.user.user_profile.default_payment_method
            )
            if (
                prev_default_payment_method is not None
                and str(default_payment_method) == prev_default_payment_method
            ):
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            "Provided default payment method "
                            + "is already added as default."
                        ),
                    }
                )
            if int(default_payment_method) >= 0:
                cards_result = make_request(
                    GET_REQUEST,
                    f"/cards?customer_id={customer_id}&include_disabled=false",
                    add_default_payment_method.user.id,
                    module="Square retrieve user cards API",
                )
                if cards_result.status_code != 200:
                    return DATA_INVALID
                response_data = json.loads(cards_result.content)
                if "cards" not in response_data:
                    return DATA_NOT_FOUND
                if int(default_payment_method) >= len(response_data["cards"]):
                    return Response(
                        {
                            "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                            "status": False,
                            "message": "Not acceptable",
                        }
                    )
            default_payment_paln_updated = Profile.objects.filter(
                user=add_default_payment_method.user
            ).update(default_payment_method=str(default_payment_method))
            if not default_payment_paln_updated:
                return Response(
                    {
                        "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                        "status": False,
                        "message": ("Failed to add default payment method."),
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": (
                        "Default payment method " + "added successfully!"
                    ),
                }
            )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT


class RetrieveCustomerCardApi(APIView):
    """retrieve customer card"""

    permission_classes = [IsAuthenticated]

    @classmethod
    def get(cls, get_customer_card_request):
        """get customer card"""
        try:
            card_id = "ccof:SnL869XlkMCx4pMd3GB"
            customer_card = make_request(
                GET_REQUEST,
                f"/cards/{card_id}",
                get_customer_card_request.user.id,
                module="Square retrieve card details API",
            )
            if customer_card.status_code != 200:
                return DATA_INVALID
            card_data = json.loads(customer_card.content)
            if "card" in card_data:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "successfully loaded card \
                            data for a customer",
                        "data": {"carddata": card_data["card"]},
                    }
                )
            return DATA_INVALID
        except Exception as error:
            print(
                "Failed to get card for "
                + f"user with id ->{get_customer_card_request.user.id}"
                + "due to exception -> "
            )
            print(error)
            return SERVER_ERROR


class CreateCustomerCardApi(APIView):
    """create customer card api"""

    permission_classes = [IsAuthenticated]

    @classmethod
    def post(cls, create_customer_card_request):
        """create customer card with 3DS flow"""
        try:
            if not create_customer_card_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                create_customer_card_request.user.id,
                create_customer_card_request.auth,
            ):
                return MULTIPLE_LOGIN
            print(
                '***********create_customer_card_request cardDetails***********',
                create_customer_card_request.data["cardDetails"]
            )
            print(
                '***********create_customer_card_request is3DSAvailable***********',
                create_customer_card_request.data["is3DSAvailable"]
            )
            customer_id = create_customer_card_request.user.get_customer_id()
            create_customer_card_request.data["cardDetails"]["idempotency_key"] = str(uuid.uuid1())
            create_customer_card_request.data["cardDetails"]["card"]["customer_id"] = customer_id
            card_obj = create_customer_card_request.data["cardDetails"]
            if (
                create_customer_card_request.data and
                create_customer_card_request.data["is3DSAvailable"]
            ):
                print("******************* with 3DS *******************")
                card_obj["autocomplete"] = False
                card_obj["delay_duration"] = "PT2M"
                card_obj["delay_action"] = "CANCEL"
                print("************** Charge Card Object **************", card_obj)
                create_payment_result = make_request(
                    POST_REQUEST,
                    "/payments",
                    create_customer_card_request.user.id,
                    module="Square create payment API",
                    data=card_obj,
                )
                print("************Payment Response**********", create_payment_result.content)
                if create_payment_result.status_code != 200:
                    return Response(
                        {
                            "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                            "status": False,
                            "message": "Card owner verification unsuccessful.",
                        }
                    )
                if create_payment_result.status_code == 200:
                    print("ok")
                    payment_response = create_payment_result.json()
                    card_obj_2 = {
                        "source_id": payment_response["payment"]["id"],
                        "card": card_obj["card"],
                        "idempotency_key": card_obj["idempotency_key"],
                        "verification_token": card_obj["verification_token"]
                    }
                    print("************** Create Card Object **************", card_obj_2)
                    create_card_result = make_request(
                        POST_REQUEST,
                        "/cards",
                        create_customer_card_request.user.id,
                        data=card_obj_2,
                        module="Square create card API",
                    )
                    print("************Create card Response**********", create_card_result.content)


                    if create_card_result.status_code != 200:
                        return Response(
                            {
                                "status_code": status.HTTP_403_FORBIDDEN,
                                "status": False,
                                "message": "Invalid card data",
                            }
                        )
                    card_data = json.loads(create_card_result.content)
                    if "card" in card_data:
                        return Response(
                            {
                                "status_code": status.HTTP_200_OK,
                                "status": True,
                                "message": "Successfully added customer card with 3DS flow",
                            }
                        )
                    return Response(
                        {
                            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "status": False,
                            "message": "Something went wrong",
                        }
                    )
                return Response(
                    {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "status": False,
                        "message": "Something went wrong",
                    }
                )
            print("******************* without 3DS *******************")
            card_obj = create_customer_card_request.data["cardDetails"]
            create_card_result = make_request(
                POST_REQUEST,
                "/cards",
                create_customer_card_request.user.id,
                data=card_obj,
                module="Square create card API",
            )
            print("************Create card Response**********", create_card_result.content)
            if create_card_result.status_code != 200:
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": "Invalid card data",
                    }
                )
            card_data = json.loads(create_card_result.content)
            if "card" in card_data:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "Successfully added customer card",
                    }
                )
            return Response(
                    {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "status": False,
                        "message": "Something went wrong",
                    }
                )
        except Exception as error:
            print(
                "Internal server error in create card API for "
                + f"user with id ->{create_customer_card_request.user.id}"
            )
            print(error)
            return SERVER_ERROR



class DisableCustomerApi(APIView):
    """disable customer card api"""

    permission_classes = [IsAuthenticated]

    @classmethod
    def delete(cls, disable_request):
        """delete customer card"""
        try:
            if not disable_request.auth:
                return UNAUTHORIZED
            if not handle_concurrent_user_login(
                disable_request.user.id, disable_request.auth
            ):
                return MULTIPLE_LOGIN
            card_id = disable_request.data["card_id"]
            card_index = disable_request.data["card_index"]
            default_payment_method = (
                disable_request.user.user_profile.default_payment_method
            )
            if default_payment_method is None:
                default_payment_method = 0
            else:
                default_payment_method = int(default_payment_method)
            if card_index <= default_payment_method:
                Profile.objects.filter(user_id=disable_request.user).update(
                    default_payment_method= (
                        str(default_payment_method - 1)
                        if card_index != default_payment_method
                        else 0
                    )
                )
            disable_result = make_request(
                POST_REQUEST,
                f"/cards/{card_id}/disable",
                disable_request.user.id,
                None,
                "Square disable card API",
            )
            if disable_result.status_code != 200:
                return DATA_INVALID
            if "card" in json.loads(disable_result.content):
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "successfully disabled card",
                    }
                )
            return DATA_INVALID
        except Exception as error:
            print(
                "Failed to disable card for "
                + f"user with id ->{disable_request.user.id}"
                + "due to exception -> "
            )
            print(error)
            return SERVER_ERROR



class CreateCustomerCardApiV4(APIView):
    """create customer card api"""

    permission_classes = [IsAuthenticated]

    @classmethod
    def post(cls, create_customer_card_request):
        """create customer card with 3DS flow"""
        try:
            if not create_customer_card_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                create_customer_card_request.user.id,
                create_customer_card_request.auth,
            ):
                return MULTIPLE_LOGIN
            print(
                '***********create_customer_card_request cardDetails***********',
                create_customer_card_request.data["cardDetails"]
            )
            print(
                '***********create_customer_card_request is3DSAvailable***********',
                create_customer_card_request.data["is3DSAvailable"]
            )
            print(
                '***********create_customer_card_request is3DSAvailable_with_billing***********',
                create_customer_card_request.data["is3DSAvailableWithBilling"]
            )
            customer_id = create_customer_card_request.user.get_customer_id()
            create_customer_card_request.data["cardDetails"]["idempotency_key"] = str(uuid.uuid1())
            create_customer_card_request.data["cardDetails"]["card"]["customer_id"] = customer_id
            card_obj = create_customer_card_request.data["cardDetails"]
            is_3ds_available_with_billing = create_customer_card_request.data["is3DSAvailableWithBilling"]
            if (
                create_customer_card_request.data and
                create_customer_card_request.data["is3DSAvailable"] and not is_3ds_available_with_billing 
            ):
                print("******************* with 3DS *******************")
                card_obj["autocomplete"] = False
                card_obj["delay_duration"] = "PT2M"
                card_obj["delay_action"] = "CANCEL"
                print("************** Charge Card Object **************", card_obj)
                create_payment_result = make_request(
                    POST_REQUEST,
                    "/payments",
                    create_customer_card_request.user.id,
                    module="Square create payment API",
                    data=card_obj,
                )
                print("************Payment Response**********", create_payment_result.content)
                if create_payment_result.status_code != 200:
                    return Response(
                        {
                            "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                            "status": False,
                            "message": "Card owner verification unsuccessful.",
                        }
                    )
                if create_payment_result.status_code == 200:
                    print("ok")
                    payment_response = create_payment_result.json()
                    card_obj_2 = {
                        "source_id": payment_response["payment"]["id"],
                        "card": card_obj["card"],
                        "idempotency_key": card_obj["idempotency_key"],
                        "verification_token": card_obj["verification_token"]
                    }
                    print("************** Create Card Object **************", card_obj_2)
                    create_card_result = make_request(
                        POST_REQUEST,
                        "/cards",
                        create_customer_card_request.user.id,
                        data=card_obj_2,
                        module="Square create card API",
                    )
                    print("************Create card Response**********", create_card_result.content)


                    if create_card_result.status_code != 200:
                        return Response(
                            {
                                "status_code": status.HTTP_403_FORBIDDEN,
                                "status": False,
                                "message": "Invalid card data",
                            }
                        )
                    card_data = json.loads(create_card_result.content)
                    if "card" in card_data:
                        return Response(
                            {
                                "status_code": status.HTTP_200_OK,
                                "status": True,
                                "message": "Successfully added customer card with 3DS flow",
                            }
                        )
                    return Response(
                        {
                            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "status": False,
                            "message": "Something went wrong",
                        }
                    )
                return Response(
                    {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "status": False,
                        "message": "Something went wrong",
                    }
                )
            print("******************* with 3DS and without billing or without 3DS *******************")
            card_obj = create_customer_card_request.data["cardDetails"]
            if "amount_money" in card_obj:
                    del card_obj["amount_money"]
            print("************** Card Object **************", card_obj)
            create_card_result = make_request(
                POST_REQUEST,
                "/cards",
                create_customer_card_request.user.id,
                data=card_obj,
                module="Square create card API",
            )
            print("************Create card Response**********", create_card_result.content)
            if create_card_result.status_code != 200:
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": "Invalid card data",
                    }
                )
            card_data = json.loads(create_card_result.content)
            if "card" in card_data:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "Successfully added customer card",
                    }
                )
            return Response(
                    {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "status": False,
                        "message": "Something went wrong",
                    }
                )
        except Exception as error:
            print(
                "Internal server error in create card API for "
                + f"user with id ->{create_customer_card_request.user.id}"
            )
            print(error)
            return SERVER_ERROR

