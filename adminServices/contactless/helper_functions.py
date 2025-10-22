"""contact less helper functions"""
#  File details-
#   Author      - Vismay Raul
#   Description - This file contains helper functions for Contactless modules.
#   Name        - helper functions
#   Modified by - Vismay Raul

# These are all the imports that we are exporting from
# different module's from project or library.

import json
from datetime import datetime, timedelta
import pytz


import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import Timeout
from decouple import config

from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response

# pylint:disable=import-error
from sharedServices.model_files.config_models import BaseConfigurations

from sharedServices.contactless_common_functions import (
    get_payter_transactions_from_data_api,
)
from sharedServices.common import filter_function_for_base_configuration,base_configuration
from sharedServices.sentry_tracers import traced_request
from sharedServices.constants import (
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    REQUEST_API_TIMEOUT,
    PAYTER_DAILY_DATASET_SIZE,
    DEFAULT_PAYTER_DAILY_DATASET_SIZE,
    GET_REQUEST,
    POST_REQUEST,
)
from sharedServices.model_files.contactless_models import (
    ThirdPartyServicesData,
)

from .app_level_constants import (
    DRIIVZ,
    PAYTER,
    BILLING_PLAN_CODE,
    BILLING_PLAN_CODE_VALUE,
    DATE_FORMAT_FOR_DRIIVZ,
    SUCCESSFULLY_FETCHED_DATA,
    FAILED,
    COMPLETE,
)


def driivz_api(from_date, to_date):
    """driivz API to get sessions in time range"""
    try:
        response = traced_request(
            GET_REQUEST,
            (
                config("DJANGO_APP_DRIIVZ_BASE_URL")
                + "/api/transactions?date-from="
                + from_date
                + "&date-to="
                + to_date
            ),
            headers={
                "Content-Type": "application/json",
            },
            auth=HTTPBasicAuth(
                config("DJANGO_APP_DRIIVZ_ADMIN_USERNAME"),
                config("DJANGO_APP_DRIIVZ_ADMIN_PASSWORD"),
            ),
            timeout=REQUEST_API_TIMEOUT,
        )
        return response
    except (Timeout, requests.exceptions.ConnectionError, requests.exceptions.SSLError) as error:
        print("error", error)
        return None


def get_driivz_access_token_v2():
    base_url = config("DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL")
    url = f"{base_url}/api-gateway/v1/authentication/operator/login"
    payload = {
        "userName": config("DJANGO_APP_DRIIVZ_API_GATEWAY_ADMIN_USERNAME"),
        "password": config("DJANGO_APP_DRIIVZ_API_GATEWAY_ADMIN_PASSWORD"),
    }
    headers = {"Content-Type": "application/json"}
    response = traced_request(POST_REQUEST, url, headers=headers, data=json.dumps(payload))
    return response.json().get("data")[0].get("ticket")


def driivz_api_v2(from_date, to_date, charge_point_ids=None):
    """driivz API to get sessions in time range"""
    try:
        base_url = config("DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL")
        url = f"{base_url}/api-gateway/v1/ev-transactions/filter?pageSize=20000"
        payload = {
            "fromDate": from_date,
            "toDate": to_date
        }
        if charge_point_ids:
            payload["chargerIds"] = charge_point_ids
        headers = {"Content-Type": "application/json", "dmsTicket": base_configuration("driivz_access_token_v2")}
        response = traced_request(POST_REQUEST, url, headers=headers, data=json.dumps(payload), timeout=REQUEST_API_TIMEOUT)
        if response.status_code in [400, 403]:
            headers.update({"dmsTicket": base_configuration("driivz_access_token_v2",get_driivz_access_token_v2(),forceUpdate=True)})
            response = traced_request(POST_REQUEST, url, headers=headers, data=json.dumps(payload), timeout=REQUEST_API_TIMEOUT)
        return response.json().get("data")
    except (Timeout, requests.exceptions.ConnectionError, requests.exceptions.SSLError) as error:
        print("error", error)
        return None


