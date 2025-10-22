"""Authentication API to tackle new features in V4.0.0"""
# Date - 26/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on APIs
#                       related to authentication of MFG EV app user.
#   Name            - App athentication API
#   Modified by     - Manish Pawar
#   Modified date   - 23/10/2024


# These are all the imports that we are exporting from different
# module's from project or library.
# pylint:disable=import-error
import json
from datetime import timedelta
from django.db.models import Q

from itertools import repeat
import traceback
import threading

from decouple import config

from passlib.hash import django_pbkdf2_sha256 as handler

from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
)
from sharedServices.constants import OCPI_CREDENTIALS_CACHE_KEY
from rest_framework.views import APIView
from concurrent.futures import ThreadPoolExecutor, as_completed

from concurrent.futures import ProcessPoolExecutor
from passlib.hash import django_pbkdf2_sha256 as handler

from backendServices.charging_sessions.app_level_constants import OCPI_TOKENS_ENDPOINT
from sharedServices.model_files.ocpi_credentials_models import OCPICredentials


# pylint:disable=import-error
from sharedServices.model_files.app_user_models import (
    EmailVerification,
)
from sharedServices.constants import (
    INVALID_CODE,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    SECRET_KEY_IN_VALID,
    SECRET_KEY_NOT_PROVIDED,
    DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET,
    BLOCKED_USERS_EMAILS_LIST,
    GOOGLE_SIGN_IN,
    GUEST_SIGN_IN
)
from sharedServices.common import (
    hasher,
    not_valid,
    filter_function_for_base_configuration,
    randon_string_generator,
    redis_connection,
    get_node_secret
)

from .auth_utils import (
    otp_exists_for_user_function,
    register_users_cron
)
from .two_fa_apis import (
    create_third_party_and_mfg_accounts,
    create_third_party_and_mfg_accounts_ocpi,
    decode_jwt_token
)

from sharedServices.model_files.app_user_models import MFGUserEV, Profile
from sharedServices.model_files.ocpi_tokens_models import OCPITokens
from .auth_utils import generate_ocpi_token

from sharedServices.custom_jwt_handler import jwt_payload_handler
from sharedServices.model_files.app_user_models import Profile

# function to check whether user is registered or not

BLOB_CDN_URL = config("DJANGO_APP_CDN_BASE_URL")

class CreateUserTokens(APIView):
    """create ocpi token for existing user"""

    @classmethod
    def post(cls, create_user_token):
        try:
            secret_key = create_user_token.data.get("secret_key", None)

            if secret_key is None:
                return SECRET_KEY_NOT_PROVIDED
            if not handler.verify(secret_key, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET):
                return SECRET_KEY_IN_VALID
            
            users = MFGUserEV.objects.filter(~Q(user_email = ""))
            ocpi_users = set(token.user_id for token in OCPITokens.objects.all())
            
            ocpi_unregistered_users = [user for user in users if user not in ocpi_users]
            # ocpi_registered_users = [token.user_id for token in OCPITokens.objects.all()]
            # for user in users:
            #     if user.id not in ocpi_registered_users:
            #         token = generate_ocpi_token(user)

            def generate_token_for_user(user):
                try:
                    return generate_ocpi_token(user)
                except Exception as e:
                    print(f"Failed to generate token for user {user.id}: {e}")
                    return None
            
            def run_in_background(ocpi_unregistered_users):
                with ThreadPoolExecutor(max_workers=20) as executor:
                    futures = [executor.submit(generate_token_for_user, user) for user in ocpi_unregistered_users]
                    for future in as_completed(futures):
                        _ = future.result()  
            
            threading.Thread(target=run_in_background, args=(ocpi_unregistered_users,), daemon=True).start()

            return Response({
                "status_code": status.HTTP_200_OK,
                "status": True,
                "message": f"OCPITokens generated for {len(ocpi_unregistered_users)} users.",
            })

        except COMMON_ERRORS as exception:
            print(
                f"Token Creation failed -> \
                        {exception}"
            )
            return API_ERROR_OBJECT


class DeleteExpiredOTPs(APIView):
    """delete expired OTPs"""

    @classmethod
    def post(cls, delete_expire_otps):
        """delete expired OTPs"""
        try:
            secret_key = delete_expire_otps.data.get("secret_key", None)

            if secret_key is None:
                return SECRET_KEY_NOT_PROVIDED
            if not handler.verify(secret_key, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET):
                return SECRET_KEY_IN_VALID
            EmailVerification.objects.filter(
                modified_date__lte=timezone.localtime(timezone.now()) - timedelta(minutes=10)
            ).delete()
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "OTPs deleted successfully!",
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Delete expire OTP failed due to exception -> \
                        {exception}"
            )
            return API_ERROR_OBJECT


