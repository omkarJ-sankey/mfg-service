"""Auths views"""
# Date - 26/06/2021
# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on views(backend logic)
#                       related to authentication of app user and admin user.
#   Name            - Authentication and User Views
#   Modified by     - Manish Pawar
#   Modified date   - 26/06/2021

# imports required to create views
from urllib.parse import urlencode
from passlib.hash import django_pbkdf2_sha256 as handler
from cryptography.fernet import Fernet

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

import jwt

from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_http_methods

# pylint:disable=import-error
from sharedServices.model_files.admin_user_models import (
    AdminAuthorization,
    AdminUser,
    LoginRecords,
)
from sharedServices.model_files.app_user_models import MFGUserEV
from sharedServices.common import (
    generate_token_func,
    email_validator,
    password_validator,
    set_token_cache,
)
from sharedServices.email_common_functions import (
    send_otp
)
from sharedServices.constants import (
    FORGET_PASS_CONST,
    ADMIN_OTP,
    YES,
    NO,
    GET_METHOD_ALLOWED,
    POST_METHOD_ALLOWED,
    COMMON_ERRORS,
    ERROR_TEMPLATE_URL,
    API_ERROR_OBJECT,
)
from sharedServices.decorators import authenticated_user, unauthenticated_user
from sharedServices.routes_constants import LOGIN_ADMIN

# This view is used to authenticate user, this view checks
# whether user with the given email is present in
# database or not.
#   if yes- then OTP will be sent to user via email.
#   else - error of email is invalid i shown to user.


@unauthenticated_user
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
def admin_login_page(request):
    """admin login function"""
    try:
        if request.method == "POST":
            # Getting data from request
            email = request.POST.get("email")
            password = request.POST.get("password")
            # checking validation of email and password
            email_validate = email_validator(email)
            password_validate = password_validator(password)
            # Conidition to check whether email and ppassword are valid or not.
            if email_validate is False:
                messages.warning(
                    request, "Please provide email with right format"
                )
                return render(request, LOGIN_ADMIN)

            if password_validate is False:
                messages.warning(
                    request,
                    "Password length should be more than 8, \
                        and must contain one uppercase letter, one lowercase \
                            and one special character.",
                )
                return render(request, LOGIN_ADMIN)

            # Checking whether user with given email is
            # present in database or not.
            user = AdminUser.objects.filter(email=email)
            if (
                user.first() is not None
                and user.first().first_time_login == YES
            ):
                base_url = reverse("AdminResetPassword")
                query_string = urlencode({"user_id": user.first().id})
                url = f"{base_url}?{query_string}"
                return redirect(url)

            login_status = LoginRecords.objects.filter(user_id=user.first())
            if login_status.first() is None:
                LoginRecords.objects.create(
                    user_id=user.first(),
                    current_status="Active",
                    updated_date=timezone.localtime(timezone.now()),
                )
                messages.warning(request, "Try once again.")
            elif login_status.first().current_status == "Active":
                if len(user) > 0:
                    # If user with given mail is present then we will fetch
                    # user password from 'AdminAuthorization table
                    # and compare with the user entered password
                    user_auth_data = AdminAuthorization.objects.get(
                        user_id=user[0].id
                    )
                    if handler.verify(password, user_auth_data.password):

                        # The send_otp function send email to user
                        # containing the OTP to authenticate himself/herself.
                        otp = send_otp(
                            user[0].email, user[0].full_name, ADMIN_OTP
                        )
                        if otp:
                            # We have maintained the otp field
                            # in 'AdminAuthorization'table so following code
                            # update the otp field with new
                            # generated otp.
                            AdminAuthorization.objects.filter(
                                user_id=user[0].id
                            ).update(otp=otp, otp_type=ADMIN_OTP)
                            login_status.update(
                                updated_date=timezone.localtime(timezone.now())
                            )
                            # The following code will redirect admin user
                            # to OTP verification page
                            base_url = reverse("AdminOTPVerifiction")
                            query_string = urlencode({"user_id": user[0].id})
                            url = f"{base_url}?{query_string}"
                            return redirect(url)
                        messages.warning(request, "Failed sending email")
                    else:
                        messages.warning(
                            request, "please enter valid password"
                        )
                messages.warning(request, "Email not found ")
            else:
                messages.warning(request, "The account is deactivated.")

            return render(request, LOGIN_ADMIN)
        return render(request, LOGIN_ADMIN)
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


def send_otp_function(user_id):
    """send otp"""
    user = AdminUser.objects.get(id=user_id)
    otp = send_otp(user.email, user.full_name, ADMIN_OTP)
    AdminAuthorization.objects.filter(user_id=user_id).update(
        otp=otp, otp_type=ADMIN_OTP
    )


def store_token_browser(token_data, user_filter_data, request):
    """store token browser"""
    response = redirect("dashboard")
    response = set_token_cache(token_data, request, response, user_filter_data)
    return response


