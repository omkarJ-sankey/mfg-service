"""authentication APIs"""
# Date - 26/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on APIs
#                       related to authentication of MFG EV app user.
#   Name            - App athentication API
#   Modified by     - Shivkumar Kumbhar
#   Modified date   - 29/03/2023


# These are all the imports that we are exporting from different
# module's from project or library.
# pylint:disable=import-error
import json
from decouple import config

from passlib.hash import django_pbkdf2_sha256 as handler

from rest_framework import status
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
)
from rest_framework.views import APIView

# pylint:disable=import-error
from sharedServices.model_files.app_user_models import (
    MFGUserEV,
    EmailVerification,
    Profile,
)
from sharedServices.model_files.third_party_users_models import (
    ThirdPartyCredentials,
)
from sharedServices.constants import (
    INVALID_CODE,
    REGISTER,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    EMAIL_SIGN_IN
)
from sharedServices.common import (
    handle_concurrent_user_login,
    hasher,
    return_otp_limit,
    not_valid,
)

from sharedServices.custom_jwt_handler import jwt_payload_for_third_party_user
from backendServices.charging_sessions.swarco_apis import (
    swarco_user_authentication_using_refresh_token,
    swarco_generate_tokens_for_new_user,
)
from backendServices.backend_app_constants import MULTIPLE_LOGIN, UNAUTHORIZED
from .serializers import UserLoginSerializer
from .two_fa_apis import (
    create_third_party_and_mfg_accounts
)
from .auth_utils import (
    user_exists_function,
    save_otp_function,
    otp_exists_for_user_function,
)

# function to check whether user is registered or not

BLOB_CDN_URL = config("DJANGO_APP_CDN_BASE_URL")

#################################################
###           Registration part               ###


# view to validate user email for registration
@authentication_classes([])
@permission_classes([])
class UserNameChecker(APIView):
    """unique user name cheker"""

    @classmethod
    def post(cls, user_name_check):
        """post method to check username uniquness"""
        try:
            username = user_name_check.data.get("username")
            if username is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Please enter username",
                    }
                )
            user_exists = MFGUserEV.objects.filter(username=username)
            if user_exists.first() is None:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "Username is available",
                    }
                )
            print(f"Username -> '{username}' already exists")
            return Response(
                {
                    "status_code": status.HTTP_403_FORBIDDEN,
                    "status": False,
                    "message": "This username is already exists",
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"User Name Checker API failed due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


@authentication_classes([])
@permission_classes([])
class ValidateEmailSendOTPRegister(APIView):
    """
    This class view takes email number and if it doesn't exists
    already then it sends otp"""

    @classmethod
    def get(cls, _):
        """This a get method added to avoid error when someone
        hits the url with get method"""
        return Response(
            {
                "status_code": status.HTTP_200_OK,
                "message": "Server is running!",
            }
        )

    @classmethod
    def post(cls, validate_send_otp_post):
        """post method to send otp to user"""
        try:
            email = validate_send_otp_post.data.get("email")
            first_name = validate_send_otp_post.data.get("first_name")
            resend_otp = validate_send_otp_post.data.get("resend_otp", False)
            if not_valid("email", email) or first_name is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            "You have to enter valid email and first name in order to get OTP"
                        ),
                    }
                )
            email = email.lower()

            user_exists = user_exists_function(email, None, False, False)
            if user_exists:
                print(
                    f"{email.replace(email[len(email)-10:],'**********')} \
                        is already registered"
                )
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": "This email is already registered",
                    }
                )
            # logic to send the otp and store the email and that otp in table.
            count = save_otp_function(email, REGISTER, first_name, resend_otp=resend_otp)
            if count is None:
                print(
                    f"Failed to send register OTP to \
                        {email.replace(email[len(email)-10:],'**********')}"
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
                    f"Maximum OTP limit reached for email \
                        {email.replace(email[len(email)-10:],'**********')}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": "Maximum otp limits reached. Kindly contact"
                            + "our customer care or try with different email",
                    }
                )
            print(
                f"Register OTP sent successfully to \
                        {email.replace(email[len(email)-10:],'**********')}"
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
                f"Validate Email Send OTP Register API failed due to \
                    exception -> {exception}"
            )
            return API_ERROR_OBJECT


# validate OTP and register user also provide token to access app functionalities
@authentication_classes([])
@permission_classes([])

