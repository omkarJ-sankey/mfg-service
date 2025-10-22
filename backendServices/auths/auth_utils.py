"""authentication required functions"""
# Date - 26/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly fcontains functions related
#                       to OTP and verifying users
#   Name            - Auth utils
#   Modified by     - Manish Pawar
#   Modified date   - 27/01/2022


# These are all the imports that we are exporting from different
# module's from project or library.

import json
import threading
import requests
from decouple import config
from django.utils import timezone
from rest_framework import status

from cryptography.fernet import Fernet

from passlib.hash import django_pbkdf2_sha256 as handler
import random
import string
from sharedServices.common import (
    get_node_secret,
    ensure_str,
)

from django.forms.models import model_to_dict
from datetime import datetime
# pylint:disable=import-error
from sharedServices.model_files.app_user_models import (
    MFGUserEV,
    EmailVerification,
    Profile,
)
from sharedServices.model_files.config_models import (
    BaseConfigurations
)
from sharedServices.common import (
    return_otp_limit,
    hasher,
    filter_function_for_base_configuration
)
from sharedServices.email_common_functions import (
    send_otp
)
from sharedServices.driivz_api_gateway_functions import (
    get_driivz_api_gateway_dms_ticket
)
from sharedServices.sentry_tracers import traced_request,traced_request_with_retries
from sharedServices.constants import (
    REGISTER,
    REQUEST_API_TIMEOUT,
    DEFAULT_DRIIVZ_PLAN_CODE,
    DRIIVZ_PLAN_CODE,
    EMAIL_SIGN_IN,
    POST_REQUEST,
    PATCH_REQUEST,
    CONTENT_TYPE_HEADER_KEY,
    JSON_DATA,
    EMSP_ENDPOINT,
    GET_REQUEST,
    REREGISTER_TOKENS_ENDPOINT,
)

from backendServices.charging_sessions.app_level_constants import (
    DRRIVZ_USER_ACCOUNT_NUMBER,
    DRRIVZ_USER_VIRTUAL_CARD_ID,
    DRRIVZ_USER_VIRTUAL_CARD_NUMBER,
)

from .app_level_constants import (
    TWO_FA_VERIFICATION,
    DRIIVZ_SHIPPING_ADDRESS,
)

from sharedServices.model_files.ocpi_tokens_models import OCPITokens

from backendServices.charging_sessions.app_level_constants import (
    OCPI_TOKENS_ENDPOINT,
    EMSP_COUNTRY_CODE,
    EMSP_PARTY_ID,
    APP_USER,
    OCPI_TOKEN_ISSUER
)

from sharedServices.model_files.ocpi_credentials_models import OCPICredentials, OCPICredentialsRole

def update_user_email_function(*arg):
    """This function adds user mail if his email is not added earlier"""
    user_id, user_email = arg
    user_data = MFGUserEV.objects.filter(id=user_id)
    encrypter = Fernet(user_data.first().key)
    user_data.update(encrypted_email=encrypter.encrypt(user_email.encode()))


def user_exists_function(
    email,
    password,
    password_verification,
    return_email,
    check_email_sign_in=True
):
    """user exists or not checker function"""
    user_exists = False

    if return_email:
        user_first_name = ""
        user_last_name = ""
        user_user_name = ""
        user_password = ""
        user_email = ""
        user_country = ""
        user_post_code = ""
        profile_picture = None
        email_verified = False
        password_verified = False
    user = MFGUserEV.objects.filter(
        user_email=hasher(email)
    ).first()
    if check_email_sign_in and user and user.sign_in_method != EMAIL_SIGN_IN:
        return user.sign_in_method
    if user:
        email_verified = True
        key = user.key
        if key:
            decrypter = Fernet(key)
            if password_verification:
                if handler.verify(password, user.password):
                    password_verified = True
                    user_exists = True
                    if user.encrypted_email is None:
                        update_user_mail = threading.Thread(
                            target=update_user_email_function,
                            args=[user.id, email],
                            daemon=True
                        )
                        update_user_mail.start()
                    user_email = user.user_email
                    user_password = user.password
                    user_first_name = decrypter.decrypt(
                        user.first_name
                    ).decode()
                    user_last_name = decrypter.decrypt(user.last_name).decode()
                    user_user_name = user.username
                    if user.country:
                        user_country = decrypter.decrypt(user.country).decode()
                    if user.post_code:
                        user_post_code = decrypter.decrypt(user.post_code).decode()
                    profiles = Profile.objects.filter(user=user)
                    if profiles.first():
                        profile_picture = (
                            profiles.first().get_profile_picture()
                        )
            else:
                user_exists = True
                user_email = user.user_email
                user_first_name = decrypter.decrypt(user.first_name).decode()
                user_last_name = decrypter.decrypt(user.last_name).decode()
                user_user_name = ""

    if return_email:
        return {
            "user_exists": user_exists,
            "user_email": user_email,
            "password": user_password,
            "user_name": user_user_name,
            "email": email,
            "user_first_name": user_first_name,
            "user_last_name": user_last_name,
            "user_country": user_country,
            "user_post_code": user_post_code,
            "profile_picture": profile_picture,
            "email_verified": email_verified,
            "password_verified": password_verified,
        }
    return user_exists


