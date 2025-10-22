# """orders apis"""
# # Date - 12/08/2021


# # File details-
# #   Author          - Manish Pawar
# #   Description     - This file is mainly focused on APIs related to customer.
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

# IDEMPOTENCY_KEY = str(uuid.uuid1())

# client = Client(
#     access_token=config("DJANGO_PAYMENT_ACCESS_TOKEN"),
#     environment=config("DJANGO_PAYMENT_ENV"),
# )
# orders_api = client.orders


# class CreateOrderApi(APIView):
#     """create order api"""

#     permission_classes = [IsAuthenticated]

#     @classmethod
#     def post(cls, create_order_request):
#         """create order"""
#         try:
#             body = create_order_request.data.get("carddata")
#             create_order_result = orders_api.create_order(body)
#             if create_order_result.is_success():
#                 if "order" in create_order_result.body:
#                     return Response(
#                         {
#                             "status_code": status.HTTP_200_OK,
#                             "status": True,
#                             "message": "Order created successfully",
#                             "data": {
#                                 "orderData": create_order_result.body["order"]
#                             },
#                         }
#                     )
#                 if create_order_result.is_error():
#                     return DATA_NOT_FOUND
#             if create_order_result.is_error():
#                 return DATA_INVALID
#             return SERVER_ERROR
#         except COMMON_ERRORS:
#             return API_ERROR_OBJECT
