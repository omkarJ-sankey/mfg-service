# """tranaction apis"""
# # Date - 12/08/2021


# # File details-
# #   Author          - Manish Pawar
# #   Description     - This file is mainly focused on APIs
# #                       related to transaction.
# #   Name            - Cards API
# #   Modified by     - Manish Pawar
# #   Modified date   - 12/08/2021

# # These are all the imports that we are exporting from
# # different module's from project or library.
# # pylint:disable=import-error
# import uuid
# from decouple import config

# from square.client import Client

# from rest_framework import status
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated
# from sharedServices.constants import COMMON_ERRORS, API_ERROR_OBJECT
# from backendServices.backend_app_constants import (
#     DATA_NOT_FOUND,
#     DATA_INVALID,
#     SERVER_ERROR,
# )
# from .app_level_constants import LOCATION_ID

# IDEMPOTENCY_KEY = str(uuid.uuid1())

# client = Client(
#     access_token=config("DJANGO_PAYMENT_ACCESS_TOKEN"),
#     environment=config("DJANGO_PAYMENT_ENV"),
# )

# transactions_api = client.transactions

# body = {}

# TRANSACTION_ID = "C0ZJVK3jtJReFYQK90vujwJJ84CZY"


# class TransactionsListAPI(APIView):
#     """transactions list api"""

#     permission_classes = [IsAuthenticated]

#     @classmethod
#     def get(cls, _):
#         """fetching transaction list with get request"""
#         try:
#             list_transaction_result = transactions_api.list_transactions(
#                 LOCATION_ID
#             )
#             if (
#                 list_transaction_result.is_success() and
#                 "transactions" in list_transaction_result.body
#             ):
#                 return Response(
#                     {
#                         "status_code": status.HTTP_200_OK,
#                         "status": True,
#                         "message": "successfully loaded data \
#                             for all transactions",
#                         "data": {
#                             "transactionsdata": (
#                                 list_transaction_result.body["transactions"]
#                             )
#                         },
#                     }
#                 )
#             if list_transaction_result.is_error():
#                 return DATA_INVALID
#             return SERVER_ERROR
#         except COMMON_ERRORS:
#             return API_ERROR_OBJECT


# class RetrieveTransactionAPI(APIView):
#     """retrieve transactions"""

#     permission_classes = [IsAuthenticated]

#     @classmethod
#     def get(cls, _):
#         """get request to retrieve transactions"""
#         try:
#             retrieve_transaction_result = (
#                 transactions_api.retrieve_transaction(
#                     LOCATION_ID, TRANSACTION_ID
#                 )
#             )
#             if retrieve_transaction_result.is_success():
#                 if "transaction" in retrieve_transaction_result.body:
#                     return Response(
#                         {
#                             "status_code": status.HTTP_200_OK,
#                             "status": True,
#                             "message": "successfully loaded data\
#                                 for a transaction",
#                             "data": {
#                                 "transactiondata": (
#                                     retrieve_transaction_result.body[
#                                         "transaction"
#                                     ]
#                                 )
#                             },
#                         }
#                     )
#                 if retrieve_transaction_result.is_error():
#                     return DATA_NOT_FOUND
#             if retrieve_transaction_result.is_error():
#                 return DATA_INVALID
#             return SERVER_ERROR
#         except COMMON_ERRORS:
#             return API_ERROR_OBJECT
