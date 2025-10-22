"""delete user account APIs"""
# Date - 26/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on APIs
#                       tp delete MFG EV user account.
#   Name            - delete user account API
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 05/06/2025


# These are all the imports that we are exporting from different
# module's from project or library.
from cryptography.fernet import Fernet
from django.utils import timezone
from datetime import datetime
from datetime import timezone as datetime_timezone
from dateutil import parser
from sharedServices.common import redis_connection
import traceback
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.forms.models import model_to_dict

# pylint:disable=import-error
from sharedServices.model_files.app_user_models import (
    MFGUserEV,
    EmailVerification,
    Profile,
)
from sharedServices.model_files.charging_session_models import ChargingSession
from sharedServices.model_files.audit_models import AuditTrail

from sharedServices.constants import (
    APP_USER_DELETION,
    APP_USER_MODULE,
    DELETE_ACCOUNT,
    DELETED_ACCOUNT,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    NO,
    YES,
    EMSP_ENDPOINT,
)
from sharedServices.common import (
    array_to_string_converter,
    handle_concurrent_user_login,
    return_otp_limit,
    string_to_array_converter,
)
from sharedServices.email_common_functions import send_email_function
from sharedServices.driivz_api_gateway_functions import (
    get_driivz_api_gateway_dms_ticket
)
from backendServices.backend_app_constants import MULTIPLE_LOGIN, UNAUTHORIZED

from .auth_utils import (
    user_exists_function,
    save_otp_function,
    otp_exists_for_user_function,
    delete_driivz_customer_account_api_call
)

from sharedServices.model_files.ocpi_tokens_models import OCPITokens
from sharedServices.sentry_tracers import traced_request_with_retries
from decouple import config
from sharedServices.constants import (
    REQUEST_API_TIMEOUT,
    POST_REQUEST,
)
import json

from backendServices.charging_sessions.app_level_constants import OCPI_TOKENS_ENDPOINT
from sharedServices.model_files.config_models import BaseConfigurations
from sharedServices.constants import REQUEST_API_TIMEOUT, POST_REQUEST,CONTENT_TYPE_HEADER_KEY, JSON_DATA 
from sharedServices.common import get_node_secret

class VerifyEmailForDeleteAccount(APIView):
    """This API will verify email to delete account"""

    @classmethod
    def post(cls, delete_email_verify):
        """verify user email for account deletion"""
        try:
            email = delete_email_verify.data.get("email", False)
            resend_otp = delete_email_verify.data.get("resend_otp", False)
            reason_for_deletion = delete_email_verify.data.get(
                "reason_for_deletion", False
            )
            if not email or not delete_email_verify.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                delete_email_verify.user.id, delete_email_verify.auth
            ):
                return MULTIPLE_LOGIN
            # checking whether user have any unpaid current running
            # charging sessions or not.
            user_charging_sessions = ChargingSession.objects.filter(
                user_id=delete_email_verify.user, session_status="running"
            )
            if user_charging_sessions.first() is not None:
                print(
                    f"Cannot delete account as User -> \
                        {delete_email_verify.user.id} is having running \
                            charging session"
                )
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": "User have running charging session!",
                    }
                )
            email = str(email.lower())

            # logic to send the otp and store the email and that otp in table.
            user_exists_delete = user_exists_function(
                email, None, False, False, check_email_sign_in=False
            )
            if not user_exists_delete:
                print(
                    f"{email.replace(email[len(email)-10:],'**********')}\
                        is not registered"
                )
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": "This email is not registered",
                    }
                )

            count = save_otp_function(
                email,
                DELETE_ACCOUNT,
                None,
                resend_otp=resend_otp
            )
            if count is None:
                print(
                    f"Failed to send OTP to \
                        {email.replace(email[len(email)-10:],'**********')} \
                            for deleting account"
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
                    f"Maximum OTP limit reached for \
                        {email.replace(email[len(email)-10:],'**********')}\
                              while sending otp to delete account"
                )
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": "Maximum otp limits reached. Kindly"
                            + "contact our customer care.",
                    }
                )
            user_already_requested_otp = AuditTrail.objects.filter(
                user_id=delete_email_verify.user.id, action=APP_USER_DELETION
            )
            audit = None
            app_user_const = "App user"
            if user_already_requested_otp.first():
                audit = user_already_requested_otp.update(
                    new_data=array_to_string_converter(
                        [
                            {
                                "reason": reason_for_deletion,
                                "deleted_status": NO,
                            }
                        ]
                    )
                    if reason_for_deletion
                    else array_to_string_converter([{"deleted_status": NO}]),
                    updated_date=timezone.now(),
                )
            else:
                audit = AuditTrail.objects.create(
                    user_id=delete_email_verify.user.id,
                    action=APP_USER_DELETION,
                    module=APP_USER_MODULE,
                    new_data=array_to_string_converter(
                        [
                            {
                                "reason": reason_for_deletion,
                                "deleted_status": NO,
                            }
                        ]
                    )
                    if reason_for_deletion
                    else array_to_string_converter([{"deleted_status": NO}]),
                    data_db_id=(
                        app_user_const + str(delete_email_verify.user.id)
                    ),
                    user_name=app_user_const,
                    user_role=app_user_const,
                    module_id=delete_email_verify.user.id,
                    created_date=timezone.now(),
                    updated_date=timezone.now(),
                )

            if audit:
                print(
                    f"Delete account otp sent to user \
                        '{email.replace(email[len(email)-10:],'**********')}'"
                )
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "Otp has been sent successfully.",
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                    "status": True,
                    "message": "Something went wrong.",
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Verify Email For Delete Account failed for user ->\
                      {delete_email_verify.user.id} due to exception\
                      -> {exception}"
            )
            return API_ERROR_OBJECT