def payter_api(start_date, end_date):
    """payter API to get sessions in time range"""
    payload = json.dumps(
        {
            "index": "Transactions",
            "maxResults": filter_function_for_base_configuration(
                PAYTER_DAILY_DATASET_SIZE,
                DEFAULT_PAYTER_DAILY_DATASET_SIZE,
            ),
            "sorts": [{"field": "txnTimestamp", "asc": False}],
            "filters": [
                {
                    "type": "range",
                    "field": "@timestamp",
                    "from": start_date,
                    "to": end_date,
                }
            ],
        }
    )
    response = get_payter_transactions_from_data_api(payload)
    if response.status_code == 401:
        response = get_payter_transactions_from_data_api(payload, True)
    return response


def save_data_to_database(date, source, response, data, name):
    """Saves the data coming from driivz or payter to database"""
    try:
        driivz_db = ThirdPartyServicesData.objects.filter(
            source=source, data_date__date=date.date()
        )
        if source == DRIIVZ:
            res = response.text
        else:
            res = response.reason
        if not driivz_db:
            ThirdPartyServicesData.objects.create(
                data_date=date.replace(tzinfo=pytz.UTC),
                source=source,
                data=(data if response.status_code == 200 else ""),
                status=(COMPLETE if response.status_code == 200 else FAILED),
                created_date=timezone.localtime(timezone.now()),
                updated_date=timezone.localtime(timezone.now()),
                updated_by=name,
                details=(
                    SUCCESSFULLY_FETCHED_DATA
                    if response.status_code == 200
                    else res
                ),
            )
        else:
            driivz_db.update(
                data_date=date.replace(tzinfo=pytz.UTC),
                source=source,
                data=(data if response.status_code == 200 else ""),
                status=(COMPLETE if response.status_code == 200 else FAILED),
                updated_date=timezone.localtime(timezone.now()),
                updated_by=name,
                details=(
                    SUCCESSFULLY_FETCHED_DATA
                    if response.status_code == 200
                    else res
                ),
            )
        return Response(
            {
                "status_code": status.HTTP_200_OK,
                "status": True,
                "message": "Data saved to database",
            }
        )
    except COMMON_ERRORS:
        return API_ERROR_OBJECT


def datewise_driivz_data(date, name):
    """saving date wise driivz data"""
    from_date = datetime.strftime(date, DATE_FORMAT_FOR_DRIIVZ)
    to_date = datetime.strftime(
        date + timedelta(days=1), DATE_FORMAT_FOR_DRIIVZ
    )
    response = driivz_api(from_date, to_date)
    if response.status_code == 200:
        driivz_response_data = json.loads(response.content)["transactions"]
        sessions = filter(
            lambda session: BILLING_PLAN_CODE in session
            and session[BILLING_PLAN_CODE] in BILLING_PLAN_CODE_VALUE,
            driivz_response_data,
        )
        data = json.dumps(list(sessions))
        save_data_to_database(date, DRIIVZ, response, data, name)
        return Response(
            {
                "status_code": status.HTTP_200_OK,
                "status": True,
                "message": "Data saved successfully in database",
            }
        )
    return Response(
        {
            "status_code": response.status_code,
            "status": False,
            "message": "Data saving failed",
        }
    )


def datewise_payter_data(date, name):
    """saves date wise payter data"""
    start_date = int((date.replace(tzinfo=pytz.UTC)).timestamp()) * 1000
    end_date = (
        int((date.replace(tzinfo=pytz.UTC) + timedelta(days=1)).timestamp())
        * 1000
    )
    response = payter_api(start_date, end_date)
    if response.status_code == 200:
        payter_response_data = json.loads(response.content)["documents"]
        data = json.dumps(payter_response_data)
        save_data_to_database(date, PAYTER, response, data, name)
        return Response(
            {
                "status_code": status.HTTP_200_OK,
                "status": True,
                "message": "Data saved successfully in database",
            }
        )
    return Response(
        {
            "status_code": response.status_code,
            "status": False,
            "message": "Data saving failed",
        }
    )


def return_invalid_source_response(*_):
    """this funtion returns response for invalid source"""
    return Response(
        {
            "status_code": status.HTTP_400_BAD_REQUEST,
            "status": False,
            "message": "No such source available.",
        }
    )


def thirdparty_api_selector(source, date, name):
    """this function calls thirdparty api of a perticular source"""
    switcher = {
        DRIIVZ: datewise_driivz_data,
        PAYTER: datewise_payter_data,
    }
    func = switcher.get(source, return_invalid_source_response)
    return func(date, name)
