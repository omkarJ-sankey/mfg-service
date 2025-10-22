"""2fa apis"""

# Date - 25/10/2022

# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on APIs related to 2fa.
#   Name            - 2fa API
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 20/05/2025

# These are all the imports that we are exporting from
# different module's from project or library.

import io
import re
import json
import threading
import jwt
import requests
from PIL import Image
from cryptography.fernet import Fernet
import traceback

from django.db.models import Q
from django.shortcuts import get_object_or_404
from decouple import config


from passlib.hash import django_pbkdf2_sha256 as handler

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
)

# pylint:disable=import-error

from sharedServices.model_files.app_user_models import (
    MFGUserEV,
    EmailVerification,
    Profile,
    AppUserThirdPartyRegistrationFailedAPILogs
)
from sharedServices.model_files.config_models import BaseConfigurations
from sharedServices.common import (
    get_blocked_emails_and_phone_numbers,
    handle_concurrent_user_login,
    hasher,
    not_valid,
    return_otp_limit,
    randon_string_generator,
)
from sharedServices.sentry_tracers import traced_request
from sharedServices.constants import (
    INVALID_CODE,
    YES,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    THIRD_PARTY_SIGN_IN_PROFILE_PICTURE,
    REQUEST_API_TIMEOUT,
    EMAIL_SIGN_IN,
    GOOGLE_SIGN_IN,
    APPLE_SIGN_IN,
    GET_REQUEST,
)
from sharedServices.gift_card_common_functions import (
    create_customer_gift_card
)
from sharedServices.image_optimization_funcs import optimize_image

from backendServices.payment.customerapis import CreateCustomerApi

from backendServices.auths.auth_utils import (
    save_otp_function,
    otp_exists_for_user_function,
)
from backendServices.backend_app_constants import (
    MULTIPLE_LOGIN,
    UNAUTHORIZED,
)

from backendServices.charging_sessions.app_level_constants import (
    DRRIVZ_USER_ACCOUNT_NUMBER,
    DRRIVZ_USER_VIRTUAL_CARD_ID,
    DRRIVZ_USER_VIRTUAL_CARD_NUMBER,
)

from .serializers import UserGetDetailsSerializer
from .serializers import UserLoginSerializer
from .app_level_constants import (
    TWO_FA_VERIFICATION
)
from .auth_utils import (
    auth_register_mfg_user_with_drrivz_v4,
    update_user_phone_number_on_driivz,
    generate_ocpi_token
)
from .error_messages import (
    PHONE_ALREADY_REGISTERED
)
# this function validates user phone number

from sharedServices.constants import REQUEST_API_TIMEOUT, POST_REQUEST,CONTENT_TYPE_HEADER_KEY, JSON_DATA 


def decode_jwt_token(token):
    """This function decodes jwt token"""
    return jwt.decode(token, options={"verify_signature": False})


def validate_user_phone_number(phone_number):
    """this function validates phone number"""
    return re.search("^\\+?[1-9][0-9]{8,14}$", phone_number)


def check_phone_number_exists(phone_number):
    """Check if the phone_number exists in the database using hashed phone number"""
    exists = MFGUserEV.objects.filter(
        Q(hashed_phone_number=hasher(str(phone_number)))
    ).exists()
    return exists


class SendOTPFor2FA(APIView):
    """send otp to user phone for 2fa"""

    permission_classes = [IsAuthenticated]

    @classmethod
    def post(cls, send_2fa_otp):
        """send otp to user phone for 2fa"""
        try:
            if not send_2fa_otp.auth:
                return UNAUTHORIZED
            if not handle_concurrent_user_login(
                send_2fa_otp.user.id, send_2fa_otp.auth
            ):
                return MULTIPLE_LOGIN
            if (
                send_2fa_otp.user.user_profile.two_factor_done
                and send_2fa_otp.user.user_profile.two_factor_done == YES
            ):
                print(
                    f"Two factor authentication already done for user -> \
                        {send_2fa_otp.user.id}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            "Two factor authentication " + "is already done for user."
                        ),
                    }
                )
            phone = send_2fa_otp.data.get("phone", None)

            resend_otp = send_2fa_otp.data.get("resend_otp", False)

            if phone is not None:
                phone = phone.lstrip("0")
            country_code = send_2fa_otp.data.get("country_code", None)
            if phone is None or country_code is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            "You have to provide country code "
                            + "and phone number in order to get OTP "
                            + "for two factor authentication."
                        ),
                    }
                )
            phone = f"{country_code}{phone}"

            _, blocked_phone_numbers = get_blocked_emails_and_phone_numbers()

            if phone in blocked_phone_numbers:
                print(
                    f"Phone number is blocked -> \
                            {phone.replace(phone[len(phone)-5:],'*****')}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "This phone number is blocked.",
                    }
                )
            if validate_user_phone_number(phone) is None:
                print(f"Invalid phone number for 2fa -> {phone}")
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Please enter valid phone number.",
                    }
                )
            if check_phone_number_exists(phone):
                print(
                    f"Phone number already exists -> \
                            {phone.replace(phone[len(phone)-5:],'*****')}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": PHONE_ALREADY_REGISTERED
                    }
                )
            decrypter = Fernet(send_2fa_otp.user.key)
            first_name = decrypter.decrypt(send_2fa_otp.user.first_name).decode()
            # logic to send the otp and store the phone and that otp in table.

            count = save_otp_function(
                phone,
                TWO_FA_VERIFICATION,
                first_name,
                send_email=False,
                resend_otp=resend_otp,
                send_sms_otp_for_v3=True
            )
            if count is None:
                print(
                    f"failed to send 2fa otp to \
                        {phone.replace(phone[len(phone)-5:],'*****')}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                        "status": False,
                        "message": "Failed to send OTP.",
                    }
                )
            if count >= return_otp_limit():
                print(
                    f"Maximum OTP limit reached for user with phone \
                        {phone.replace(phone[len(phone)-5:],'*****')}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": (
                            "Maximum otp limits reached. Kindly contact "
                            + "our customer care or try with different phone number"
                        ),
                    }
                )
            print(
                f"2fa otp sent successfully to \
                        {phone.replace(phone[len(phone)-5:],'*****')}"
            )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Otp has been sent successfully.",
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Send OTP For 2FA api failed for user -> \
                    {send_2fa_otp.user.id} due to exception -> \
                        {exception}"
            )
            return API_ERROR_OBJECT