class DeleteAccount(APIView):
    """This API will delete User account"""

    @classmethod
    def post(cls, delete_account_request):
        """delete user account"""
        try:
            otp_sent = delete_account_request.data.get("otp", False)
            email = delete_account_request.data.get("email", False)
            delete_account_user = delete_account_request
            if not delete_account_user.auth:
                return Response(
                    {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "status": False,
                        "message": "Not authorized user to delete account",
                    }
                )

            if not handle_concurrent_user_login(
                delete_account_user.user.id, delete_account_user.auth
            ):
                return MULTIPLE_LOGIN
            if not email or not otp_sent:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "You have to enter email , and \
                            OTP sent over mail.",
                    }
                )

            email = email.lower()
            user_first_name = ""
            otp_exists_checker_delete = otp_exists_for_user_function(
                email, DELETE_ACCOUNT, False
            )

            if not otp_exists_checker_delete["otp_exists"]:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Email not recognised or OTP has expired. Kindly request a"
                            + "new otp with this email",
                    }
                )

            old = EmailVerification.objects.filter(
                verify_email=otp_exists_checker_delete["user_email"],
                otp_type=DELETE_ACCOUNT,
            )
            if str(otp_exists_checker_delete["user_otp"]) != str(otp_sent):
                print(
                    f"Invallid OTP entered by user \
                        {email.replace(email[len(email)-10:],'**********')}\
                             while deleting account"
                )
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": "Incorrect Verification Code.",
                    }
                )

            user_id = delete_account_request.user.id
            user_for_username = MFGUserEV.objects.filter(id=user_id).first()
            key = user_for_username.key
            decrypter = Fernet(key)
            user_first_name = decrypter.decrypt(
                user_for_username.first_name
            ).decode()
            user_data_deleted = MFGUserEV.objects.filter(id=user_id).update(
                user_email="",
                password=None,
                first_name=None,
                last_name=None,
                username=None,
                post_code=None,
                country=None,
                key=None,
                hashed_phone_number=None,
                phone_number=None,
                encrypted_email=None,
            )
            Profile.objects.filter(user_id=user_id).update(
                app_access_token=None
            )
            if not user_data_deleted:
                return Response(
                    {
                        "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                        "status": True,
                        "message": "Something went wrong.",
                    }
                )

            old.delete()
            audit = AuditTrail.objects.filter(user_id=user_id)
            reason = string_to_array_converter(audit.first().new_data)
            reason[0]["deleted_status"] = YES
            reason = array_to_string_converter(reason)
            audit.update(new_data=reason)
            send_email_function(email, DELETED_ACCOUNT, user_first_name, None)
            auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket()
            if auth_response is not None and auth_response.status_code != 200:
                return {
                    "endpoint": "/api-gateway/v1/authentication/operator/login",
                    "response": auth_response.content,
                }
            delete_customer_api_response = delete_driivz_customer_account_api_call(
                dms_ticket,
                user_for_username.user_profile.driivz_account_number,
            )
            if delete_customer_api_response.status_code == 403:
                auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket(generate_token=True)
                if auth_response is not None and auth_response.status_code != 200:
                    return {
                        "endpoint": "/api-gateway/v1/authentication/operator/login",
                        "response": auth_response.content,
                    }
                delete_driivz_customer_account_api_call(
                    dms_ticket,
                    user_for_username.user_profile.driivz_account_number
                )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Account deleted.",
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Delete Account API failed for user -> \
                    {delete_account_request.user.id} \
                    due to exception -> {exception}"
            )
            return API_ERROR_OBJECT



