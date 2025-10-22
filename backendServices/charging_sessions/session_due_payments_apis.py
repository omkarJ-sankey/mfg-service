"""charging sessions payment apis"""
# Date - 29/09/2022

# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on APIs
#                       related to charging session payments.
#   Name            - chrging session payment APIs
#   Modified by     - Shivkumar Kumbhar
#   Modified date   - 29/03/2023


# These are all the imports that we are exporting from different
# module's from project or library.
import threading
import concurrent.futures
from passlib.hash import django_pbkdf2_sha256 as handler

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

# pylint:disable=import-error
from backendServices.backend_app_constants import (
    MULTIPLE_LOGIN,
    UNAUTHORIZED,
)
from sharedServices.model_files.charging_session_models import ChargingSession
from sharedServices.model_files.app_user_models import Profile
from sharedServices.common import (
    handle_concurrent_user_login,
    string_to_array_converter,
)
from sharedServices.common_session_functions import (
    send_charging_payment_mail,
    get_user_due_amount_for_session,
)
from sharedServices.constants import (
    YES,
    AMOUNT_DUE_REMINDER_TEMPLATE_ID,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    CHARGING_SESSION,
    SECRET_KEY_IN_VALID,
    SECRET_KEY_NOT_PROVIDED,
    DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET,
)
from .session_helper_functions import handle_user_due_payment


class MakeDueSessionPayment(APIView):
    """this API is used to make payments
    for failed session payments"""

    @classmethod
    def post(cls, make_due_session_payment_request):
        """post method to initialize payment"""
        try:
            if not make_due_session_payment_request.auth:
                return UNAUTHORIZED
            if not handle_concurrent_user_login(
                make_due_session_payment_request.user.id,
                make_due_session_payment_request.auth,
            ):
                return MULTIPLE_LOGIN
            handle_user_due_payment_response = handle_user_due_payment(
                make_due_session_payment_request
            )
            if handle_user_due_payment_response:
                return Response(handle_user_due_payment_response)
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Payment successful.",
                }
            )
        except COMMON_ERRORS as error:
            print(
                "Make due session payment API failed for user ->"
                + f"{make_due_session_payment_request.user.id}"
                + f"due to error -> {error}"
            )
            return API_ERROR_OBJECT


def send_due_payment_reminder_emails():
    """this function sends due payment reminder emails"""
    due_amount_users = Profile.objects.filter(have_amount_due=YES)
    session_ids = []
    if due_amount_users.first():
        session_ids = [
            int(session_data["reference_id"])
            for user in due_amount_users
            for session_data in string_to_array_converter(user.due_amount_data)
            if (
                int(session_data["amount"]) > 0
                and session_data["amount_due_for"] == CHARGING_SESSION
            )
        ]
    due_payment_sessions = ChargingSession.objects.filter(
        id__in=session_ids,
    )

    def send_due_payment_reminder_email(charging_session):
        """this function sends due payment reminder emails"""

        due_amount = get_user_due_amount_for_session(
            charging_session.user_id, charging_session.id
        )
        send_due_amount_reminder_email = send_charging_payment_mail(
            charging_session.id,
            template_id=AMOUNT_DUE_REMINDER_TEMPLATE_ID,
            due_amount=due_amount,
        )
        if send_due_amount_reminder_email:
            print(
                f"Due payment reminder email sent for user -> {charging_session.user_id}"
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(
            send_due_payment_reminder_email,
            list(due_payment_sessions),
        )


class SendDuePaymentMails(APIView):
    """cronjonb API to send due payment mails"""

    @classmethod
    def post(cls, cron_job_request):
        """post method to initialize cron job api"""
        secret_key_azure = cron_job_request.data.get("secret_key", None)
        if secret_key_azure is None:
            return SECRET_KEY_NOT_PROVIDED
        if not handler.verify(
            secret_key_azure, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
        ):
            return SECRET_KEY_IN_VALID

        start_time = threading.Thread(
            target=send_due_payment_reminder_emails,
            daemon=True
        )
        start_time.start()

        return Response(
            {
                "status_code": status.HTTP_200_OK,
                "status": True,
                "message": "Cron job initiated.",
            }
        )