class Verfiy2FAOTP(APIView):
    """verify 2fa otp"""

    permission_classes = [IsAuthenticated]

    @classmethod
    def post(cls, verify_2fa_otp):
        """verify 2fa otp"""
        try:
            if not verify_2fa_otp.auth:
                return UNAUTHORIZED
            if not handle_concurrent_user_login(
                verify_2fa_otp.user.id, verify_2fa_otp.auth
            ):
                return MULTIPLE_LOGIN
            if (
                verify_2fa_otp.user.user_profile.two_factor_done
                and verify_2fa_otp.user.user_profile.two_factor_done == YES
            ):
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            "Two factor authentication is already done for user."
                        ),
                    }
                )
            phone = verify_2fa_otp.data.get("phone", None)

            if phone is not None:
                phone = phone.lstrip("0")
            country_code = verify_2fa_otp.data.get("country_code", None)
            otp_sent = verify_2fa_otp.data.get("otp", None)
            if phone is None or otp_sent is None or country_code is None:
                return Response(
                    {
                        "status code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            "Please provide all fields. "
                            + "Phone number, Contry code, and "
                            + "OTP are mandatory for two factor authentication."
                        ),
                    },
                )
            phone = f"{country_code}{phone}"

            _, blocked_phone_numbers = (
                get_blocked_emails_and_phone_numbers()
            )

            if phone in blocked_phone_numbers:
                print(
                    f"Phone number is blocked -> \
                            {phone.replace(phone[len(phone)-5:],'*****')}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "This phone number is blocked.",
                    }
                )
            if validate_user_phone_number(phone) is None:
                print(f"Invalid phone number for 2fa -> {phone}")
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Please enter valid phone number.",
                    }
                )
            if check_phone_number_exists(phone):
                print(
                    f"Phone number already exists -> \
                            {phone.replace(phone[len(phone)-5:],'*****')}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": PHONE_ALREADY_REGISTERED,
                    }
                )
            otp_exists_checker = otp_exists_for_user_function(
                phone, TWO_FA_VERIFICATION, False
            )
            if not otp_exists_checker["otp_exists"]:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "OTP has expired. Kindly request a new otp.",
                    }
                )
            old = EmailVerification.objects.filter(
                verify_email=otp_exists_checker["user_email"],
                otp_type=TWO_FA_VERIFICATION,
            )
            if str(otp_exists_checker["user_otp"]) != str(otp_sent):
                print(f"Invalid otp entered by user -> {verify_2fa_otp.user.id}")
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": INVALID_CODE,
                    }
                )
            encrypter = Fernet(verify_2fa_otp.user.key)
            MFGUserEV.objects.filter(id=verify_2fa_otp.user.id).update(
                phone_number=encrypter.encrypt(str(phone).encode()),
                hashed_phone_number=hasher(str(phone)),
            )
            Profile.objects.filter(user=verify_2fa_otp.user).update(two_factor_done=YES)
            old.delete()
            start_time = threading.Thread(
                target=update_user_phone_number_on_driivz,
                args=[phone, verify_2fa_otp.user.user_profile.driivz_account_number],
                daemon=True,
            )
            start_time.start()
            return Response(
                {
                    **{
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "Two factor authentication successful.",
                    },
                    **UserGetDetailsSerializer(
                        MFGUserEV.objects.filter(id=verify_2fa_otp.user.id).first(),
                        context={"token": verify_2fa_otp.auth},
                    ).data,
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Verify OTP For 2FA api failed for user -> \
                    {verify_2fa_otp.user.id} due to exception -> \
                        {exception}"
            )
            return API_ERROR_OBJECT


@authentication_classes([])
@permission_classes([])
class SendOTPFor2FAv4(APIView):
    """send otp to user phone for 2fa"""

    @classmethod
    def post(cls, send_2fa_otp):
        """send otp to user phone for 2fa"""
        try:
            phone = send_2fa_otp.data.get("phone", None)
            resend_otp = send_2fa_otp.data.get("resend_otp")

            if phone is not None:
                phone = phone.lstrip("0")
            country_code = send_2fa_otp.data.get("country_code", None)
            if phone is None or country_code is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            "You have to provide email, country code "
                            + "and phone number in order to get OTP "
                            + "for two factor authentication."
                        ),
                    }
                )
            phone = f"{country_code}{phone}"
            _, blocked_phone_numbers = get_blocked_emails_and_phone_numbers()
            if phone in blocked_phone_numbers:
                print(
                    f"Phone number is blocked -> \
                            {phone.replace(phone[len(phone)-5:],'*****')}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "This phone number is blocked.",
                    }
                )
            if validate_user_phone_number(phone) is None:
                print(f"Invalid phone number for 2fa -> {phone}")
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Please enter valid phone number.",
                    }
                )
            if check_phone_number_exists(phone):
                print(
                    f"Phone number already exists -> \
                            {phone.replace(phone[len(phone)-5:],'*****')}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": PHONE_ALREADY_REGISTERED,
                    }
                )
            # logic to send the otp and store the phone and that otp in table.
            count = save_otp_function(
                phone,
                TWO_FA_VERIFICATION,
                None,
                send_email=False,
                resend_otp=resend_otp
            )
            if count is None:
                print(
                    f"failed to send 2fa otp to \
                        {phone.replace(phone[len(phone)-5:],'*****')}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                        "status": False,
                        "message": "Failed to send OTP.",
                    }
                )
            if count >= return_otp_limit():
                print(
                    f"Maximum OTP limit reached for user with phone \
                        {phone.replace(phone[len(phone)-5:],'*****')}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": (
                            "Maximum otp limits reached. Kindly contact "
                            + "our customer care or try with different phone number"
                        ),
                    }
                )
            print(
                f"2fa otp sent successfully to \
                        {phone.replace(phone[len(phone)-5:],'*****')}"
            )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Otp has been sent successfully.",
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Send OTP For 2FA api failed due to exception -> \
                        {exception}"
            )
            return API_ERROR_OBJECT


