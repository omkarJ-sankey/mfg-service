"""payment apis"""
# Date - 12/08/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on APIs related to customer.
#   Name            - Cards API
#   Modified by     - Manish Pawar
#   Modified date   - 12/08/2021


# These are all the imports that we are exporting from
# different module's from project or library.

import uuid
import json
# from decouple import config
# from square.client import Client

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated


from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

# pylint:disable=import-error
from sharedServices.constants import SUCCESS_PAYMENT
from sharedServices.model_files.station_models import Stations
from sharedServices.model_files.transaction_models import Transactions
from sharedServices.model_files.charging_session_models import ChargingSession
from sharedServices.payments_helper_function import make_request
from sharedServices.common import array_to_string_converter
from sharedServices.constants import (
    PUT_REQUEST,
    POST_REQUEST,
    GET_REQUEST
)
from backendServices.backend_app_constants import (
    DATA_NOT_FOUND,
    DATA_INVALID,
    SERVER_ERROR
)
IDEMPOTENCY_KEY = str(uuid.uuid1())

# client = Client(
#     access_token=config("DJANGO_PAYMENT_ACCESS_TOKEN"),
#     environment=config("DJANGO_PAYMENT_ENV"),
     
# )

# payments_api = client.payments


class CustomerPaymentListAPI(APIView):
    """get customer payment list api"""

    permission_classes = [IsAuthenticated]
    @classmethod
    def get(cls, list_payments_request):
        """get customer payment list"""
        try:
            list_payment_result = make_request(
                GET_REQUEST,
                f'/payments',
                list_payments_request.user.id,
                module="Square list payments API"
            )
            if list_payment_result.status_code != 200:
                return DATA_INVALID
            payments_data = json.loads(list_payment_result.content)
            if "payments" in payments_data:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "successfully loaded \
                            payments for all customers",
                        "data": {"cardsdata": \
                            payments_data["payments"]},
                    }
                )
            return DATA_INVALID
        except Exception as error:
            print(
                f"Failed to fetch payments for "
                + f"user with id ->{list_payments_request.user.id}"
                + "due to exception -> "
            )
            print(error)
            return SERVER_ERROR


class RetrieveCustomerPaymentApi(APIView):
    """retrieve customer payment  api"""
    permission_classes = [IsAuthenticated]
    @classmethod
    def get(cls, retrieve_customer_payment_request):
        """retrieve customer payment"""
        try:
            payment_id = retrieve_customer_payment_request.\
                data.get("payment_id")
            
            retrieve_payments_result = make_request(
                GET_REQUEST,
                f'/payments/{payment_id}',
                retrieve_customer_payment_request.user.id,
                module="Square get payment details API"
            )

            retrieve_payments_result = make_request(
                GET_REQUEST,
                f"/payments/{payment_id}",
                retrieve_customer_payment_request.user.id,
                module="Square get payment details API",
            )
            if retrieve_payments_result.status_code != 200:
                return DATA_INVALID
            payment_data = json.loads(retrieve_payments_result.content)
            if "payment" in payment_data:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "successfully loaded cards for a customer",
                        "data": {
                            "customercardsdata":payment_data["payment"]
                        },
                    }
                )
            return DATA_NOT_FOUND
        except Exception as error:
            print(
                f"Failed to fetch payment details for "
                + f"user with id ->{retrieve_customer_payment_request.user.id}"
                + "due to exception -> "
            )
            print(error)
            return SERVER_ERROR


class CreateCustomerPaymentApi(APIView):
    """create customer payment  api"""

    permission_classes = [IsAuthenticated]
    @classmethod
    def post(cls, create_payment_request):
        """create customer payment"""
        try:
            pay_body = create_payment_request.data.get("carddata")
            idempotency_key = str(uuid.uuid1())
            customer_id = create_payment_request.user.get_customer_id()
            pay_body["customer_id"] = customer_id
            pay_body["idempotency_key"] = idempotency_key
            pay_body["autocomplete"] = False
            create_payment_result = make_request(
                POST_REQUEST,
                f"/payments",
                create_payment_request.user.id,
                data=pay_body,
                module="Square create payment API",
            )
            if create_payment_result.status_code != 200:
                return DATA_INVALID
            payment_data = json.loads(create_payment_result.content)
            if "payment" in payment_data:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": SUCCESS_PAYMENT,
                        "data": {
                            "customersdata": payment_data["payment"]},
                    }
                )
            return SERVER_ERROR
        except Exception as error:
            print(
                "Internal server error in create payment API for "+
                f"user with id ->{create_payment_request.user.id}"
            )
            print(error)
            return SERVER_ERROR