# validate OTP and register user also provide token to
# access app functionalities
@authentication_classes([])
@permission_classes([])
class SignInWithGoogleOrAppleAccountV4(APIView):
    """Create/Sign in user MFG EV app account with google or apple account"""

    @classmethod
    def post(cls, third_party_sign_in):
        """Post API call to create/sign in user MFG EV app account with google or apple account"""
        try:
            token_data = third_party_sign_in.data.get("token", False)
            user_token = third_party_sign_in.data.get("user_token", "mfgconnect")
            sso_type = third_party_sign_in.data.get("sso_type", False)
            if (
                token_data is False or
                user_token is False or
                sso_type is False
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

            profile_picture = parsed_json_data.get("picture", "")
            if email is False:
                return Response({
                    "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                    "status": False,
                    "message": "We’re experiencing issues with third-party registration. Please try using a different sign-in method",
                })
            email = email.lower()
            hashed_email = hasher(email)
            if email.endswith("@privaterelay.appleid.com"):
                return Response({
                    "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                    "status": False,
                    "message": "The provided email is invalid, please try again with different email.",
                })
            blocked_email_list = filter_function_for_base_configuration(
                BLOCKED_USERS_EMAILS_LIST, json.dumps([])
            )
            if (
                blocked_email_list and
                email in list(json.loads(blocked_email_list))
            ):
                return Response({
                    "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                    "status": False,
                    "message": "Failed to sign in",
                })
            account_creation_result = create_third_party_and_mfg_accounts_ocpi(
                hashed_email,
                email,
                "",
                first_name,
                last_name,
                None,
                None,
                None,
                profile_picture,
                user_token,
                password=handler.hash(randon_string_generator()),
                sso_type=sso_type,
                check_account=True
            )
            return Response(account_creation_result)
        except Exception as exception:# COMMON_ERRORS as exception:
            traceback.print_exc()
            print(
                f"Sign in Withh Google or Apple Account API failed for email  \
                    {email.replace(email[len(email)-10:],'**********')}-> \
                        due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


# validate OTP and sign in user, also provide token to
# access app functionalities
@authentication_classes([])
@permission_classes([])
class VerifyRegistrationOrForgetPasswordEmailOTP(APIView):
    """This API will verify registration and forget password email OTP"""

    @classmethod
    def post(cls, verify_otp_api):
        """This API will verify registration and forget password email OTP"""
        try:
            email = verify_otp_api.data.get("email", False)
            otp_sent = verify_otp_api.data.get("otp", False)
            verification_type = verify_otp_api.data.get("verification_type", False)
            if not_valid("email", email) or not otp_sent or not verification_type:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "You have to enter valid email, \
                            and OTP sent over mail.",
                    }
                )

            email = email.lower()
            otp_exists_checker = otp_exists_for_user_function(
                email, verification_type, False
            )
            if not otp_exists_checker["otp_exists"]:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "OTP has expired. Kindly request a new otp with this email",
                    }
                )

            if str(otp_exists_checker["user_otp"]) != str(otp_sent):
                print(
                    f"OTP did not found for user \
                        {email.replace(email[len(email)-10:],'**********')}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": INVALID_CODE,
                    }
                )
            print(
                f"OTP verified for user \
                        {email.replace(email[len(email)-10:],'**********')}"
            )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "OTP verified successfully.",
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Verify OTP API failed due to exception -> {exception}"
            )
            return API_ERROR_OBJECT

class ReregisterTokensCron(APIView):
    """Cronjonb API"""

    @classmethod
    def post(cls, cron_job_request):
        """Post method to initialize cron job api"""
        try:
            secret_key_azure = cron_job_request.data.get("secret_key", None)
            if secret_key_azure is None:
                return SECRET_KEY_NOT_PROVIDED
            if not handler.verify(
                secret_key_azure, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
            ):
                return SECRET_KEY_IN_VALID
            
            register_users_cron()
            
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Cron job to sync location status initiated.",
                }
            )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT


# Api for Guest user flow
@authentication_classes([])
@permission_classes([])
class RegisterGuestUser(APIView):
    """Create/Sign in user MFG EV app account with google or apple account"""

    @classmethod
    def post(cls, guest_user_request):
        """Post API call to create/sign in user MFG EV app account with google or apple account"""
        try:
            token_data = guest_user_request.data.get("token", "")
            # user_token = guest_user_request.data.get("user_token", "mfgconnect")
            # sso_type = guest_user_request.data.get("sso_type", False)
            if token_data ==  "":
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "status": False,
                        "message": "Please provide a valid device token",
                    },
                )
            guest_user = MFGUserEV.objects.filter(device_token = token_data)
            if not guest_user:
                guest_user = MFGUserEV.objects.create(device_token = token_data, sign_in_method = GUEST_SIGN_IN)
                token = generate_and_save_token(guest_user)
            else:
                token = generate_and_save_token(guest_user.first())
            
            
            return Response(
                    {
                        "status_code": status.HTTP_201_CREATED,
                        "status": True,
                        "token": token,
                        "message": "Guest user logged in successfully",
                    },
                )

        except Exception as exception:
            traceback.print_exc()
            print(
                f"Failed to register guest user \
                due to exception -> {exception}"
            )
            return API_ERROR_OBJECT
        
def generate_and_save_token(guest_user):
    """Helper function to create app access token for guest users"""
    profile= Profile.objects.filter(user=guest_user.id).first()
    token = jwt_payload_handler(guest_user)
    profile.app_access_token = token
    profile.save()
    return token
