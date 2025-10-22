"""DRIIVZ common API functions"""
# Date - 22/11/2024


# File details-
#   Author          - Manish Pawar
#   Description     - This file contains DRIIVZ common API call functions
#   Name            - DRIIVZ common API functions
#   Modified by     - Manish Pawar
#   Modified date   - 22/11/2024


# These are all the imports that we are exporting from different
# module's from project or library.
import json
# from decimal import Decimal, ROUND_HALF_UP
from decouple import config

from django.utils import timezone

# pylint:disable=import-error
from sharedServices.model_files.config_models import BaseConfigurations
from sharedServices.sentry_tracers import traced_request
from sharedServices.constants import (
    REQUEST_API_TIMEOUT,
    DRIIVZ_DMS_TOKEN,
    POST_REQUEST,
    # WEKK_DAYS_DATA
)


def driivz_operator_auth_api_call():
    """this function fetches the operator login token from DRIIVZ"""
    return traced_request(
        POST_REQUEST,
        config(
            "DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL"
        ) + "/api-gateway/v1/authentication/operator/login",
        headers={
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "userName": config("DJANGO_APP_DRIIVZ_API_GATEWAY_ADMIN_USERNAME"),
            "password": config("DJANGO_APP_DRIIVZ_API_GATEWAY_ADMIN_PASSWORD")
        }),
        timeout=REQUEST_API_TIMEOUT,
    )


def get_driivz_api_gateway_dms_ticket(generate_token=False):
    """this function return driivz api gateway dms token"""
    dms_token = BaseConfigurations.objects.filter(
        base_configuration_key=DRIIVZ_DMS_TOKEN
    )
    if dms_token.first() and generate_token is False:
        return [None, dms_token.first().base_configuration_value]
    auth_response = driivz_operator_auth_api_call()
    dms_ticket = None
    if auth_response.status_code == 200:
        dms_ticket = json.loads(auth_response.content)['data'][0]['ticket']
        if dms_token.first() is None:
            BaseConfigurations.objects.create(
                base_configuration_key=DRIIVZ_DMS_TOKEN,
                base_configuration_name=DRIIVZ_DMS_TOKEN,
                base_configuration_value=dms_ticket,
                description="This is the DRIIVZ authentication token",
                for_app_version=4,
                created_date=timezone.localtime(timezone.now()),
                updated_date=timezone.localtime(timezone.now()),
            )
        else:
            BaseConfigurations.objects.filter(
                base_configuration_key=DRIIVZ_DMS_TOKEN
            ).update(
                base_configuration_value=dms_ticket,
                updated_date=timezone.localtime(timezone.now()),
            )
    return [auth_response, dms_ticket]


# def get_dynamic_tariffs():
#     """this function returns the tariff details"""
#     auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket()
#     if auth_response is not None and auth_response.status_code != 200:
#         return {
#             "endpoint": "/api-gateway/v1/authentication/operator/login",
#             "response": auth_response.content,
#         }
#     customer_tariffs = traced_request(
#         POST_REQUEST,
#         config(
#             "DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL"
#         ) + "/api-gateway/v1/customer-plans/MFG-Default-Plan/tariffs/charger-groups/all",
#         headers={
#             "Content-Type": "application/json",
#             "dmsTicket": dms_ticket
#         },
#         data=json.dumps({}),
#         timeout=REQUEST_API_TIMEOUT,
#     )
#     if customer_tariffs.status_code == 403:
#         auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket(generate_token=True)
#         if auth_response is not None and auth_response.status_code != 200:
#             return {
#                 "endpoint": "/api-gateway/v1/authentication/operator/login",
#                 "response": auth_response.content,
#             }
#         customer_tariffs = traced_request(
#             POST_REQUEST,
#             config(
#                 "DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL"
#             ) +"/api-gateway/v1/customer-plans/MFG-Default-Plan/tariffs/charger-groups/all",
#             headers={
#                 "Content-Type": "application/json",
#                 "dmsTicket": dms_ticket
#             },
#             data=json.dumps({}),
#             timeout=REQUEST_API_TIMEOUT,
#         )
#     if customer_tariffs.status_code != 200:
#         return None
#     customer_tariffs_object = {
#         customer_tariff["id"]: Decimal(
#             customer_tariff["firstLevelPeriod"]["kwhRate"]
#         ).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
#         for customer_tariff in json.loads(customer_tariffs.content)["data"]
#     }
#     get_charger_tariffs_response = traced_request(
#         GET_REQUEST,
#         config(
#             "DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL"
#         ) + "/api-gateway/v1/customer-plans/MFG-Default-Plan/tariffs/charger-groups/all",
#         headers={
#             "Content-Type": "application/json",
#             "dmsTicket": dms_ticket
#         },
#         timeout=REQUEST_API_TIMEOUT,
#     )
#     if get_charger_tariffs_response.status_code == 403:
#         auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket(generate_token=True)
#         if auth_response is not None and auth_response.status_code != 200:
#             return {
#                 "endpoint": "/api-gateway/v1/authentication/ope rator/login",
#                 "response": auth_response.content,
#             }
#         get_charger_tariffs_response = traced_request(GET_REQUEST,
#             config(
#                 "DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL"
#             ) +"/api-gateway/v1/customer-plans/MFG-Default-Plan/tariffs/charger-groups/all",
#             headers={
#                 "Content-Type": "application/json",
#                 "dmsTicket": dms_ticket
#             },
#             timeout=REQUEST_API_TIMEOUT,
#         )
#     if get_charger_tariffs_response.status_code != 200:
#         return None
#     get_charger_tariffs_response_data = json.loads(get_charger_tariffs_response)["data"]

#     for dynamic_tariff_group in get_charger_tariffs_response_data:


def driivz_fetch_dynamic_tariff_details(
    connector_id,
    driivz_account_number,
    driivz_account_card_number
):
    """this function returns transaction details
    for particular transaction"""
    auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket()
    if auth_response is not None and auth_response.status_code != 200:
        return None
    tariff_data_response = traced_request(POST_REQUEST,
        (
            config(
                "DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL"
            ) + f"/api-gateway/v1/accounts/{driivz_account_number}/billing-transactions/estimation"
        ),
        headers={
            "Content-Type": "application/json",
            "dmsTicket": dms_ticket
        },
        timeout=REQUEST_API_TIMEOUT,
        data=json.dumps({
            "cardNumber": driivz_account_card_number,
            "connectorId": connector_id,
            "durationInMinutes": 1
        })
    )
    if tariff_data_response.status_code == 403:
        auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket(
            generate_token=True
        )
        if auth_response is not None and auth_response.status_code != 200:
            return None
        tariff_data_response = traced_request(POST_REQUEST,
            (
                config(
                    "DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL"
                ) + f"/api-gateway/v1/accounts/{driivz_account_number}/billing-transactions/estimation"
            ),
            headers={
                "Content-Type": "application/json",
                "dmsTicket": dms_ticket
            },
            timeout=REQUEST_API_TIMEOUT,
            data=json.dumps({
                "cardNumber": driivz_account_card_number,
                "connectorId": connector_id,
                "durationInMinutes": 1
            })
        )
    return tariff_data_response