def store_token(user_id, user_filter_data, request):
    """store token"""
    token_data = generate_token_func(user_id, user_filter_data.first().id)
    # saving token in AdminAuthorization
    # table for the logged in user.
    user_filter_data.update(
        otp="",
        token=token_data[0],
        token_secret=token_data[1],
        refresh_token=token_data[3],
        token_expire_time=token_data[2],
    )
    return store_token_browser(token_data, user_filter_data, request)


# This view verifies entered OTP with the database OTP.
@unauthenticated_user
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
def admin_otp_verification_page(request):
    """admin otp verification view"""
    # Fetching user id to verify entered OTP with user's saved
    # otp in AdminAuthorization table
    try:
        user_id = request.GET.get("user_id")
        resend_otp = request.GET.get("resend_otp")
        if resend_otp == YES and request.method != "POST":
            send_otp_function(user_id)
            messages.success(request, "OTP sent on your email.")
        # Post method to make operation sequerely.

        if request.method == "POST":
            # Filter user data from AdminAuthorization table.
            user_filter_data = AdminAuthorization.objects.filter(
                user_id=user_id, otp_type=ADMIN_OTP
            )
            if len(user_filter_data) > 0:
                user_data = user_filter_data.first()
                # getting OTP from post request
                otp = request.POST.get("otp")
                # Comparing OTP with the sent OTP
                if str(otp) == str(user_data.otp) and len(otp) == 4:
                    token = user_filter_data.first().token
                    refresh_token = user_filter_data.first().refresh_token
                    token_secret = user_filter_data.first().token_secret
                    token_expire_time = (
                        user_filter_data.first().token_expire_time
                    )
                    payload = {"user_id": None}
                    if token and refresh_token:
                        try:
                            payload = jwt.decode(
                                token, token_secret, algorithms=["HS256"]
                            )
                        except jwt.InvalidTokenError:
                            try:
                                payload = jwt.decode(
                                    refresh_token,
                                    token_secret,
                                    algorithms=["HS256"],
                                )
                            except jwt.InvalidTokenError:
                                return store_token(
                                    user_id, user_filter_data, request
                                )

                    if (
                        user_id == payload["user_id"]
                        and token
                        and refresh_token
                    ):
                        token_data = []
                        token_data.append(token)
                        token_data.append(token_secret)
                        token_data.append(token_expire_time)
                        token_data.append(refresh_token)
                        return store_token_browser(
                            token_data, user_filter_data, request
                        )

                    # Following logic will generate token and
                    # save in AdminAuthorization table also this token will
                    # be set inside the cookie so that we
                    #  can authorize user later.
                    return store_token(user_id, user_filter_data, request)

                # Informing user what's wrong with the OTP that
                # they have entered.
                if len(otp) != 4:
                    messages.warning(
                        request, "OTP has to be at least of length 4"
                    )
                else:
                    messages.warning(request, "Invalid OTP")
            else:
                return redirect("AdminLogin")
        updated_url = f"&user_id={user_id}"
        return render(request, "auths/otp.html", context={"url": updated_url})
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


# This view will be used if user forgots his password and want to
# change his password.
@unauthenticated_user
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
def admin_forget_password_page(request):
    """admin forget password view"""
    # Post method to securely make database queries.
    try:
        if request.method == "POST":

            # Getting email from post request.
            email = request.POST.get("email")

            # Fetching user with given email
            user = AdminUser.objects.filter(email=email).first()

            # Checking whether email is in valid format or not.
            email_validate = email_validator(email)
            if email_validate:
                # Condition to check whether user with given
                #  mail is present or not
                if user:
                    # OTP will be sent to user so that we can verify user.
                    otp = send_otp(
                        user.email, user.full_name, FORGET_PASS_CONST
                    )

                    # saving newly generated OTP inside a database.
                    AdminAuthorization.objects.filter(user_id_id=user.id).update(
                        otp=otp, otp_type="forgotPassword"
                    )

                    # Redirecting user to change password page.
                    base_url = reverse("AdminChangePassword")
                    query_string = urlencode({"user_id": user.id})
                    url = f"{base_url}?{query_string}"
                    return redirect(url)
                messages.warning(request, "Your email is not authorized")
            else:
                messages.warning(
                    request, "Please provide email in correct format"
                )
        return render(request, "auths/forget_password.html")
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