def create_third_party_and_mfg_accounts(
    *args,
    password=None,
    sso_type=None,
    check_account=False,
    v3_registration=False
):
    """This function creates user account in the DRIIVZ, Square and MFG Connect APP"""
    (
        hashed_email,
        email,
        phone,
        first_name,
        last_name,
        user_name,
        country,
        postal_code,
        profile_picture,
        user_token
    ) = args
    enc_key = Fernet.generate_key()
    encrypter = Fernet(enc_key)
    user = MFGUserEV.objects.filter(
        user_email=hashed_email
    ).first()
    create_third_party_account = user is None and check_account is False
    if sso_type != EMAIL_SIGN_IN and user is None and check_account is True:
        return {
            "status_code": status.HTTP_200_OK,
            "status": True,
            "message": "Sign in successful!",
            "two_factor_auth_done": False
        }
    if (
        sso_type != EMAIL_SIGN_IN and
        user and user.sign_in_method and
        user.sign_in_method != sso_type
    ):
        return {
            "status_code": status.HTTP_403_FORBIDDEN,
            "status": False,
            "message": "This email is linked to a different sign-in method. Please try another way to log in.",
        }
    if user is not None:
        encrypter = Fernet(user.key)
        first_name = encrypter.decrypt(user.first_name).decode()
        last_name = encrypter.decrypt(user.last_name).decode()
        if v3_registration:
            user_name = user.username
            country = encrypter.decrypt(user.country).decode()
            postal_code = encrypter.decrypt(user.country).decode()
    if user is not None and check_account is False:
        MFGUserEV.objects.filter(id=user.id).update(
            phone_number=encrypter.encrypt(str(phone).encode()),
            hashed_phone_number=hasher(str(phone)),
        )
    if create_third_party_account is True:
        if sso_type == APPLE_SIGN_IN and (first_name is False or last_name is False):
            return {
                "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                "status": False,
                "message": "We’re experiencing issues with third-party registration. Please try using a different sign-in method",
            }
        try:
            mfg_customer_care = (
                BaseConfigurations.objects.filter(
                    base_configuration_key="mfg_customer_care"
                )
                .first()
                .base_configuration_value
            )
            drrivz_auth_response = auth_register_mfg_user_with_drrivz_v4(
                first_name,
                last_name,
                email,
                phone,
                v3_registration
            )
            if "endpoint" in drrivz_auth_response and "response" in drrivz_auth_response:
                print(
                    f"Failed to register user on driivz with email -> \
                        {email.replace(email[len(email)-10:],'**********')}"
                )
                print(
                    f"Driivz API status code -> {drrivz_auth_response}",
                )
                AppUserThirdPartyRegistrationFailedAPILogs.objects.create(
                    app_user=user,
                    url=drrivz_auth_response["endpoint"],
                    response=drrivz_auth_response["response"]
                )
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "status": False,
                    "message": "Account creation error. "
                    + "Please try with another email "
                    + "address or call customer service at "
                    + mfg_customer_care,
                }
            if v3_registration is False:
                user = MFGUserEV.objects.create(
                    user_email=hashed_email,
                    first_name=encrypter.encrypt(first_name.encode()),
                    last_name=encrypter.encrypt(last_name.encode()),
                    encrypted_email=encrypter.encrypt(email.encode()),
                    phone_number=encrypter.encrypt(str(phone).encode()),
                    hashed_phone_number=hasher(str(phone)),
                    sign_in_method=sso_type,
                    password=password,
                    key=enc_key,
                )
                Profile.objects.filter(user=user).update(
                    # driivz_account_number=drrivz_auth_response[
                    #     DRRIVZ_USER_ACCOUNT_NUMBER
                    # ],
                    # driivz_virtual_card_id=drrivz_auth_response[
                    #     DRRIVZ_USER_VIRTUAL_CARD_ID
                    # ],
                    # driivz_virtual_card_number=drrivz_auth_response[
                    #     DRRIVZ_USER_VIRTUAL_CARD_NUMBER
                    # ],
                    two_factor_done=YES
                )
            else:
                user = MFGUserEV.objects.create(
                    user_email=hashed_email,
                    first_name=encrypter.encrypt(first_name.encode()),
                    last_name=encrypter.encrypt(last_name.encode()),
                    password=password,
                    username=user_name,
                    post_code=encrypter.encrypt((postal_code.strip()).encode()),
                    encrypted_email=encrypter.encrypt(email.encode()),
                    country=encrypter.encrypt(country.encode()),
                    sign_in_method=EMAIL_SIGN_IN,
                    key=enc_key,
                )
                Profile.objects.filter(user=user).update(
                    driivz_account_number=drrivz_auth_response[
                        DRRIVZ_USER_ACCOUNT_NUMBER
                    ],
                    driivz_virtual_card_id=drrivz_auth_response[
                        DRRIVZ_USER_VIRTUAL_CARD_ID
                    ],
                    driivz_virtual_card_number=drrivz_auth_response[
                        DRRIVZ_USER_VIRTUAL_CARD_NUMBER
                    ],
                )
            customer_req_body = {
                "given_name": email,
                "reference_id": email,
                "email_address": email,
            }
            customer_data = CreateCustomerApi.post(customer_req_body)
            if customer_data.data["status_code"] == status.HTTP_200_OK:
                customer_id = customer_data.data["customersdata"]["id"]
                create_customer_gift_card(customer_id, user)
        except requests.exceptions.ConnectionError as error:
            print(f"Error -> {error}")
            print(
                f"Failed to register user -> \
                    {email.replace(email[len(email)-10:],'**********')}\
                        with DRIIVZ"
            )
            return {
                "status_code": status.HTTP_504_GATEWAY_TIMEOUT,
                "status": False,
                "message": "Account creation error. "
                + "Please try with another email "
                + "address or call customer service at "
                + mfg_customer_care,
            }

    if check_account is False and v3_registration is False:
        Profile.objects.filter(user=user).update(
            two_factor_done=YES
        )
    if profile_picture:
        user_profile = get_object_or_404(
            Profile, id=user.user_profile.id
        )
        if user_profile.profile_picture is None:
            image_req = traced_request(GET_REQUEST, profile_picture, timeout=REQUEST_API_TIMEOUT)
            image = Image.open(io.BytesIO(image_req.content))
            profile_image = optimize_image(
                image,
                f"{first_name}_{last_name}_{user_token}.jpeg",
                THIRD_PARTY_SIGN_IN_PROFILE_PICTURE,
            )
            user_profile.profile_picture = profile_image
            user_profile.save()
    serializer = UserLoginSerializer(
        data={
            "email": hashed_email,
            "user_token": user_token,
            "password": password,
            "sso_type": sso_type,
            "check_2fa": True,
            "v3_registration": v3_registration
        }
    )
    if serializer.is_valid():
        return {
            "status": True,
            "status_code": status.HTTP_200_OK,
            "message": (
                "User credentials added"
                if sso_type=="Email Sign In"
                else "User account created successfully!"
            ),
            "token": serializer.data["token"],
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "user_name": user_name,
            "user_country": country,
            "user_post_code": postal_code,
            "profile_picture": Profile.objects.get(
                id=user.user_profile.id
            ).get_profile_picture(),
            "driivz_account_number": serializer.data[
                "driivz_account_number"
            ],
            "user_evs": serializer.data["user_evs"],
            "user_have_ev": serializer.data["user_have_ev"],
            "loyalty_enabled": serializer.data["loyalty_enabled"],
            "two_factor_auth_done": serializer.data[
                "two_factor_auth_done"
            ],
            "phone_number": serializer.data["phone_number"],
            "already_registered_user": not create_third_party_account
        }

    error_message = "Something went wrong."
    if serializer.errors.get("non_field_errors"):
        error_message = str(serializer.errors.get("non_field_errors"))
        error_message = error_message.split(",", maxsplit=1)[0]
        error_message = error_message.replace("'", "")
        error_message = error_message.split("[ErrorDetail(string=")[1]
    return {
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "status": False,
        "message": error_message,
    }




