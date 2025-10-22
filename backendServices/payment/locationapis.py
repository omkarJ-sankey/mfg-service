# """location apis"""
# # Date - 17/08/2021

# # File details-
# #   Author          - Manish Pawar
# #   Description     - This file is mainly focused on APIs related to locations.
# #   Name            - Cards API
# #   Modified by     - Manish Pawar
# #   Modified date   - 17/08/2021


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

# locations_api = client.locations


# class ListLocationsApi(APIView):
#     """llocation list api"""

#     permission_classes = [IsAuthenticated]

#     @classmethod
#     def get(cls, _):
#         """get loaction list"""
#         try:
#             list_loc_result = locations_api.list_locations()
#             if list_loc_result.is_success():
#                 if "locations" in list_loc_result.body:
#                     return Response(
#                         {
#                             "status_code": status.HTTP_200_OK,
#                             "status": True,
#                             "message": "successfully loaded all locations",
#                             "data": {
#                                 "locations": list_loc_result.body["locations"]
#                             },
#                         }
#                     )
#                 if list_loc_result.is_error():
#                     return DATA_NOT_FOUND
#             if list_loc_result.is_error():
#                 return DATA_INVALID
#             return SERVER_ERROR
#         except COMMON_ERRORS:
#             return API_ERROR_OBJECT


# class RetrieveLocationApi(APIView):
#     """retrieve location api"""

#     permission_classes = [IsAuthenticated]

#     @classmethod
#     def get(cls, retrieve_loc_request):
#         """retrieve location API"""
#         try:
#             list_locations_response = ListLocationsApi.get(
#                 retrieve_loc_request
#             )
#             location_id = list_locations_response.data["data"]["locations"][0][
#                 "id"
#             ]
#             retrieve_loc_result = locations_api.retrieve_location(location_id)
#             if retrieve_loc_result.is_success():
#                 if "location" in retrieve_loc_result.body:
#                     return Response(
#                         {
#                             "status_code": status.HTTP_200_OK,
#                             "status": True,
#                             "message": "successfully loaded location",
#                             "data": {
#                                 "customercardsdata": retrieve_loc_result.body[
#                                     "location"
#                                 ]
#                             },
#                         }
#                     )
#                 if retrieve_loc_result.is_error():
#                     return DATA_NOT_FOUND
#             if retrieve_loc_result.is_error():
#                 return DATA_INVALID
#             return SERVER_ERROR
#         except COMMON_ERRORS:
#             return API_ERROR_OBJECT


# class CreateLocationApi(APIView):
#     """create location api"""

#     permission_classes = [IsAuthenticated]

#     @classmethod
#     def post(cls, create_location_request):
#         """create location"""
#         try:
#             body = create_location_request.data.get("carddata")
#             create_loc_result = locations_api.create_location(body)
#             if create_loc_result.is_success():
#                 if "location" in create_loc_result.body:
#                     return Response(
#                         {
#                             "status_code": status.HTTP_200_OK,
#                             "status": True,
#                             "message": "successfully added location",
#                             "data": {
#                                 "customersdata": create_loc_result.body[
#                                     "location"
#                                 ]
#                             },
#                         }
#                     )
#                 if create_loc_result.is_error():
#                     return DATA_NOT_FOUND
#             if create_loc_result.is_error():
#                 return DATA_INVALID
#             return SERVER_ERROR
#         except COMMON_ERRORS:
#             return API_ERROR_OBJECT