class DeleteAccountOCPI(APIView):
    """This API will delete User account"""

    @classmethod
    def post(cls, delete_account_request):
        """delete user account"""
        try:
            otp_sent = delete_account_request.data.get("otp", False)
            email = delete_account_request.data.get("email", False)
            delete_account_user = delete_account_request
            if not delete_account_user.auth:
                return Response(
                    {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "status": False,
                        "message": "Not authorized user to delete account",
                    }
                )

            if not handle_concurrent_user_login(
                delete_account_user.user.id, delete_account_user.auth
            ):
                return MULTIPLE_LOGIN
            if not email or not otp_sent:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "You have to enter email , and \
                            OTP sent over mail.",
                    }
                )

            email = email.lower()
            user_first_name = ""
            otp_exists_checker_delete = otp_exists_for_user_function(
                email, DELETE_ACCOUNT, False
            )



            if not otp_exists_checker_delete["otp_exists"]:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Email not recognised or OTP has expired. Kindly request a"
                            + "new otp with this email",
                    }
                )

            old = EmailVerification.objects.filter(
                verify_email=otp_exists_checker_delete["user_email"],
                otp_type=DELETE_ACCOUNT,
            )
            if str(otp_exists_checker_delete["user_otp"]) != str(otp_sent):
                print(
                    f"Invallid OTP entered by user \
                        {email.replace(email[len(email)-10:],'**********')}\
                             while deleting account"
                )
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": "Incorrect Verification Code.",
                    }
                )

            user_id = delete_account_request.user.id
            user_for_username = MFGUserEV.objects.filter(id=user_id).prefetch_related('user_profile').first()


            if user_for_username.user_profile.have_amount_due == "Yes":
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Please pay the due amount\
                            before deleting your account",
                    }
                )

            key = user_for_username.key
            decrypter = Fernet(key)
            user_first_name = decrypter.decrypt(
                user_for_username.first_name
            ).decode()
            user_data_deleted = MFGUserEV.objects.filter(id=user_id).update(
                user_email="",
                password=None,
                first_name=None,
                last_name=None,
                username=None,
                post_code=None,
                country=None,
                key=None,
                hashed_phone_number=None,
                phone_number=None,
                encrypted_email=None,
            )
            Profile.objects.filter(user_id=user_id).update(
                app_access_token=None
            )
            # if not user_data_deleted:
            #     return Response(
            #         {
            #             "status_code": status.HTTP_501_NOT_IMPLEMENTED,
            #             "status": True,
            #             "message": "Something went wrong.",
            #         }
            #     )
            

            old.delete()
            audit = AuditTrail.objects.filter(user_id=user_id)
            reason = string_to_array_converter(audit.first().new_data)
            reason[0]["deleted_status"] = YES
            reason = array_to_string_converter(reason)
            audit.update(new_data=reason)
            send_email_function(email, DELETED_ACCOUNT, user_first_name, None)
            token = get_node_secret()
            fields = [f.name for f in OCPITokens._meta.fields if f.name not in [ 'is_verified','id']]
            token_data = OCPITokens.objects.filter(user_id_id = user_id).values(*fields)
            token_date = token_data[0]
            token_date['last_updated'] = datetime.now(datetime_timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            print(f"Token data to be revoked: {json.dumps(token_date)}")
            OCPITokens.objects.filter(user_id_id=user_id).delete()

            revoke_token = traced_request_with_retries(
                POST_REQUEST,
                EMSP_ENDPOINT + OCPI_TOKENS_ENDPOINT,
                data=json.dumps(token_date),
                timeout=REQUEST_API_TIMEOUT,
                headers= {
                    CONTENT_TYPE_HEADER_KEY: JSON_DATA,
                    "Authorization": f"Token {token}"
                }
            )

            # if not revoke_token:
            #     return Response(
            #         {
            #             "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            #             "status": True,
            #             "message": "Something went wrong.",
            #         }
            #     )
            OCPITokens.objects.filter(user_id_id=user_id).update(valid=False)
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Account deleted.",
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Delete Account API failed for user -> \
                    {delete_account_request.user.id} \
                    due to exception -> {exception}"
            )
            traceback.print_exc()
            return API_ERROR_OBJECT