def create_third_party_and_mfg_accounts_ocpi(
    *args,
    password=None,
    sso_type=None,
    check_account=False,
    v3_registration=False
):
    """This function creates user account in the DRIIVZ, Square and MFG Connect APP"""
    (
        hashed_email,
        email,
        phone,
        first_name,
        last_name,
        user_name,
        country,
        postal_code,
        profile_picture,
        user_token
    ) = args
    enc_key = Fernet.generate_key()
    encrypter = Fernet(enc_key)
    user = MFGUserEV.objects.filter(
        user_email=hashed_email
    ).first()
    create_third_party_account = user is None and check_account is False
    if sso_type != EMAIL_SIGN_IN and user is None and check_account is True:
        return {
            "status_code": status.HTTP_200_OK,
            "status": True,
            "message": "Sign in successful!",
            "two_factor_auth_done": False
        }
    if (
        sso_type != EMAIL_SIGN_IN and
        user and user.sign_in_method and
        user.sign_in_method != sso_type
    ):
        return {
            "status_code": status.HTTP_403_FORBIDDEN,
            "status": False,
            "message": "This email is linked to a different sign-in method. Please try another way to log in.",
        }
    if user is not None:
        encrypter = Fernet(user.key)
        first_name = encrypter.decrypt(user.first_name).decode()
        if user.last_name is not None:
            last_name = encrypter.decrypt(user.last_name).decode() 
        if v3_registration:
            user_name = user.username
            country = encrypter.decrypt(user.country).decode()
            postal_code = encrypter.decrypt(user.country).decode()
    if user is not None and check_account is False:
        MFGUserEV.objects.filter(id=user.id).update(
            phone_number=encrypter.encrypt(str(phone).encode()),
            hashed_phone_number=hasher(str(phone)),
        )
    if create_third_party_account is True:
        if sso_type == APPLE_SIGN_IN and (first_name is False or last_name is False):
            return {
                "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                "status": False,
                "message": "We’re experiencing issues with third-party registration. Please try using a different sign-in method",
            }
        mfg_customer_care = (
                BaseConfigurations.objects.filter(
                    base_configuration_key="mfg_customer_care"
                )
                .first()
                .base_configuration_value
            )
        try:
            mfg_customer_care = (
                BaseConfigurations.objects.filter(
                    base_configuration_key="mfg_customer_care"
                )
                .first()
                .base_configuration_value
            )

            
            if v3_registration is False:
                if user_token == "mfg_connect":
                    user = MFGUserEV.objects.create(
                        user_email=hashed_email,
                        first_name=encrypter.encrypt(first_name.encode()),
                        last_name=encrypter.encrypt(last_name.encode()) if last_name else None,
                        encrypted_email=encrypter.encrypt(email.encode()),
                        phone_number=encrypter.encrypt(str(phone).encode()),
                        hashed_phone_number=hasher(str(phone)),
                        sign_in_method=sso_type,
                        password=password,
                        key=enc_key,
                    )
                else:
                    user = MFGUserEV.objects.filter(device_token = user_token)
                    # user = MFGUserEV.objects.filter(device_token = user_token)
                    user.update(
                        user_email=hashed_email,
                        first_name=encrypter.encrypt(first_name.encode()),
                        last_name=encrypter.encrypt(last_name.encode()) if last_name else None,
                        encrypted_email=encrypter.encrypt(email.encode()),
                        phone_number=encrypter.encrypt(str(phone).encode()),
                        hashed_phone_number=hasher(str(phone)),
                        sign_in_method=sso_type,
                        password=password,
                        key=enc_key,
                    )
                    user = user.first()
                    if user is None:
                         return {
                            "status_code": status.HTTP_404_NOT_FOUND,
                            "status": False,
                            "message": "User with provided device token not found",
                        }
                    
                Profile.objects.filter(user=user).update(
                    # driivz_account_number=drrivz_auth_response[
                    #     DRRIVZ_USER_ACCOUNT_NUMBER
                    # ],
                    # driivz_virtual_card_id=drrivz_auth_response[
                    #     DRRIVZ_USER_VIRTUAL_CARD_ID
                    # ],
                    # driivz_virtual_card_number=drrivz_auth_response[
                    #     DRRIVZ_USER_VIRTUAL_CARD_NUMBER
                    # ],
                    two_factor_done=YES
                )
            else:
                if user_token == "mfg_connect":
                    user = MFGUserEV.objects.create(
                        user_email=hashed_email,
                        first_name=encrypter.encrypt(first_name.encode()),
                        last_name=encrypter.encrypt(last_name.encode()) if last_name else None,
                        password=password,
                        username=user_name,
                        post_code=encrypter.encrypt((postal_code.strip()).encode()),
                        encrypted_email=encrypter.encrypt(email.encode()),
                        country=encrypter.encrypt(country.encode()),
                        sign_in_method=EMAIL_SIGN_IN,
                        key=enc_key,
                    )
                else:
                    user = MFGUserEV.objects.filter(device_token = user_token)
                    # user = MFGUserEV.objects.filter(device_token = user_token)
                    user.update(
                        user_email=hashed_email,
                        first_name=encrypter.encrypt(first_name.encode()),
                        last_name=encrypter.encrypt(last_name.encode()) if last_name else None,
                        password=password,
                        username=user_name,
                        post_code=encrypter.encrypt((postal_code.strip()).encode()),
                        encrypted_email=encrypter.encrypt(email.encode()),
                        country=encrypter.encrypt(country.encode()),
                        sign_in_method=EMAIL_SIGN_IN,
                        key=enc_key,
                    )
                    user = user.first()
                    if user is None:
                         return {
                            "status_code": status.HTTP_404_NOT_FOUND,
                            "status": False,
                            "message": "User with provided device token not found",
                        }
                
            customer_req_body = {
                "given_name": email,
                "reference_id": email,
                "email_address": email,
            }
            customer_data = CreateCustomerApi.post(customer_req_body)
            if customer_data.data["status_code"] == status.HTTP_200_OK:
                customer_id = customer_data.data["customersdata"]["id"]
                create_customer_gift_card(customer_id, user)
        except requests.exceptions.ConnectionError as error:
            print(f"Error -> {error}")
            print(
                f"Failed to register user -> \
                    {email.replace(email[len(email)-10:],'**********')}\
                        with DRIIVZ"
            )
            mfg_customer_care = (
                BaseConfigurations.objects.filter(
                    base_configuration_key="mfg_customer_care"
                )
                .first()
                .base_configuration_value
            )
            return {
                "status_code": status.HTTP_504_GATEWAY_TIMEOUT,
                "status": False,
                "message": "Account creation error. "
                + "Please try with another email "
                + "address or call customer service at "
                + mfg_customer_care,
            }

    if check_account is False and v3_registration is False:
        Profile.objects.filter(user=user).update(
            two_factor_done=YES
        )
    if profile_picture:
        user_profile = get_object_or_404(
            Profile, id=user.user_profile.id
        )
        if user_profile.profile_picture is None:
            image_req = traced_request(GET_REQUEST, profile_picture, timeout=REQUEST_API_TIMEOUT)
            image = Image.open(io.BytesIO(image_req.content))
            profile_image = optimize_image(
                image,
                f"{first_name}_{last_name}_{user_token}.jpeg",
                THIRD_PARTY_SIGN_IN_PROFILE_PICTURE,
            )
            user_profile.profile_picture = profile_image
            user_profile.save()
    serializer = UserLoginSerializer(
        data={
            "email": hashed_email,
            "user_token": user_token,
            "password": password,
            "sso_type": sso_type,
            "check_2fa": True,
            "v3_registration": v3_registration
        }
    )
    if serializer.is_valid():
        try:
            token = generate_ocpi_token(user)
        except Exception as e:
            print(e)
            # if token and token['status_message'].lower() == 'success':
        return {
            "status": True,
            "status_code": status.HTTP_200_OK,
            "message": (
                "User credentials added"
                if sso_type=="Email Sign In"
                else "User account created successfully!"
            ),
            "token": serializer.data["token"],
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "user_name": user_name,
            "user_country": country,
            "user_post_code": postal_code,
            "profile_picture": Profile.objects.get(
                id=user.user_profile.id
            ).get_profile_picture(),
            "driivz_account_number": serializer.data[
                "driivz_account_number"
            ],
            "user_evs": serializer.data["user_evs"],
            "user_have_ev": serializer.data["user_have_ev"],
            "loyalty_enabled": serializer.data["loyalty_enabled"],
            "two_factor_auth_done": serializer.data[
                "two_factor_auth_done"
            ],
            "phone_number": serializer.data["phone_number"],
            "already_registered_user": not create_third_party_account
        }
        

    error_message = "Something went wrong."
    if serializer.errors.get("non_field_errors"):
        error_message = str(serializer.errors.get("non_field_errors"))
        error_message = error_message.split(",", maxsplit=1)[0]
        error_message = error_message.replace("'", "")
        error_message = error_message.split("[ErrorDetail(string=")[1]
    return {
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "status": False,
        "message": error_message,
    }