class ValidateOTPRegister(APIView):
    """
    If you have received otp, post a request with number
        , fname , lname and that otp and
        you will be signed up
    """

    @classmethod
    def post(cls, validate_otp):
        """validte otp entered by user and logged in user"""
        try:
            email = validate_otp.data.get("email", False)
            otp_sent = validate_otp.data.get("otp", False)
            first_name = validate_otp.data.get("first_name", False)
            last_name = validate_otp.data.get("last_name", False)
            user_name = validate_otp.data.get("user_name", False)
            password = validate_otp.data.get("password", False)
            postal_code = validate_otp.data.get("postal_code", False)
            country = validate_otp.data.get("country", False)
            user_token = validate_otp.data.get("user_token", "mfgconnect")
            invalid_register_condition = (
                not_valid("email", email)
                or not_valid("otp", otp_sent)
                or not_valid("name", first_name)
                or not_valid("name", last_name)
                or not_valid("user_name", user_name)
                or not_valid("password", password)
                or postal_code
                or not_valid("country", country)
                or not_valid("user_token", user_token)
            )
            if invalid_register_condition is True:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            "Please provide all valid fields. Username, "
                            + "First name, last name, email , "
                            + "country, postal code "
                            + ", password and OTP are mandatory for "
                            + "registration."
                        ),
                    },
                )

            if user_token is False:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Please try to register again.",
                    },
                    # status = status.HTTP_406_NOT_ACCEPTABLE
                )
            email = email.lower()
            # password_validate = password_validator(password)
            # if not password_validate:
            #     return Response(
            #         {
            #             "status_code": status.HTTP_406_NOT_ACCEPTABLE,
            #             "status": False,
            #             "message": "Please enter password in valid format",
            #         },
            #         status = status.HTTP_406_NOT_ACCEPTABLE
            #     )
            otp_exists_checker = otp_exists_for_user_function(
                email, REGISTER, False
            )
            if not otp_exists_checker["otp_exists"]:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "You might have not requested for the OTP,\
                            in order to  registered with this app please \
                                request for OTP",
                    },
                    # status = status.HTTP_406_NOT_ACCEPTABLE
                )
            old = EmailVerification.objects.filter(
                verify_email=otp_exists_checker["user_email"],
                otp_type=REGISTER,
            )
            if str(otp_exists_checker["user_otp"]) != str(otp_sent):
                print(
                    f"{email.replace(email[len(email)-10:],'**********')} \
                        has entered wrong OTP to register"
                )
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": INVALID_CODE,
                    },
                    # status = status.HTTP_406_NOT_ACCEPTABLE
                )
            old.delete()
            hashed_email = hasher(email)
            hashed_password = handler.hash(password)
            account_creation_result = create_third_party_and_mfg_accounts(
                hashed_email,
                email,
                "",
                first_name,
                last_name,
                user_name,
                country,
                postal_code,
                None,
                user_token,
                password=hashed_password,
                sso_type=EMAIL_SIGN_IN,
                v3_registration=True
            )
            return Response(account_creation_result)
        except COMMON_ERRORS as exception:
            print(
                f"Validate OTP Register API failed for user \
                    {email.replace(email[len(email)-10:],'**********')}-> \
                        due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


##########################################
###           Login part               ###


# validate OTP and sign in user, also provide token
# to access app functionalities
@authentication_classes([])
@permission_classes([])
class ValidateOTPLogin(APIView):
    """If you have received otp, post a request with email and that otp to
    complete sign in for the app"""

    serializer_class = UserLoginSerializer

    def post(self, validate_otp_login):
        """user login api"""
        try:
            email = validate_otp_login.data.get("email", False)
            password = validate_otp_login.data.get("password", False)
            user_token = validate_otp_login.data.get(
                "user_token", "mfgconnect"
            )
            if not_valid("user_token", user_token):
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Please try to login again.",
                    }
                )

            if not_valid("email", email) or not_valid("password", password):
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Please enter valid email and password.",
                    }
                )

            email = email.lower()
            user_exists_data = user_exists_function(
                email, password, True, True
            )
            if isinstance(user_exists_data, str):
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Registration is done through social login. Please sign in using the respective platform.",
                    }
                )
            if isinstance(user_exists_data, dict) and not user_exists_data["user_exists"]:
                if not user_exists_data["email_verified"]:
                    print(
                        f"{email.replace(email[len(email)-10:],'**********')}\
                             is not registered"
                    )
                    return Response(
                        {
                            "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                            "status": False,
                            "message": "Email is not registered.",
                        }
                    )
                if not user_exists_data["password_verified"]:
                    print(
                        f"{email.replace(email[len(email)-10:],'**********')}\
                             entered incorrect password"
                    )
                    return Response(
                        {
                            "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                            "status": False,
                            "message": "Password is not correct.",
                        }
                    )
                return Response(
                    {
                        "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                        "status": False,
                        "message": "Something went wrong.",
                    }
                )
            serializer = self.serializer_class(
                data={
                    "email": user_exists_data["user_email"],
                    "password": user_exists_data["password"],
                    "user_token": user_token,
                    "sso_type": "Email Sign In",
                    "check_2fa": 'v4' in validate_otp_login.build_absolute_uri(),
                    "v3_registration": False
                }
            )

            if serializer.is_valid():
                response = {
                    "success": True,
                    "status_code": status.HTTP_200_OK,
                    "message": "User logged in  successfully",
                    "token": serializer.data["token"],
                    "email": user_exists_data["email"],
                    "first_name": user_exists_data["user_first_name"],
                    "last_name": user_exists_data["user_last_name"],
                    "user_name": user_exists_data["user_name"],
                    "user_country": user_exists_data["user_country"],
                    "user_post_code": user_exists_data["user_post_code"],
                    "profile_picture": user_exists_data["profile_picture"],
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
                }
                status_code = status.HTTP_200_OK

                return Response(response, status=status_code)

            error_message = "Invalid data provided"
            if serializer.errors.get("non_field_errors"):
                error_message = str(serializer.errors.get("non_field_errors"))
                error_message = error_message.split(",", maxsplit=1)[0]
                error_message = error_message.replace("'", "")
                error_message = error_message.split("[ErrorDetail(string=")[1]
            return Response(
                {
                    "status_code": status.HTTP_403_FORBIDDEN,
                    "status": False,
                    "message": error_message,
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Validate OTP login APIs failed for user \
                    {email.replace(email[len(email)-10:],'**********')}-> \
                        due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


class AuthorizeUser(APIView):
    """authorize user"""

    @classmethod
    def post(cls, authorize_request):
        """check whether user has logged in or not"""
        try:
            update_auth_request = authorize_request
            if not update_auth_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                update_auth_request.user.id, update_auth_request.auth
            ):
                return MULTIPLE_LOGIN
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Authorized.",
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Authorize user API failed for user -> \
                    {authorize_request.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


class SWARCOAuth(APIView):
    """SWARCO extrenal auth"""

    permission_classes = [permissions.IsAuthenticated]

    @classmethod
    def post(cls, swarco_auth):
        """post method to authenticate user for SWARCo"""
        try:
            swarco_request = swarco_auth
            if not swarco_request:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                swarco_request.user.id, swarco_request.auth
            ):
                return MULTIPLE_LOGIN
            profile = Profile.objects.filter(user=swarco_auth.user)

            if profile.first() is None:
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "status": False,
                        "data": "Bad request.",
                    }
                )
            response = swarco_user_authentication_using_refresh_token(
                profile, swarco_auth.user
            )
            if response.status_code == 200:
                content = json.loads(response.content)
                profile_updated = profile.update(
                    swarco_token=content["access_token"],
                    swarco_refresh_token=content["refresh_token"],
                )
                if profile_updated:
                    return Response(
                        {
                            "status_code": status.HTTP_200_OK,
                            "status": True,
                            "data": content,
                        }
                    )
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "status": False,
                        "message": "Unable to process request.",
                    }
                )
            auth_response = swarco_generate_tokens_for_new_user(
                swarco_auth.user
            )
            if auth_response.status_code == 200:
                content = json.loads(auth_response.content)
                profile_updated = profile.update(
                    swarco_token=content["access_token"],
                    swarco_refresh_token=content["refresh_token"],
                )
                if profile_updated:
                    return Response(
                        {
                            "status_code": status.HTTP_200_OK,
                            "status": True,
                            "data": content,
                        }
                    )
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "status": False,
                        "message": "Unable to process request.",
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "status": False,
                    "message": "Failed to authenticate user \
                        by third party.",
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Swarco auth api failed for user -> \
                    {swarco_auth.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


class ThirdPartyExternalAuthAPI(APIView):
    """Generate tokens for third party user"""

    def post(self, request):
        """post method to get request body"""
        try:
            username = request.data.get("username", None)
            password = request.data.get("password", None)
            refresh_token = request.data.get("refresh_token", None)
            grant_type = request.data.get("grant_type", None)
            if grant_type is None:
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "status": False,
                        "message": (
                            "Please provide grant type for authentication"
                        ),
                    }
                )
            if grant_type == "refresh_token":
                if not refresh_token:
                    return Response(
                        {
                            "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                            "status": False,
                            "message": "Refresh token not provided!",
                        }
                    )
                third_party_user = ThirdPartyCredentials.objects.filter(
                    refresh_token=str(refresh_token)
                )
                if third_party_user.first() is None:
                    return Response(
                        {
                            "status_code": status.HTTP_401_UNAUTHORIZED,
                            "status": False,
                            "message": "Not authorized!",
                        }
                    )
            if grant_type == "password":
                if not username or not password:
                    return Response(
                        {
                            "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                            "status": False,
                            "message": "Please provide username and password!",
                        }
                    )
                third_party_user = ThirdPartyCredentials.objects.filter(
                    username=username
                )
                if third_party_user.first() is None:
                    print(
                        f"Third party user with username -> '{username}' not found"
                    )
                    return Response(
                        {
                            "status_code": status.HTTP_404_NOT_FOUND,
                            "status": False,
                            "message": (
                                "User with provided username not found!"
                            ),
                        }
                    )
                if not handler.verify(
                    password, third_party_user.first().password
                ):
                    print(
                        f"Incorrect password by {third_party_user.first().id} \
                            for third party user Authentication"
                    )
                    return Response(
                        {
                            "status_code": status.HTTP_400_BAD_REQUEST,
                            "status": False,
                            "message": "Password is incorrect!",
                        }
                    )

            token, refresh_token = jwt_payload_for_third_party_user(
                third_party_user.first().user_id
            )
            third_party_user.update(token=token, refresh_token=refresh_token)
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "User verified successfully!",
                    "data": {"token": token, "refresh_token": refresh_token},
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Third party external auth api failed for third party user ->\
                      {third_party_user.first().id} due to exception -> \
                        {exception}"
            )
            return API_ERROR_OBJECT
