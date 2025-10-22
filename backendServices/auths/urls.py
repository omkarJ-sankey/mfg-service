"""auths apis urls"""
# Date - 21/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on defining url
#                       path to access particular view.
#   Name            - Authentication Urls
#   Modified by     - Manish Pawar
#   Modified date   - 23/10/2024


# Imports required to make urls are below
from django.urls import path

from .apis import (
    AuthorizeUser,
    SWARCOAuth,
    UserNameChecker,
    ValidateEmailSendOTPRegister,
    ValidateOTPLogin,
    ValidateOTPRegister,
    ThirdPartyExternalAuthAPI,
)

from .build_version_apis import (
    BuildChecker,
    AppUpdateAndUnderMaintenanceChecker,
    BuildValue,
)
from .delete_account_apis import DeleteAccount, DeleteAccountOCPI, VerifyEmailForDeleteAccount
from .update_account_apis import UpdateUserData
from .forget_password_apis import (
    ChangePasswordAPI,
    VerifyEmailForForgetPassword,
    VerifyOTPAPI,
)

from .two_fa_apis import (
    SendOTPFor2FA,
    Verfiy2FAOTP,
    SendOTPFor2FAv4,
    Verfiy2FAOTPv4,
    Verfiy2FAOTPv4OCPI,
)
from .v4_apis import (
    DeleteExpiredOTPs,
    SignInWithGoogleOrAppleAccountV4,
    VerifyRegistrationOrForgetPasswordEmailOTP,
    CreateUserTokens,
    ReregisterTokensCron,
    RegisterGuestUser,
)

# Assigning Views to particular url to access there functionality
v3_urlpatterns = [
    path("", ValidateEmailSendOTPRegister.as_view()),
    path("otp-register/", ValidateOTPRegister.as_view()),
    path("otp-login/", ValidateOTPLogin.as_view()),
    path("check-username-availability/", UserNameChecker.as_view()),
    path("check-update-availabil/", BuildChecker.as_view()),
    path(
        "check-update-available/",
        AppUpdateAndUnderMaintenanceChecker.as_view(),
    ),
    path("add-mobile-build-version/", BuildValue.as_view()),
    path(
        "verify-forget-password-mail/", VerifyEmailForForgetPassword.as_view()
    ),
    path("change-password/", ChangePasswordAPI.as_view()),
    path("verify-otp/", VerifyOTPAPI.as_view()),
    path("update-data/", UpdateUserData.as_view()),
    path("delete-verification/", VerifyEmailForDeleteAccount.as_view()),
    path("delete-account/", DeleteAccount.as_view()),
    path("delete-account/", DeleteAccountOCPI.as_view()),
    path("authorize-user/", AuthorizeUser.as_view()),
    path("swarco_auth/", SWARCOAuth.as_view()),
    path("external-auth/", ThirdPartyExternalAuthAPI.as_view()),
    # enable wallet functionality/ wallet 2fa APIs
    path("send-otp-for-two-fa-auth/", SendOTPFor2FA.as_view()),
    path("verify-two-fa-auth-otp/", Verfiy2FAOTP.as_view()),
]

v4_urlpatterns = [
    # Existing API logic has been used to check email already
    # registered or not and send OTP
    path("v4/send-registration-otp/", ValidateEmailSendOTPRegister.as_view()),
    # New API logic has been created to handle Google and Apple sign in
    path("v4/third-party-sign-in/", SignInWithGoogleOrAppleAccountV4.as_view()),
    # Existing API logic has been used to check email already
    # registered or not and provide token for sign in
    path("v4/otp-login/", ValidateOTPLogin.as_view()),

    # Existing API logic has been used as the API purpose is same
    path("v4/check-update-availabil/", BuildChecker.as_view()),

    # Existing API logic has been used as the API purpose is same
    path(
        "v4/check-update-available/",
        AppUpdateAndUnderMaintenanceChecker.as_view(),
    ),

    # Existing API logic has been used as the API purpose is same
    path("v4/add-mobile-build-version/", BuildValue.as_view()),

    # Existing API logic has been used as no need to change anything in the forget password APIs
    path(
        "v4/verify-forget-password-mail/", VerifyEmailForForgetPassword.as_view()
    ),
    path("v4/verify-otp/", VerifyRegistrationOrForgetPasswordEmailOTP.as_view()),
    path("v4/change-password/", ChangePasswordAPI.as_view()),

    # New API logic has been created due to changes in request body
    path("v4/update-data/", UpdateUserData.as_view()),
    path("v4/delete-verification/", VerifyEmailForDeleteAccount.as_view()),
    path("v4/delete-account/", DeleteAccount.as_view()),
    path("v4/delete-account-ocpi/", DeleteAccountOCPI.as_view()),

    # Existing API logic has been used as the API purpose is same
    path("v4/authorize-user/", AuthorizeUser.as_view()),

    # New API logic has been created as user need to done 2FA to get logged in
    path("v4/send-otp-for-two-fa-auth/", SendOTPFor2FAv4.as_view()),
    path("v4/verify-two-fa-auth-otp/", Verfiy2FAOTPv4.as_view()),
    path("v4/verify-two-fa-auth-otp-ocpi/", Verfiy2FAOTPv4OCPI.as_view()),
    # New API created to delete expired OTPs
    path("v4/delete-expire-otps/", DeleteExpiredOTPs.as_view()),
    path("v4/create-user-tokens/", CreateUserTokens.as_view()),

    path("v4/re-register-user-tokens-cron/", ReregisterTokensCron.as_view()),
    
    #api for guest user flow
    path("v4/guest-user-login/", RegisterGuestUser.as_view())
]

urlpatterns = v3_urlpatterns + v4_urlpatterns
