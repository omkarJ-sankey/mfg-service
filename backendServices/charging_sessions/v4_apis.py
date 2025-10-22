"""charging sessions V.4.0.0 apis"""

# Date - 22/11/2024

# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on APIs
#                       related to charging sessions.
#   Name            - charging session v4.0.0 APIs
#   Modified by     - Manish Pawar
#   Modified date   - 22/11/2024


# These are all the imports that we are exporting from different
# module's from project or library.
import json
import concurrent.futures
import threading
from datetime import timedelta

from django.utils import timezone

# from square.client import Client
from passlib.hash import django_pbkdf2_sha256 as handler
from django.db.models import Q

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

# pylint:disable=import-error
from sharedServices.common import (
    filter_function_for_base_configuration
)
from sharedServices.constants import (
    YES,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    SECRET_KEY_NOT_PROVIDED,
    SECRET_KEY_IN_VALID,
    DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET,
    POST_REQUEST,
)
from sharedServices.model_files.charging_session_models import ChargingSession
from sharedServices.model_files.ocpi_sessions_models import OCPISessions

from sharedServices.payments_helper_function import make_request

from sharedServices.common_session_payment_functions import handle_session_invalid_cdr_payment


def close_failed_preauths():
    """this function initiates cron job to close failed preauths"""
    sessions = list(
        OCPISessions.objects.filter(
            # ~Q(charging_authorization_status="ACCEPTED"),
            is_refund_initiated=YES,
            session_status="start",
            paid_status="unpaid",
            # status = "AWAITING",
            payment_id__isnull=False,
            chargepoint_id__manufacturer__in=json.loads(
                filter_function_for_base_configuration(
                    "excluded_manufactures_for_pre_auth_refund", '["Alpitronic", "SWARCO"]'
                )
            ),
        ).only("id", "payment_id")
        | OCPISessions.objects.filter(
            # ~Q(charging_authorization_status="ACCEPTED"),
            session_status="start",
            paid_status="unpaid",
            # status = "AWAITING",
            payment_id__isnull=False,
            start_datetime__lte=timezone.localtime(timezone.now())
            - timedelta(
                minutes=int(
                    filter_function_for_base_configuration(
                        "pre_auth_refund_trigger_time", "10"
                    )
                )
            ),
            start_datetime__gte=timezone.localtime(timezone.now()) - timedelta(hours=24)
        ).only("id", "payment_id")
        | OCPISessions.objects.filter(
            paid_status="unpaid",
            status = "INVALID",
            payment_id__isnull=False,
            start_datetime__lte=timezone.localtime(timezone.now())
            - timedelta(
                minutes=int(
                    filter_function_for_base_configuration(
                        "pre_auth_refund_trigger_time", "10"
                    )
                )
            ),
            start_datetime__gte=timezone.localtime(timezone.now()) - timedelta(hours=24)
        ).only("id", "payment_id")
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(
            refund_session_payment,
            list(sessions),
        )

def refund_session_payment(session):
    refund_response = make_request(
        POST_REQUEST,
        f"/payments/{session.payment_id}/cancel",
        session.user_id.id,
        module="Cancel user payment",
    )
    if (
        refund_response.status_code == 200 and
        "payment" in json.loads(refund_response.content)
    ):
        OCPISessions.objects.filter(
            id=session.id
        ).update(
            paid_status="refunded",
            session_status="completed",
            status = "INVALID"
        )

# def process_invalid_cdr_payment(session):
#     print("session is : ", session.id)
#     return None
    # refund_response = make_request(
    #     POST_REQUEST,
    #     f"/payments/{session.payment_id}/cancel",
    #     session.user_id.id,
    #     module="Cancel user payment",
    # )
    # if (
    #     refund_response.status_code == 200 and
    #     "payment" in json.loads(refund_response.content)
    # ):
    #     OCPISessions.objects.filter(
    #         id=session.id
    #     ).update(
    #         paid_status="refunded",
    #         session_status="completed",
    #         status = "INVALID"
    #     )

def close_invalid_cdr_sessions():
    """this function initiates cron job to close failed preauths"""
    now = timezone.now()

    handle_cdrs_from = now - timedelta(hours=48)
    sessions = OCPISessions.objects.filter(
        status = "COMPLETED",
        session_status = "closed",
        start_datetime__gte = handle_cdrs_from,
        is_cdr_valid=False
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(
            handle_session_invalid_cdr_payment,
            list(sessions),
        )


class CloseFailedPreAuth(APIView):
    """close preauth cronjonb API"""

    @classmethod
    def post(cls, cron_job_request):
        """post method to initialize cron job api"""
        try:
            secret_key_azure = cron_job_request.data.get("secret_key", None)
            if secret_key_azure is None:
                return SECRET_KEY_NOT_PROVIDED
            if not handler.verify(
                secret_key_azure, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
            ):
                return SECRET_KEY_IN_VALID

            start_time = threading.Thread(
                target=close_failed_preauths,
                daemon=True
            )
            start_time.start()

            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Close failed preauth cron job initiated.",
                }
            )

        except COMMON_ERRORS:
            return API_ERROR_OBJECT


class CloseInvalidCdrSessions(APIView):
    """API to close sessions with invalid cdrs"""

    @classmethod
    def post(cls, cron_job_request):
        """post method to initialize cron job api"""
        try:
            secret_key_azure = cron_job_request.data.get("secret_key", None)
            if secret_key_azure is None:
                return SECRET_KEY_NOT_PROVIDED
            if not handler.verify(
                secret_key_azure, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
            ):
                return SECRET_KEY_IN_VALID

            start_time = threading.Thread(
                target=close_invalid_cdr_sessions,
                daemon=True
            )
            start_time.start()

            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Close session with invalid cdrs cron job initiated.",
                }
            )

        except COMMON_ERRORS:
            return API_ERROR_OBJECT
