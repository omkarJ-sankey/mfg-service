"""stations helper functions"""
# Date - 05/08/2025


# File details-
#   Author          - Abhinav Shivalkar
#   Description     - This file contains helper functions for credentials module.
#   Name            - OCPI credentials helper functions
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 05/08/2025

import json
import threading
import traceback
from django.db import models
from rest_framework import status
from django.db.models import Func,Value
from django.db.models.functions import Cast



from sharedServices.common import get_node_secret
from sharedServices.model_files.ocpi_tokens_models import OCPITokens
from sharedServices.sentry_tracers import traced_request_with_retries
from sharedServices.constants import (
    GET_REQUEST,
    EMSP_ENDPOINT,
    CONTENT_TYPE_HEADER_KEY,
    REQUEST_API_TIMEOUT,
    JSON_DATA,
    REREGISTER_TOKENS_ENDPOINT
)


class JSONModify(Func):
    function = 'JSON_MODIFY'
    arity = 3

def register_user_tokens(back_office):
    """this function registers tokens on CPO"""
    print("Initiated token registration process")
    OCPITokens.objects.update(
        back_offices = JSONModify(
            Cast('back_offices', models.TextField()),
            Value(f'$.{back_office}'),
            Value(False)
        ),
        is_verified = False
    )
    token = get_node_secret()
    response=traced_request_with_retries(
        GET_REQUEST,
        EMSP_ENDPOINT + REREGISTER_TOKENS_ENDPOINT,
        headers={
            CONTENT_TYPE_HEADER_KEY: JSON_DATA,
            "Authorization": f"Token {token}"
        },
        timeout=REQUEST_API_TIMEOUT,
    )
    if response is None or response.status_code != status.HTTP_200_OK or json.loads(response.content.decode())["status_code"] != status.HTTP_200_OK:
        print(json.loads(response.content.decode()))
        print("Failed to register tokens on ",back_office)
    else:
        print("Initiated function to register tokens on ",back_office)
    return None

def register_existing_users_to_cpo(back_office):
    """this function initiates tokens registration process on CPO in a new thread"""
    try:
        register_tokens = threading.Thread(
            target=register_user_tokens,
            args=(back_office,),
            daemon=True
        )
        register_tokens.start()
    except Exception as e:
        print("Failed to register tokens to cpo due to error -> ",e)
        traceback.print_exc()