@authentication_classes([])
@permission_classes([])
class Verfiy2FAOTPv4(APIView):
    """verify 2fa otp"""

    @classmethod
    def post(cls, verify_2fa_otp):
        """verify 2fa otp"""
        try:
            sso_type = verify_2fa_otp.data.get("sso_type", None)
            if sso_type is None:
                return Response(
                    {
                        "status code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Failed to sign in due to missing sign in option.",
                    },
                )
            phone = verify_2fa_otp.data.get("phone", None)
            country_code = verify_2fa_otp.data.get("country_code", None)
            user_token = verify_2fa_otp.data.get("user_token", "mfgconnect")
            phone_otp = verify_2fa_otp.data.get("phone_otp", None)
            if phone is not None:
                phone = phone.lstrip("0")

            phone = f"{country_code}{phone}"
            profile_picture=None
            if sso_type == EMAIL_SIGN_IN:
                email = verify_2fa_otp.data.get("email", False)

                email = email.lower()
                first_name = verify_2fa_otp.data.get("first_name", False)
                last_name = verify_2fa_otp.data.get("last_name", False)
                password = verify_2fa_otp.data.get("password", False)
                invalid_register_condition = (
                    phone is None
                    or not_valid("otp", phone_otp)
                    or not_valid("name", first_name)
                    or not_valid("name", last_name)
                    or not_valid("password", password)
                    or country_code is None
                    or email is None
                )
                if invalid_register_condition:
                    return Response(
                        {
                            "status code": status.HTTP_406_NOT_ACCEPTABLE,
                            "status": False,
                            "message": (
                                "Please provide all fields. "
                                + "Phone number, Contry code, and "
                                + "OTP are mandatory for two factor authentication."
                            ),
                        },
                    )

                if validate_user_phone_number(phone) is None:
                    print(f"Invalid phone number for 2fa -> {phone}")
                    return Response(
                        {
                            "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                            "status": False,
                            "message": "Please enter valid phone number.",
                        }
                    )
                if check_phone_number_exists(phone):
                    print(
                        "Phone number already exists -> "+
                        f"{phone.replace(phone[len(phone)-5:],'*****')}"
                    )
                    return Response(
                        {
                            "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                            "status": False,
                            "message": PHONE_ALREADY_REGISTERED
                        }
                    )
            else:
                token_data = verify_2fa_otp.data.get("token", False)
                if (
                    token_data is False or
                    not_valid("otp", phone_otp) or
                    not_valid("user_token", user_token) or
                    country_code is None
                ):
                    return Response(
                        {
                            "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                            "status": False,
                            "message": "Please try to register again.",
                        },
                        # status = status.HTTP_406_NOT_ACCEPTABLE
                    )
                parsed_json_data = json.loads(
                    token_data
                )
                email = parsed_json_data.get("email")
                first_name = False
                last_name = False
                email = False
                if sso_type == GOOGLE_SIGN_IN:
                    email = parsed_json_data.get("email", False)
                    first_name = parsed_json_data.get("given_name", False)
                    last_name = parsed_json_data.get("family_name", False)
                elif "fullName" in parsed_json_data:
                    decoded_token = decode_jwt_token(parsed_json_data["identityToken"])
                    email = decoded_token.get("email", False)
                    first_name = parsed_json_data["fullName"]["givenName"]
                    last_name = parsed_json_data["fullName"]["familyName"]
                email = email.lower()
                profile_picture = parsed_json_data.get("picture", "")
                password =  handler.hash(randon_string_generator())
            _, blocked_phone_numbers = get_blocked_emails_and_phone_numbers()
            if phone in blocked_phone_numbers:
                print(
                    f"Phone number is blocked -> \
                            {phone.replace(phone[len(phone)-5:],'*****')}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "This phone number is blocked.",
                    }
                )
            phone_otp_exists_checker = otp_exists_for_user_function(
                phone, TWO_FA_VERIFICATION, False
            )
            if not phone_otp_exists_checker["otp_exists"]:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            "OTP has expired. Kindly request a new otp."
                        ),
                    }
                )
            old_phone_otp = EmailVerification.objects.filter(
                verify_email=phone_otp_exists_checker["user_email"],
                otp_type=TWO_FA_VERIFICATION,
            )
            if str(phone_otp_exists_checker["user_otp"]) != str(phone_otp):
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": INVALID_CODE,
                    }
                )
            old_phone_otp.delete()
            hashed_email = hasher(email)
            hashed_password = handler.hash(password)
            account_creation_result = create_third_party_and_mfg_accounts(
                hashed_email,
                email,
                phone,
                first_name,
                last_name,
                None,
                None,
                None,
                profile_picture,
                user_token,
                password=hashed_password,
                sso_type=sso_type
            )
            return Response(account_creation_result)
        except COMMON_ERRORS as exception:
            print(
                f"Verify OTP For 2FA api failed due to exception -> \
                        {exception}"
            )
            return API_ERROR_OBJECT


