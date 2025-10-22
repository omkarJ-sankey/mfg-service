"""contact less module common functions"""
#  File details-
#   Author         - Manish Pawar
#   Description    - This file contains functions for Contactless module.
#   Name           - contact less module functions
#   Modified by    - Shivkumar Kumbhar
#   Modified date  - 29/03/2023

# These are all the imports that we are exporting from
# different module's from project or library.
import json
import traceback
import requests
from decouple import config

from django.utils import timezone

# pylint:disable=import-error
from sharedServices.sentry_tracers import traced_request
from sharedServices.constants import REQUEST_API_TIMEOUT, POST_REQUEST
from sharedServices.model_files.config_models import BaseConfigurations

DJANGO_APP_PAYTER_BASE_URL = config("DJANGO_APP_PAYTER_BASE_URL")
DJANGO_APP_PAYTER_USERNAME = config("DJANGO_APP_PAYTER_USERNAME")
DJANGO_APP_PAYTER_PASSWORD = config("DJANGO_APP_PAYTER_PASSWORD")
DJANGO_APP_PAYTER_DOMAIN = config("DJANGO_APP_PAYTER_DOMAIN")

PAYTER_TOKEN_EXPIRY = "payter_token_expiry"
PAYTER_TOKEN = "payter_token"

ADVAM_API_ACCOUNT=config("DJANGO_APP_ADVAM_API_ACCOUNT_NUMBER")
ADVAM_API_USERNAME=config("DJANGO_APP_ADVAM_API_USERNAME")
ADVAM_API_PASSWORD=config("DJANGO_APP_ADVAM_API_PASSWORD")

def generate_payter_tokens(generate_new_token):
    """generate payter tokens"""

    token_expiry = BaseConfigurations.objects.filter(
        base_configuration_key=PAYTER_TOKEN_EXPIRY
    )
    if token_expiry.first():
        token_db_entry = BaseConfigurations.objects.filter(
            base_configuration_key=PAYTER_TOKEN,
        )
        if token_db_entry.first() and generate_new_token is False:
            total_duration_in_seconds = int(
                (
                    timezone.now() - token_db_entry.first().updated_date
                ).total_seconds()
            )
            if total_duration_in_seconds < (
                int(token_expiry.first().base_configuration_value) - 3600
            ):
                return token_db_entry.first().base_configuration_value

    req_url = f"{DJANGO_APP_PAYTER_BASE_URL}/Auth"

    headers_list = {"Content-Type": "application/json"}

    payload = json.dumps(
        {
            "username": DJANGO_APP_PAYTER_USERNAME,
            "password": DJANGO_APP_PAYTER_PASSWORD,
            "domain": DJANGO_APP_PAYTER_DOMAIN,
        }
    )

    auth_response = traced_request(POST_REQUEST, req_url, data=payload, headers=headers_list,timeout=REQUEST_API_TIMEOUT)

    if auth_response.status_code == 200:
        response_data = json.loads(auth_response.content)
        # update tokens in DB
        if token_expiry.first() and token_db_entry.first():
            token_db_entry.update(
                base_configuration_value=response_data["tokenId"],
                updated_date=timezone.now(),
            )
        else:
            BaseConfigurations.objects.create(
                base_configuration_key=PAYTER_TOKEN,
                base_configuration_value=response_data["tokenId"],
                created_date=timezone.now(),
                updated_date=timezone.now(),
            )
        if token_expiry.first():
            token_expiry.update(
                base_configuration_value=str(response_data["expiresIn"]),
                updated_date=timezone.now(),
            )
        else:
            BaseConfigurations.objects.create(
                base_configuration_key=PAYTER_TOKEN_EXPIRY,
                base_configuration_value=str(response_data["expiresIn"]),
                created_date=timezone.now(),
                updated_date=timezone.now(),
            )

        return response_data["tokenId"]
    else:
        return None


def get_payter_transactions_from_data_api(body, generate_new_token=False):
    """this API returns payter transactions"""

    url = f"{DJANGO_APP_PAYTER_BASE_URL}/Data"

    payter_token = generate_payter_tokens(generate_new_token)
    if payter_token is None:
        print("Failed to generate new payter tokens")
        return payter_token
    headers = {
        "Content-Type": "application/json",
        "Authorization": f'CURO-TOKEN token="{payter_token}"',
    }

    return traced_request(POST_REQUEST, url, headers=headers, data=body, timeout=REQUEST_API_TIMEOUT)


def advam_api(from_time, to_time):
    try:
        url = f"https://gateway.api.advam.com/reporting/v1/report/transaction?advamAccount={ADVAM_API_ACCOUNT}&startDateTime={from_time}&endDateTime={to_time}"
        req = requests.get(url, auth=(ADVAM_API_USERNAME, ADVAM_API_PASSWORD))
        if req.status_code == 200:
            return req.json().get("transactions", [])
        else:
            print(f"Error: Advam API responded with status code {req.status_code}, {req.text}")
    except Exception:
        traceback.print_exc()
    return None