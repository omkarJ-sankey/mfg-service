"""Station APIs"""

#  File details-
#   Author      - Manish Pawar
#   Description - This file contains APIs for stations cronjob module.
#   Name        - Store chargepoint manufacturer cronjob
#   Modified by - Manish Pawar

# These are all the imports that we are exporting from
# different module's from project or library.
import math
import threading
import json
from passlib.hash import django_pbkdf2_sha256 as handler
from decouple import config

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

#pylint:disable=import-error
from sharedServices.model_files.station_models import ChargePoint
from sharedServices.driivz_api_gateway_functions import (
    get_driivz_api_gateway_dms_ticket
)
from sharedServices.sentry_tracers import traced_request
from sharedServices.constants import (
    DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    REQUEST_API_TIMEOUT,
    NO,
    GET_REQUEST,
)
from .app_level_constants import (
    DRIIVZ_PAGINATION_PAGE_SIZE,
    DRIIVZ_PAGINATION_FIRST_PAGE_INDEX,
    DRIIVZ_FETCH_CHARGER_MODELS_ENDPOINT,
    DRIIVZ_FETCH_CHARGERS_ENDPOINT
)


def driivz_fetch_records_api_call(page_size, page_number, endpoint):
    """this function returns transaction details
    for particular transaction"""
    auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket()
    if auth_response is not None and auth_response.status_code != 200:
        return None
    session_data_response = traced_request(
        GET_REQUEST,
        (
            config(
                "DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL"
            ) + endpoint
            + f"?pageSize={page_size}&pageNumber={page_number}&sortBy=id:asc"
        ),
        headers={
            "Content-Type": "application/json",
            "dmsTicket": dms_ticket
        },
        timeout=REQUEST_API_TIMEOUT,
        data=json.dumps({})
    )
    if session_data_response.status_code == 403:
        auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket(
            generate_token=True
        )
        if auth_response is not None and auth_response.status_code != 200:
            return None
        session_data_response = traced_request(
            GET_REQUEST,
            (
                config(
                    "DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL"
                ) + endpoint
                + f"?pageSize={page_size}&pageNumber={page_number}&sortBy=id:asc"
            ),
            headers={
                "Content-Type": "application/json",
                "dmsTicket": dms_ticket
            },
            timeout=REQUEST_API_TIMEOUT,
        )
    return session_data_response


def driivz_pagination_api_calls(
    driivz_pagination_page_size,
    driivz_pagination_first_page_index,
    endpoint
):
    """this function gets all charging models"""
    first_page_data = driivz_fetch_records_api_call(
        driivz_pagination_page_size,
        driivz_pagination_first_page_index,
        endpoint
    )
    all_models = []
    if first_page_data.status_code == 200:
        first_page_response = json.loads(first_page_data.content)
        all_models = first_page_response["data"]
        if first_page_response["count"] > DRIIVZ_PAGINATION_PAGE_SIZE:
            loop_range = range(
                1,
                math.ceil(first_page_response["count"]/DRIIVZ_PAGINATION_PAGE_SIZE)
            )
            for page_index in loop_range:
                other_page_data = driivz_fetch_records_api_call(
                    driivz_pagination_page_size,
                    page_index,
                    endpoint
                )
                if other_page_data.status_code == 200:
                    all_models = all_models + json.loads(other_page_data.content)["data"]
        return all_models
    return None


def store_chargepoint_manufactures():
    """this function stores the chargepoint manufacturers by fetching data from DRIIVZ"""
    charging_models = driivz_pagination_api_calls(
        DRIIVZ_PAGINATION_PAGE_SIZE,
        DRIIVZ_PAGINATION_FIRST_PAGE_INDEX,
        DRIIVZ_FETCH_CHARGER_MODELS_ENDPOINT
    )
    if charging_models:
        model_manufacturers = {}
        for model in charging_models:
            model_manufacturers[model['id']] = model["manufacturerCompany"]["name"]
        chargers = driivz_pagination_api_calls(
            DRIIVZ_PAGINATION_PAGE_SIZE,
            DRIIVZ_PAGINATION_FIRST_PAGE_INDEX,
            DRIIVZ_FETCH_CHARGERS_ENDPOINT
        )
        if chargers:
            charger_manufacturers = {}
            for charger in chargers:
                charger_manufacturers[charger["id"]] = model_manufacturers[charger["modelId"]]

            db_chargers = ChargePoint.objects.filter(
                deleted=NO
            )
            for db_charger in db_chargers:
                db_charger.manufacturer = charger_manufacturers[int(db_charger.charger_point_id)]

            ChargePoint.objects.bulk_update(db_chargers, ['manufacturer'])


class StoreChargePointManufacturerCronjob(APIView):
    """to trigger the store chargepoint manufacturers cronjob"""

    @classmethod
    def post(cls, cron_job_request):
        try:
            secret_key_azure = cron_job_request.data.get("secret_key", None)
            if secret_key_azure is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Secret key not provided.",
                    }
                )
            if not handler.verify(
                secret_key_azure, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
            ):
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Secret key is not valid.",
                    }
                )

            start_time = threading.Thread(
                target=store_chargepoint_manufactures,
                daemon=True
            )
            start_time.start()

            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Cron job initiated.",
                }
            )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT
