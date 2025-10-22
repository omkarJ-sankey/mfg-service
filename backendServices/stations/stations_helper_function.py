"""stations helper function"""
# Date - 23/02/2023


# File details-
#   Author          - Vismay Raul
#   Description     - This file is contains helper functions for stations.
#   Name            - Station Helper Functions
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 19/06/2025


# These are all the imports that we are exporting from
# different module's from project or library.

import json
import requests
from django.utils import timezone
from requests.auth import HTTPBasicAuth
from requests.exceptions import Timeout
from decouple import config
from rest_framework import status


# pylint:disable=import-error
from sharedServices.sentry_tracers import traced_request
from sharedServices.constants import (
    REQUEST_API_TIMEOUT,
    GET_REQUEST,
    GET_SESSION_ENDPOINT,
    CONTENT_TYPE_HEADER_KEY,
    JSON_DATA,
    POST_REQUEST,
    EMSP_NAME,
    EMSP_ENDPOINT,
    OCPI_KEY,
)

from sharedServices.common import get_node_secret

from ..backend_app_constants import CURRENCY_SYMBOLS
from sharedServices.sentry_tracers import traced_request, traced_request_with_retries


def location_data_api(site_id):
    """driivz API to get site data"""
    try:
        token = get_node_secret()
        response = traced_request(
            GET_REQUEST,
            (
                EMSP_ENDPOINT
                + GET_SESSION_ENDPOINT
                + site_id
            ),
            headers={
                CONTENT_TYPE_HEADER_KEY: JSON_DATA,
                "Authorization": f"Token {token}"
            },
            timeout=REQUEST_API_TIMEOUT,
        )
        return response
    except (Timeout, requests.exceptions.ConnectionError, requests.exceptions.SSLError) as error:
        print("error", error)
        return None


def updating_tariff(driivz_data, cache_data):
    """function for comparing dynamic tariff from driivz and cache"""
    # gets connector and charge points id and index in object format

    # Getting the current day of week - current_date.today().weekday()
    # returns the day of week as a number.
    # eg - timezone.localtime(
    # timezone.now()).today().weekday() returns 6 for "sunday"
    day = timezone.localtime(timezone.now()).today().weekday()
    # Getting current time to make a comparison with station opening time.
    current_time = timezone.localtime(timezone.now()).strftime("%H:%M")
    # The following logic returns the opening status of station

    def checktiming(time_status):
        state = False
        if time_status == "24 hours":
            state = True
        elif time_status == "Closed":
            state = False
        else:
            if time_status[0:5] <= current_time <= time_status[6:11]:
                state = True
        return state

    # Here 6 means sunday and 5 means saturday. For more
    # info read aboove comments
    # in this function itself.
    if day == 5:
        open_now_status = checktiming(
            cache_data["working_hours_details"][0]["saturday"]
        )
    elif day == 6:
        open_now_status = checktiming(cache_data["working_hours_details"][0]["sunday"])
    else:
        open_now_status = checktiming(
            cache_data["working_hours_details"][0]["monday_friday"]
        )
    cache_data.update({"open_now": open_now_status})

    cache_charge_points = {}
    for charge_point in cache_data["charge_points"]:
        if charge_point["connectors"]:
            connector_index = {}
            for connector in charge_point["connectors"]:
                connector_index[connector["connector_id"]] = charge_point[
                    "connectors"
                ].index(connector)
                cache_charge_points[charge_point["charger_point_id"]] = {
                    "cp_index": cache_data["charge_points"].index(charge_point),
                    "connector_index": connector_index,
                    "connectors": charge_point["connectors"],
                }

    # comparing tariff data and tariff currency coming from cache and driivz
    # and updating cache data if the value differs and returns the updated data
    driivz_data_object = json.loads(driivz_data)
    if "stations" in driivz_data_object:
        for chargepoint_id in driivz_data_object["stations"]:
            if (
                "id" in chargepoint_id
                and "evses" in chargepoint_id
                and str(chargepoint_id["id"]) in cache_charge_points
            ):
                for connector in chargepoint_id["evses"]:
                    if (
                        (
                            "connectors" in connector
                            and connector["connectors"]
                            and "id" in connector["connectors"][0]
                            and "price" in connector["connectors"][0]
                        )
                        and (
                            f'{connector["connectors"][0]["id"]}'
                            in cache_charge_points[f'{chargepoint_id["id"]}'][
                                "connector_index"
                            ]
                        )
                        and (
                            "kwh" in connector["connectors"][0]["price"]
                            and "currency" in connector["connectors"][0]["price"]
                        )
                        and (
                            (
                                cache_charge_points[f'{chargepoint_id["id"]}'][
                                    "connectors"
                                ][
                                    cache_charge_points[f'{chargepoint_id["id"]}'][
                                        "connector_index"
                                    ][f'{connector["connectors"][0]["id"]}']
                                ][
                                    "tariff_amount"
                                ]
                                != connector["connectors"][0]["price"]["kwh"]
                            )
                            or (
                                cache_charge_points[f'{chargepoint_id["id"]}'][
                                    "connectors"
                                ][
                                    cache_charge_points[f'{chargepoint_id["id"]}'][
                                        "connector_index"
                                    ][f'{connector["connectors"][0]["id"]}']
                                ][
                                    "tariff_currency"
                                ][
                                    :3
                                ]
                                != connector["connectors"][0]["price"]["currency"]
                            )
                        )
                    ):
                        cache_data["charge_points"][
                            cache_charge_points[f'{chargepoint_id["id"]}']["cp_index"]
                        ]["connectors"][
                            cache_charge_points[f'{chargepoint_id["id"]}'][
                                "connector_index"
                            ][f'{connector["connectors"][0]["id"]}']
                        ].update(
                            {
                                "tariff_amount": connector["connectors"][0]["price"][
                                    "kwh"
                                ],
                                "tariff_currency": connector["connectors"][0]["price"][
                                    "currency"
                                ]
                                + CURRENCY_SYMBOLS[
                                    connector["connectors"][0]["price"]["currency"]
                                ],
                            }
                        )
    return cache_data



def emsp_cron_function(cpo_names,token,endpoint):
    results=[]
    for cpo in cpo_names:
        if cpo.lower() == EMSP_NAME:
            continue
        ocpi_data = {
            OCPI_KEY:cpo
        }
        response=traced_request_with_retries(
            POST_REQUEST,
            EMSP_ENDPOINT + endpoint,
            headers={
                CONTENT_TYPE_HEADER_KEY: JSON_DATA,
                "Authorization": f"Token {token}"
            },
            data=json.dumps(ocpi_data),
            timeout=REQUEST_API_TIMEOUT,
        )
        # if response is not None and response.status_code == status.HTTP_201_CREATED and json.loads(response.content.decode())["status_code"]==status.HTTP_200_OK:
        if response is not None and response.status_code == status.HTTP_201_CREATED :
            results.append({"cpo": cpo, "status": "success"})
        else:
            results.append({"cpo": cpo, "status": "failed", "code": response.status_code, "error": getattr(response, "text", "")})
    return results