# function to check whether OTP is sent to user's number or not
def otp_exists_for_user_function(email, otp_type, with_count):
    """otp exists or not checker function"""
    otp_exists = False
    user_email = ""
    user_otp = ""
    otp_data = EmailVerification.objects.filter(
        otp_type=otp_type, verify_email=hasher(email)
    ).first()
    count = 0
    if otp_data:
        otp_exists = True
        user_email = otp_data.verify_email
        user_otp = otp_data.otp
        count = otp_data.count

    if with_count:
        can_resend_otp = True
        if otp_data:
            otp_cooldown_period = BaseConfigurations.objects.filter(
                base_configuration_key="otp_cooldown_period"
            ).first()
            can_resend_otp = (
                timezone.localtime(timezone.now()) - otp_data.modified_date
            ).total_seconds() > (
                int(
                    otp_cooldown_period.base_configuration_value
                ) if otp_cooldown_period else 60
            )
        return {
            "otp_exists": otp_exists,
            "user_email": user_email,
            "count": count,
            "can_resend_otp": can_resend_otp
        }
    return {
        "otp_exists": otp_exists,
        "user_email": user_email,
        "user_otp": user_otp,
    }


# function to save and send OTP
# send_email is the key to toggle between service
# of email sending or SMS sending service.
def save_otp_function(
    email,
    otp_type,
    user_name,
    send_email=True,
    resend_otp=False,
    send_sms_otp_for_v3=False
):
    """save otp function"""
    count = 0
    otp_exists_checker = otp_exists_for_user_function(email, otp_type, True)
    if resend_otp and not otp_exists_checker["can_resend_otp"]:
        return None
    count = otp_exists_checker["count"]
    if otp_exists_checker["count"] < return_otp_limit():
        user_first_name = user_name
        if otp_type not in (REGISTER ,TWO_FA_VERIFICATION):
            users = MFGUserEV.objects.filter(
                user_email=hasher(email)
            ).first()
            if users:
                key = users.key
                decrypter = Fernet(key)
                user_first_name = decrypter.decrypt(users.first_name).decode()
        otp = send_otp(
            email, user_first_name, otp_type, send_email, send_sms_otp_for_v3
        )
        if otp is False:
            return None
        now = timezone.localtime(timezone.now())
        if otp_exists_checker["otp_exists"]:
            user_otp = EmailVerification.objects.filter(
                verify_email=otp_exists_checker["user_email"],
                otp_type=otp_type,
            )
            user_otp.update(otp=otp, count=count + 1, modified_date=now)
        else:
            otp = str(otp)
            count = count + 1
            EmailVerification.objects.create(
                verify_email=hasher(email),
                otp=otp,
                count=count,
                otp_type=otp_type,
                modified_date=now,
            )
    return count


def create_driivz_customer_account_api_call(
    dms_ticket,
    first_name,
    last_name,
    email,
    phone,
    exlude_phone
):
    """this api created driivz customer account"""
    user_data = {
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "accountType": "PRIVATE",
        "billingAddress": DRIIVZ_SHIPPING_ADDRESS,
        "shippingAddress": DRIIVZ_SHIPPING_ADDRESS,
        "termsAndConditionsConsent": True,
        "profilingConsent": True,
        "activationMode": "ACTIVE",
        "countryCurrencyId": 21
    }
    if exlude_phone is False:
        user_data["mobile"] = phone
    return traced_request(
        POST_REQUEST,
        config(
            "DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL"
        ) + "/api-gateway/v1/customer-accounts",
        headers={
            "Content-Type": "application/json",
            "dmsTicket": dms_ticket
        },
        data=json.dumps(user_data),
        timeout=REQUEST_API_TIMEOUT,
    )