@authentication_classes([])
@permission_classes([])
class Verfiy2FAOTPv4OCPI(APIView):
    """verify 2fa otp"""

    @classmethod
    def post(cls, verify_2fa_otp):
        """verify 2fa otp"""
        try:
            sso_type = verify_2fa_otp.data.get("sso_type", None)
            if sso_type is None:
                return Response(
                    {
                        "status code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Failed to sign in due to missing sign in option.",
                    },
                )
            phone = verify_2fa_otp.data.get("phone", None)
            country_code = verify_2fa_otp.data.get("country_code", None)
            user_token = verify_2fa_otp.data.get("user_token", "mfgconnect")
            phone_otp = verify_2fa_otp.data.get("phone_otp", None)
            if phone is not None:
                phone = phone.lstrip("0")

            phone = f"{country_code}{phone}"
            profile_picture=None
            if sso_type == EMAIL_SIGN_IN:
                email = verify_2fa_otp.data.get("email", False)

                email = email.lower()
                first_name = verify_2fa_otp.data.get("first_name", False)
                last_name = verify_2fa_otp.data.get("last_name", False)
                password = verify_2fa_otp.data.get("password", False)
                invalid_register_condition = (
                    phone is None
                    or not_valid("otp", phone_otp)
                    or not_valid("name", first_name)
                    or not_valid("name", last_name)
                    or not_valid("password", password)
                    or country_code is None
                    or email is None
                )
                if invalid_register_condition:
                    return Response(
                        {
                            "status code": status.HTTP_406_NOT_ACCEPTABLE,
                            "status": False,
                            "message": (
                                "Please provide all fields. "
                                + "Phone number, Contry code, and "
                                + "OTP are mandatory for two factor authentication."
                            ),
                        },
                    )

                if validate_user_phone_number(phone) is None:
                    print(f"Invalid phone number for 2fa -> {phone}")
                    return Response(
                        {
                            "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                            "status": False,
                            "message": "Please enter valid phone number.",
                        }
                    )
                if check_phone_number_exists(phone):
                    print(
                        "Phone number already exists -> "+
                        f"{phone.replace(phone[len(phone)-5:],'*****')}"
                    )
                    return Response(
                        {
                            "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                            "status": False,
                            "message": PHONE_ALREADY_REGISTERED
                        }
                    )
            else:
                token_data = verify_2fa_otp.data.get("token", False)
                if (
                    token_data is False or
                    not_valid("otp", phone_otp) or
                    not_valid("user_token", user_token) or
                    country_code is None
                ):
                    return Response(
                        {
                            "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                            "status": False,
                            "message": "Please try to register again.",
                        },
                        # status = status.HTTP_406_NOT_ACCEPTABLE
                    )
                parsed_json_data = json.loads(
                    token_data
                )
                email = parsed_json_data.get("email")
                first_name = False
                last_name = False
                email = False
                if sso_type == GOOGLE_SIGN_IN:
                    email = parsed_json_data.get("email", False)
                    first_name = parsed_json_data.get("given_name", False)
                    last_name = parsed_json_data.get("family_name", False)
                elif "fullName" in parsed_json_data:
                    decoded_token = decode_jwt_token(parsed_json_data["identityToken"])
                    email = decoded_token.get("email", False)
                    first_name = parsed_json_data["fullName"]["givenName"]
                    last_name = parsed_json_data["fullName"]["familyName"]
                email = email.lower()
                profile_picture = parsed_json_data.get("picture", "")
                password =  handler.hash(randon_string_generator())
            _, blocked_phone_numbers = get_blocked_emails_and_phone_numbers()
            if phone in blocked_phone_numbers:
                print(
                    f"Phone number is blocked -> \
                            {phone.replace(phone[len(phone)-5:],'*****')}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "This phone number is blocked.",
                    }
                )
            phone_otp_exists_checker = otp_exists_for_user_function(
                phone, TWO_FA_VERIFICATION, False
            )
            if not phone_otp_exists_checker["otp_exists"]:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            "OTP has expired. Kindly request a new otp."
                        ),
                    }
                )
            old_phone_otp = EmailVerification.objects.filter(
                verify_email=phone_otp_exists_checker["user_email"],
                otp_type=TWO_FA_VERIFICATION,
            )
            if str(phone_otp_exists_checker["user_otp"]) != str(phone_otp):
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": INVALID_CODE,
                    }
                )
            old_phone_otp.delete()
            hashed_email = hasher(email)
            hashed_password = handler.hash(password)
            account_creation_result = create_third_party_and_mfg_accounts_ocpi(
                hashed_email,
                email,
                phone,
                first_name,
                last_name,
                None,
                None,
                None,
                profile_picture,
                user_token,
                password=hashed_password,
                sso_type=sso_type
            )
            return Response(account_creation_result)
        except COMMON_ERRORS as exception:
            print(
                f"Verify OTP For 2FA api failed due to exception -> \
                        {exception}"
            )
            traceback.print_exc()
            return API_ERROR_OBJECT