class UpdateCustomerPaymentApi(APIView):
    """update customer payment  api"""
    permission_classes = [IsAuthenticated]
    @classmethod
    def post(cls, update_payment_request):
        """update customer payment"""
        try:
            req_body = update_payment_request.data.get("payment_info")
            payment_id = req_body["payment_id"]
            update_body = {}
            update_body["payment"] = req_body["payment"]
            update_body["idempotency_key"] = str(uuid.uuid1())
            update_payment_result = make_request(
                PUT_REQUEST,
                f"/payments/{payment_id}",
                update_payment_request.user.id,
                data=update_body,
                module="Square update payment API",
            )
            if update_payment_result.status_code != 200:
                return DATA_NOT_FOUND
            update_payment_data = json.loads(update_payment_result)
            if "payment" in update_payment_data:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": SUCCESS_PAYMENT,
                        "data": {"customersdata": update_payment_data},
                    }
                )
            return DATA_NOT_FOUND
        except Exception as error:
            print(
                f"Failed to update payment details for "
                + f"user with id ->{update_payment_request.user.id}"
                + "due to exception -> "
            )
            print(error)
            return SERVER_ERROR


class CancelCustomerPaymentApi(APIView):
    """cancel customer payment  api"""
    permission_classes = [IsAuthenticated]
    @classmethod
    def post(cls, cancel_payment_request):
        """cancel customer payment"""
        try:
            payment_id = cancel_payment_request.data.get("payment_id")
            cancel_payment_result = make_request(
                POST_REQUEST,
                f'/payments/{payment_id}/cancel',
                cancel_payment_request.user.id,
                module="Square cancel payment API"
            )
            if cancel_payment_result.status_code != 200:
                return DATA_INVALID
            payment_data = json.loads(cancel_payment_result.content)
            if "payment" in payment_data:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "successfully canceled payment",
                        "data": {
                            "customersdata":\
                                payment_data["payment"]},
                    }
                )
            return DATA_INVALID
        except Exception as error:
            print(
                f"Failed to cancel payment for "
                + f"user with id ->{cancel_payment_request.user.id}"
                + "due to exception -> "
            )
            print(error)
            return SERVER_ERROR


class CompleteCustomerPaymentApi(APIView):
    """complete customer payment  api"""
    permission_classes = [IsAuthenticated]
    @classmethod
    def post(cls, complete_payment_request):
        """complete customer payment"""
        try:
            body = complete_payment_request.data.get("payment_id")
            station_id = complete_payment_request.data.get("station_id", None)
            station = None
            try:
                station = Stations.objects.get(station_id=station_id)
            except ObjectDoesNotExist:
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": "invalid station data provided.",
                    }
                )
            complete_payment_result = make_request(
                POST_REQUEST,
                f'payments/{body}/complete',
                complete_payment_request.user.id,
                module="Square complete payment API"
            )
            if complete_payment_result.status_code != 200:
                return DATA_INVALID
            payment_data = json.loads(complete_payment_result.content)
            if "payment" in payment_data:
                data = payment_data["payment"]

                # checking any charging session for partcular
                # payment_id is available or not.
                charging_session = ChargingSession.objects.filter(
                    payment_id=body
                )
                if charging_session.first():
                    charging_session.update(paid_status="paid")
                if station:
                    Transactions.objects.create(
                        station_id=station,
                        payment_id=data["id"],
                        order_id=data["order_id"],
                        transaction_id=data["order_id"],
                        transaction_amount=data["total_money"]["amount"],
                        transaction_currency=data["total_money"]["currency"],
                        customer_id=data["customer_id"],
                        created_date=timezone.now(),
                        payment_response=array_to_string_converter([payment_data]),
                    )
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": SUCCESS_PAYMENT,
                        "data": {
                            "customersdata": \
                                payment_data["payment"]},
                    }
                )
            return DATA_INVALID
        except Exception as error:
            print(
                f"Failed to complete payment for "
                + f"user with id ->{complete_payment_request.user.id}"
                + "due to exception -> "
            )
            print(error)
            return SERVER_ERROR