def delete_driivz_customer_account_api_call(
    dms_ticket,
    account_number
):
    """this api deletes driivz customer account"""
    return traced_request(
        PATCH_REQUEST,
        config(
            "DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL"
        ) + f"/api-gateway/v1/customer-accounts/{account_number}/actions/close",
        headers={
            "Content-Type": "application/json",
            "dmsTicket": dms_ticket
        },
        data=json.dumps({
            "closedByCustomer": True
        }),
        timeout=REQUEST_API_TIMEOUT,
    )


def create_driivz_customer_contract_api(dms_ticket, account_number):
    """this function creates DRIIVZ contract for the customer"""
    return traced_request(
        POST_REQUEST,
        config(
            "DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL"
        ) + f"/api-gateway/v1/accounts/{account_number}/contracts",
        headers={
            "Content-Type": "application/json",
            "dmsTicket": dms_ticket
        },
        data=json.dumps({
            "status": "ACTIVE",
            "planCode": filter_function_for_base_configuration(
                DRIIVZ_PLAN_CODE, DEFAULT_DRIIVZ_PLAN_CODE
            )
        }),
        timeout=REQUEST_API_TIMEOUT,
    )


def get_customer_drrivz_card(dms_ticket, account_number):
    """this function returns driivz card details for the customer"""
    return traced_request(
        POST_REQUEST,
        config(
            "DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL"
        ) + "/api-gateway/v1/cards/filter",
        headers={
            "Content-Type": "application/json",
            "dmsTicket": dms_ticket
        },
        data=json.dumps({
            "accountNumber": account_number
        }),
        timeout=REQUEST_API_TIMEOUT,
    )


def auth_register_mfg_user_with_drrivz_v4(
    first_name,
    last_name,
    email,
    phone,
    v3_registration
):
    """This function creates user DRIIVZ account"""
    auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket()
    if auth_response is not None and auth_response.status_code != 200:
        return {
            "endpoint": "/api-gateway/v1/authentication/operator/login",
            "response": auth_response.content,
        }
    create_customer_api_response = create_driivz_customer_account_api_call(
        dms_ticket,
        first_name,
        last_name,
        email,
        phone,
        v3_registration
    )
    if create_customer_api_response.status_code == 403:
        auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket(generate_token=True)
        if auth_response is not None and auth_response.status_code != 200:
            return {
                "endpoint": "/api-gateway/v1/authentication/operator/login",
                "response": auth_response.content,
            }
        create_customer_api_response = create_driivz_customer_account_api_call(
            dms_ticket,
            first_name,
            last_name,
            email,
            phone,
            v3_registration
        )
    if create_customer_api_response.status_code != 200:
        return {
            "endpoint": "/api-gateway/v1/customer-accounts",
            "response": create_customer_api_response.content,
        }

    account_number = json.loads(
        create_customer_api_response.content
    )['data'][0]['accountNumber']

    assign_contract_to_user_api_response = create_driivz_customer_contract_api(
        dms_ticket,
        account_number
    )

    if assign_contract_to_user_api_response.status_code == 403:
        auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket(generate_token=True)
        if auth_response is not None and auth_response.status_code != 200:
            return {
                "endpoint": "/api-gateway/v1/authentication/operator/login",
                "response": auth_response.content,
            }
        assign_contract_to_user_api_response = create_driivz_customer_contract_api(
            dms_ticket,
            account_number
        )
    if assign_contract_to_user_api_response.status_code != 200:
        return {
            "endpoint": "/api-gateway/v1/accounts/account_number/contracts",
            "response": assign_contract_to_user_api_response.content,
        }

    get_user_card_number_api_response = get_customer_drrivz_card(
        dms_ticket,
        account_number
    )
    if get_user_card_number_api_response.status_code == 403:
        auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket(generate_token=True)
        if auth_response is not None and auth_response.status_code != 200:
            return {
                "endpoint": "/api-gateway/v1/authentication/operator/login",
                "response": auth_response.content,
            }
        get_user_card_number_api_response = get_customer_drrivz_card(
            dms_ticket,
            account_number
        )
    if get_user_card_number_api_response.status_code != 200:
        return {
            "endpoint": "/api-gateway/v1/cards/filter",
            "response": get_user_card_number_api_response.content,
        }
    get_user_card_number_api_response_data = json.loads(
        get_user_card_number_api_response.content
    )
    return {
        DRRIVZ_USER_ACCOUNT_NUMBER: account_number,
        DRRIVZ_USER_VIRTUAL_CARD_ID: get_user_card_number_api_response_data['data'][0]['id'],
        DRRIVZ_USER_VIRTUAL_CARD_NUMBER: get_user_card_number_api_response_data[
            'data'
        ][0]['cardNumber'],
    }