# This view comes under Forget password functionality, once user verifies him
# email the user will redirect to this view.
@unauthenticated_user
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
def admin_change_password_page(request):
    """admin panel change password view"""
    # Fetching the user id
    try:
        user_id = request.GET.get("user_id")
        # Post method to make queries securely.
        if request.method == "POST":
            # Filter user data from AdminAuthorization table.
            user_filter_data = AdminAuthorization.objects.filter(
                user_id=user_id, otp_type="forgotPassword"
            )
            if len(user_filter_data) > 0:
                user_data = user_filter_data.first()
                otp = request.POST.get("otp")
                password = request.POST.get("password")
                confirm_password = request.POST.get("change_password")

                # Password validator to check whether password is valid or not.
                password_validate = password_validator(password)
                # Condition to check whether password and
                # confirm_password are same or not
                if (
                    str(password) == str(confirm_password)
                    and len(otp) == 4
                    and password_validate
                ):
                    if str(otp) == str(user_data.otp):
                        hashed_password = handler.hash(password)
                        user_filter_data.update(
                            otp="", password=hashed_password
                        )
                        messages.success(
                            request, "Password changed successfully."
                        )
                        return redirect("AdminLogin")
                    messages.warning(request, "Invalid OTP")
                else:
                    # informing user about what went wrong while
                    # performing operation.
                    if len(otp) != 4:
                        messages.warning(
                            request, "OTP has to be at least of length 4"
                        )
                    if password_validate is False:
                        messages.warning(
                            request,
                            "Password length should be more than 8, \
                            and must contain one uppercase letter, one \
                            lowercase and one special character. ",
                        )
                    else:
                        messages.warning(
                            request,
                            "Password and change password doesn't matched",
                        )

            else:
                # If user with user_id doesn't exists in authorization table
                messages.warning(request, "User doesn't exists.")
        return render(request, "auths/change_password.html")
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


# This view will be used to reset password.
@unauthenticated_user
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
def admin_reset_password_page(request):
    """admin panel  reset view"""
    try:
        user_id = request.GET.get("user_id")
        user_exists = AdminUser.objects.filter(id=user_id)
        if not user_exists.first():
            return redirect("AdminLogin")
        # Post request to make queries securely.
        if request.method == "POST":
            # Getting post data from frontend
            password = request.POST.get("password")
            confirm_password = request.POST.get("change_password")
            # Password validator to check whether password is valid or not.
            password_validate = password_validator(password)

            # Fetching an user and then if password and
            # confirm_password matched then
            # we will update the password.
            user_auth_data = AdminAuthorization.objects.filter(
                user_id_id=user_id
            )
            if str(password) == str(confirm_password) and password_validate:
                user_data = AdminUser.objects.filter(id__exact=user_id)
                user_data.update(first_time_login=NO)
                hashed_password = handler.hash(password)
                user_auth_data.update(password=hashed_password)
                # on successful updation user will be redirected to dashboard.
                messages.success(request, "Password changed successfully.")
                token_data = generate_token_func(
                    user_id, user_auth_data.first().id
                )

                # saving token in AdminAuthorization
                # table for the logged in user.
                user_auth_data.update(
                    otp="",
                    token=token_data[0],
                    token_secret=token_data[1],
                    refresh_token=token_data[3],
                    token_expire_time=token_data[2],
                )
                response = redirect("dashboard")
                # setting cookie for token

                response = set_token_cache(
                    token_data, request, response, user_auth_data
                )

                return response
            # Inform user about errors
            if password_validate:
                messages.warning(
                    request, "Password and change password doesnt matched"
                )
            else:
                messages.warning(
                    request,
                    "Password length should be more than 8,\
                    and must contain one uppercase letter, one\
                        lowercase and one special character. ",
                )
        return render(request, "auths/reset_password.html")
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


# This view will logout user.
@authenticated_user
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
def logout_user(_):
    """logout admin user"""
    # deleting cookie containing Token.
    response = redirect("AdminLogin")
    response.delete_cookie("token")
    return response


class AuthorizeMFGUser(APIView):
    """AUthorize MFG User (SWARCO extrenal auth)"""

    @classmethod
    def post(cls, request):
        """post method for authorising user"""
        try:
            email = request.data.get("email", False)
            password = request.data.get("password", False)

            if email and password:
                user_exists_data = MFGUserEV.objects.filter(
                    Q(user_email=str(email), password=str(password))
                )
                if user_exists_data.first():
                    decrypter = Fernet(user_exists_data.first().key)
                    user_first_name = decrypter.decrypt(
                        user_exists_data.first().first_name
                    ).decode()
                    user_last_name = decrypter.decrypt(
                        user_exists_data.first().last_name
                    ).decode()
                    return Response(
                        {
                            "status_code": status.HTTP_200_OK,
                            "status": True,
                            "data": {
                                "authorized": True,
                                "first_name": user_first_name,
                                "last_name": user_last_name,
                            },
                        }
                    )
                return Response(
                    {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "status": False,
                        "error": [
                            "Unauthorized",
                            {
                                "id": "unauthorized",
                                "detail": "Email and or password \
                                    are not valid",
                            },
                        ],
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "status": False,
                    "error": [
                        {
                            "id": "missing_parameters",
                            "detail": "Email and password are required",
                        }
                    ],
                }
            )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT
