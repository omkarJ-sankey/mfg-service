"""Auths urls"""
# Date - 21/06/2021
# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on defining url path
#                       to access particular view.
#   Name            - Authentication Urls
#   Modified by     - Manish Pawar
#   Modified date   - 26/06/2021
# Imports required to make urls are below
from django.urls import path
from .views import (
    AdminLoginAPIView,
    AdminOTPVerificationAPIView,
    AuthorizeMFGUser,
    admin_change_password_page,
    admin_forget_password_page,
    admin_login_page,
    admin_otp_verification_page,
    admin_reset_password_page,
    logout_user,
)

# Assigning Views to particular url to access there functionality
urlpatterns = [
    path("", admin_login_page, name="AdminLogin"),
    # path("admin-login/", AdminLoginAPIView, name="AdminLogin"),
    # path(
    #     "admin-otp-verification/",
    #     admin_otp_verification_page,
    #     name="AdminOTPVerifiction",
    # ),
    path("admin-otp-verification/", AdminOTPVerificationAPIView.as_view(), name="AdminOTPVerification"),
    path(
        "admin-forget-password/",
        admin_forget_password_page,
        name="AdminForgotPassword",
    ),
    path(
        "admin-change-password/",
        admin_change_password_page,
        name="AdminChangePassword",
    ),
    path(
        "admin-reset-password/",
        admin_reset_password_page,
        name="AdminResetPassword",
    ),
    path("logout-user/", logout_user, name="logoutUser"),
    path("authorize-mfg-user/", AuthorizeMFGUser.as_view()),
]