def update_user_phone_number_on_driivz(phone, driivz_account_number):
    """this function updates user phone number on driivz"""
    try:
        auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket()
        if auth_response is not None and auth_response.status_code != 200:
            return None
        response = traced_request(
            PATCH_REQUEST,
            config("DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL") +
            f"/api-gateway/v1/customer-accounts/{driivz_account_number}/profile",
            data=json.dumps({"mobile": phone}),
            headers={
                "Content-Type": "application/json",
                "dmsTicket": dms_ticket
            },
            timeout=REQUEST_API_TIMEOUT,
        )
        if response.status_code == 403:
            auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket(
                generate_token=True
            )
            if auth_response is not None and auth_response.status_code != 200:
                return None
            traced_request(
                PATCH_REQUEST,
                config("DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL") +
                f"/api-gateway/v1/customer-accounts/{driivz_account_number}/profile",
                data=json.dumps({"mobile": phone}),
                headers={
                    "Content-Type": "application/json",
                    "dmsTicket": dms_ticket
                },
                timeout=REQUEST_API_TIMEOUT,
            )
    except requests.exceptions.ConnectionError as error:
        print(
            "Failed to update user mobile number with DRIIVZ, "
            + "user account number ->"
            + f"{driivz_account_number}"
        )
        print("error ->", error)

def generate_ocpi_token(user_id):
    length = random.randint(10, 36)
    characters = string.ascii_uppercase + string.digits
    contract_id = ''.join(random.choices(characters, k=length))

    token = ''.join(random.choices(characters, k=length))
    ocpi_data = OCPICredentialsRole.objects.filter(business_details = "MFG").first()
    token_data = OCPITokens.objects.create(
            uid = token,
            country_code = ocpi_data.country_code if ocpi_data is not None else EMSP_COUNTRY_CODE,
            party_id = ocpi_data.party_id if ocpi_data is not None else EMSP_PARTY_ID,
            type = APP_USER,
            issuer= OCPI_TOKEN_ISSUER,
            valid= True,
            whitelist= "ALWAYS",
            contract_id = contract_id,
            energy_contract = None,
            user_id = user_id,
            last_updated = timezone.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
    request_data = model_to_dict(token_data)

    user_profile = Profile.objects.filter(user_id = user_id).first()
    if user_profile.driivz_account_number is None:
        user_profile.driivz_account_number = token
    user_profile.save()

    
    
    list_data = list(OCPICredentials.objects.filter(status = 'Active').values_list('name', flat=True).distinct())

    upper_list = []
    for ele in list_data:
        upper_list.append(ele.upper())
    request_data['OCPI']  = upper_list
    token = get_node_secret()

    data = traced_request_with_retries(
            POST_REQUEST,
            EMSP_ENDPOINT + OCPI_TOKENS_ENDPOINT,
            headers={
                CONTENT_TYPE_HEADER_KEY: JSON_DATA,
                "Authorization": f"Token {ensure_str(token)}"
            },
            data=json.dumps(request_data, default=str),
            timeout=REQUEST_API_TIMEOUT,
        )
    return data.json()

def register_users_cron():
    
    token = get_node_secret()
    response=traced_request_with_retries(
        GET_REQUEST,
        EMSP_ENDPOINT + REREGISTER_TOKENS_ENDPOINT,
        headers={
            CONTENT_TYPE_HEADER_KEY: JSON_DATA,
            "Authorization": f"Token {token}"
        },
        data=json.dumps({}),
        timeout=REQUEST_API_TIMEOUT,
    )
    if response is not None and response.status_code == status.HTTP_200_OK and json.loads(response.content.decode())["status_code"]==status.HTTP_200_OK:
        print("Failed to update tokens")
        return None
    print("Updated tokens")