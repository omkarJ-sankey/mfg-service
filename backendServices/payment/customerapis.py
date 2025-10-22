"""customer apis"""
# Date - 11/08/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on APIs related to customer.
#   Name            - Customer API
#   Modified by     - Manish Pawar
#   Modified date   - 12/08/2021


# These are all the imports that we are exporting from
# different module's from project or library.
import json
# from decouple import config
# from square.client import Client
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

# pylint:disable=import-error
from sharedServices.constants import SUCCESS_CUSTOMERS
from sharedServices.common import hasher
from sharedServices.model_files.app_user_models import MFGUserEV, Profile
from sharedServices.payments_helper_function import make_request
from sharedServices.constants import (
    POST_REQUEST,
    GET_REQUEST,
    PUT_REQUEST,
    DELETE_REQUEST
)

from backendServices.backend_app_constants import (
    DATA_NOT_FOUND,
    DATA_INVALID,
    SERVER_ERROR
)
# client = Client(
#     access_token=config("DJANGO_PAYMENT_ACCESS_TOKEN"),
#     environment=config("DJANGO_PAYMENT_ENV"),

# )

# customers_api = client.customers


class CustomerListApi(APIView):
    """customer list api"""
    permission_classes = [IsAuthenticated]
    @classmethod
    def get(cls, customer_list_request):
        """get customer list"""
        try:
            customers_result = make_request(
                GET_REQUEST,
                '/customers',
                customer_list_request.user.id,
                module="Square customer list API"
            )
            if customers_result.status_code != 200:
                return DATA_INVALID
            customers_data = json.loads(customers_result.content)
            if "customers" in customers_data:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": SUCCESS_CUSTOMERS,
                        "customersdata": customers_data["customers"],
                    }
                )
            return DATA_NOT_FOUND
        except Exception as error:
            print(
                "Failed to fetch customers for"
                + f"user with id ->{customer_list_request.user.id}"
                + "due to exception -> "
            )
            print(error)
            return SERVER_ERROR


class CreateCustomerApi(APIView):
    """create customer api"""

    permission_classes = [IsAuthenticated]
    @classmethod
    def post(cls, create_customer_request):
        """create customer api"""
        try:
            customer_req = create_customer_request
            create_customer_result = make_request(
                POST_REQUEST,
                '/customers',
                None,
                data=customer_req,
                module="Square create customer API"
            )
            if create_customer_result.status_code != 200:
                return DATA_INVALID
            customer_data = json.loads(create_customer_result.content)
            if "customer" in customer_data:
                MFGUserEV.objects.filter(
                    user_email=hasher(customer_req["email_address"])
                ).update(customer_id=customer_data["customer"]["id"])
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": SUCCESS_CUSTOMERS,
                        "customersdata": customer_data["customer"],
                    }
                )
            return DATA_INVALID
        except Exception as error:
            print(
                "Failed to create square account for"
                + f"user with id ->{create_customer_request.user.id}"
                + "due to exception -> "
            )
            print(error)
            return SERVER_ERROR


class UpdateCustomerApi(APIView):
    """update customer api"""
    permission_classes = [IsAuthenticated]
    @classmethod
    def post(cls, update_customer_request):
        """update customer"""
        try:
            customer_id = update_customer_request.data.get("customer_id")
            body = update_customer_request.data.get("customerdata")
            customer_result = make_request(
                PUT_REQUEST,
                f'/customers/{customer_id}',
                update_customer_request.user.id,
                data=body,
                module="Square update customer API"
            )
            if customer_result.status_code != 200:
                return DATA_INVALID
            customer_data = json.loads(customer_result.content)
            if "customer" in customer_data:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": SUCCESS_CUSTOMERS,
                        "customersdata": customer_data["customer"],
                    }
                )
            return DATA_NOT_FOUND
        except Exception as error:
            print(
                "Failed to update square account for "
                + f"user with id ->{update_customer_request.user.id}"
                + "due to exception -> "
            )
            print(error)
            return SERVER_ERROR


class RetrieveCustomerApi(APIView):
    """retrieve customer"""
    permission_classes = [IsAuthenticated]
    @classmethod
    def get(cls, retrieve_customer_request):
        """get customer"""
        try:
            customer_id = retrieve_customer_request.data.get("customer_id")
            retrieve_customer = make_request(
                GET_REQUEST,
                f'/customers/{customer_id}',
                retrieve_customer_request.user.id,
                module="Square get customer details API"
            )
            if retrieve_customer.status_code != 200:
                return DATA_INVALID
            customer_data = json.loads(retrieve_customer.content)
            if "customer" in customer_data:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": SUCCESS_CUSTOMERS,
                        "data": {"customersdata": customer_data["customer"]},
                    }
                )
            return DATA_INVALID
        except Exception as error:
            print(
                "Failed retrieve square account for "
                + f"user with id ->{retrieve_customer_request.user.id}"
                + "due to exception -> "
            )
            print(error)
            return SERVER_ERROR


class DeleteCustomerApi(APIView):
    """delete customer api"""

    permission_classes = [IsAuthenticated]
    @classmethod
    def delete(cls, customer_delete_request):
        """delete customer"""
        try:
            customer_id = customer_delete_request.data.get("customer_id")
            delete_result = make_request(
                DELETE_REQUEST,
                f"/customers/{customer_id}",
                customer_delete_request.user.id,
                module="Square delete customer details API",
            )
            if delete_result.status_code != 200:
                return DATA_INVALID
            Profile.objects.filter(user=customer_delete_request.user).update(
                customer_id=None
            )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Customer deleted successfully",
                }
            )
        except Exception as error:
            print(
                "Failed to delete square account for "
                + f"user with id ->{customer_delete_request.user.id}"
                + "due to exception -> "
            )
            print(error)
            return SERVER_ERROR
