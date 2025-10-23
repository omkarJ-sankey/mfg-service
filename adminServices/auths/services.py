from django.utils import timezone
from django.urls import reverse
from urllib.parse import urlencode
from sharedServices.common import generate_token_func
from sharedServices.model_files.admin_user_models import (
    AdminAuthorization,
    AdminUser,
    LoginRecords,
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
from passlib.handlers.pbkdf2 import pbkdf2_sha256 as handler

from sharedServices.constants import ConstantMessage


def admin_login_service(validated_data):
    email = validated_data.get("email")
    password = validated_data.get("password")

    user = AdminUser.objects.filter(email=email).first()
    if not user:
        return {"status": False, "message": ConstantMessage.EMAIL_NOT_FOUND}

    if user.first_time_login == YES:
        return {"status": False, "message": ConstantMessage.FIRST_TIME_LOGIN, "first_time_login": True}

    login_status = LoginRecords.objects.filter(user_id=user).first()
    if login_status is None:
        LoginRecords.objects.create(
            user_id=user,
            current_status="Active",
            updated_date=timezone.localtime(timezone.now()),
        )
        return {"status": False, "message": ConstantMessage.TRY_AGAIN}

    if login_status.current_status != "Active":
        return {"status": False, "message": ConstantMessage.ACCOUNT_DEACTIVATED}

    user_auth_data = AdminAuthorization.objects.get(user_id=user.id)
    if not handler.verify(password, user_auth_data.password):
        return {"status": False, "message": ConstantMessage.INVALID_PASSWORD}

    otp = send_otp(user.email, user.full_name, ADMIN_OTP)
    if not otp:
        return {"status": False, "message": ConstantMessage.FAILED_SENDING_EMAIL}

    AdminAuthorization.objects.filter(user_id=user.id).update(otp=otp, otp_type=ADMIN_OTP)
    login_status.updated_date = timezone.localtime(timezone.now())
    login_status.save()

    return {"status": True, "message": ConstantMessage.OTP_SENT_SUCCESSFULLY}


def admin_otp_verification_service(validated_data):
    user_id = validated_data.get("user_id")
    otp_entered = validated_data.get("otp")

    user_filter_data = AdminAuthorization.objects.filter(user_id=user_id, otp_type="ADMIN_OTP")
    if not user_filter_data.exists():
        return {"status": False, "message": ConstantMessage.USER_NOT_FOUND}

    user_data = user_filter_data.first()

    if str(otp_entered) != str(user_data.otp):
        return {"status": False, "message": ConstantMessage.INVALID_OTP}

    # OTP verified successfully
    # Generate and store token
    token_data = generate_token_func(user_id, user_data.id)
    user_filter_data.update(
        otp="",
        token=token_data[0],
        token_secret=token_data[1],
        refresh_token=token_data[3],
        token_expire_time=token_data[2],
    )

    return {
        "status": True,
        "message": ConstantMessage.OTP_VERIFIED_SUCCESSFULLY,
        "data": {
            "token": token_data[0],
            "refresh_token": token_data[3],
            "token_secret": token_data[1],
            "token_expire_time": token_data[2]
        }
    }
