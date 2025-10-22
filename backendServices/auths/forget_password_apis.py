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
from passlib.hash import django_pbkdf2_sha256 as handler

from rest_framework import status
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
)
from sharedServices.constants import (
    FORGET_PASS_CONST,
    INVALID_CODE,
    COMMON_ERRORS,
    API_ERROR_OBJECT
)
from sharedServices.common import (
    return_otp_limit,
)

from .auth_utils import (
    user_exists_function,
    save_otp_function,
    otp_exists_for_user_function,
)


# validate OTP and sign in user, also provide token to
# access app functionalities
@authentication_classes([])
@permission_classes([])
class VerifyEmailForForgetPassword(APIView):
    """This API will verify email to change password of user"""

    @classmethod
    def post(cls, verify_email_forget):
        """foregt password send otp api"""
        try:
            email = verify_email_forget.data.get("email", False)
            resend_otp = verify_email_forget.data.get("resend_otp", False)
            if not email:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            "You have to enter email in order to get OTP"
                        ),
                    }
                )
            email = str(email.lower())
            # logic to send the otp and store the email and that otp in table.
            user_exists_api = user_exists_function(email, None, False, False)
            if isinstance(user_exists_api, str):
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Registration is done through social login. Please reset your password on the respective platform."
                    }
                )
            if not user_exists_api:
                print(
                    f"{email.replace(email[len(email)-10:],'**********')} \
                        is not registered"
                )
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": "This email is not registered",
                    }
                )
            count_api = save_otp_function(
                email,
                FORGET_PASS_CONST,
                None,
                resend_otp=resend_otp
            )
            if count_api is None:
                print(
                    f"Failed to send forget password OTP to \
                        {email.replace(email[len(email)-10:],'**********')}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                        "status": False,
                        "message": "Failed to send OTP.",
                    }
                )
            if count_api >= return_otp_limit():
                print(
                    f"Maximum OTP limit reached for user \
                        {email.replace(email[len(email)-10:],'**********')}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": (
                            "Maximum otp limits reached. Kindly contact our "
                            + "customer care."
                        ),
                    }
                )
            print(
                f"Forget password OTP send successfully to user \
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
                f"Verify Email For Forget Password API failed due to \
                    exception -> {exception}"
            )
            return API_ERROR_OBJECT


@authentication_classes([])
@permission_classes([])
class VerifyOTPAPI(APIView):
    """This API will verify OTP"""

    @classmethod
    def post(cls, verify_otp_api):
        """verify forget password OTP"""
        try:
            otp_sent = verify_otp_api.data.get("otp", False)
            email = verify_otp_api.data.get("email", False)
            if not email or not otp_sent:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "You have to enter email , \
                            and sent OTP over mail.",
                    }
                )

            email = email.lower()
            otp_exists_checker = otp_exists_for_user_function(
                email, FORGET_PASS_CONST, False
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
                    f"Forgot password OTP did not for user \
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
                f"Forgot password OTP verified for user \
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


@authentication_classes([])
@permission_classes([])
class ChangePasswordAPI(APIView):
    """This API will allow user to change his password"""

    @classmethod
    def post(cls, change_pwd):
        """post method to change user password after successfull
        otp verfication"""
        try:
            email = change_pwd.data.get("email", False)
            otp_sent = change_pwd.data.get("otp", False)
            password = change_pwd.data.get("password", False)
            confirm_password = change_pwd.data.get("confirm_password", False)
            if (
                not email
                or not otp_sent
                or not password
                or not confirm_password
            ):
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "You have to enter email , \
                            sent OTP over mail, and your new password with \
                                confirm password.",
                    }
                )

            email = email.lower()
            # password_validate = password_validator(password)
            if str(password) != str(confirm_password):
                print(
                    f"Password and confirm password don't match for user\
                          {email.replace(email[len(email)-10:],'**********')}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            "Password and confirm password didnt matched."
                        ),
                    }
                )
            # if not password_validate:
            #     return Response(
            #         {
            #             "status_code": status.HTTP_406_NOT_ACCEPTABLE,
            #             "status": False,
            #             "message": "Please enter password in valid format",
            #         }
            #     )
            email = str(email.lower())

            otp_exists_checker_api = otp_exists_for_user_function(
                email, FORGET_PASS_CONST, False
            )
            if not otp_exists_checker_api["otp_exists"]:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            "Email not recognised. Kindly request a new "
                            + "otp with this number"
                        ),
                    }
                )

            old = EmailVerification.objects.filter(
                verify_email=otp_exists_checker_api["user_email"],
                otp_type=FORGET_PASS_CONST,
            )
            if str(otp_exists_checker_api["user_otp"]) != str(otp_sent):
                print(
                    f"OTP didn't match for change password for user \
                            {email.replace(email[len(email)-10:],'**********')}"
                )
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": INVALID_CODE,
                    }
                )

            # logic to send the otp and store the email and that otp in table.
            user_exists = user_exists_function(email, None, False, True, check_email_sign_in=False)
            if not user_exists:
                print(
                    f" {email.replace(email[len(email)-10:],'**********')} \
                        Something went wrong please try again after some time."
                )
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": "Something went wrong please try again \
                            after some time.",
                    }
                )
            user = MFGUserEV.objects.filter(
                user_email=user_exists["user_email"]
            )
            user.update(password=handler.hash(password))
            old.delete()

            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Password changed successfully.",
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Change Password API failed due to exception -> {exception}"
            )
            return API_ERROR_OBJECT
