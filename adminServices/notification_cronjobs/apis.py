"""contact less module APIs"""

#  File details-
#   Author      - Shivkumar Kumbhar
#   Description - This file contains APIs for Notifications cronjob module.
#   Name        - Notifications cronjob
#   Modified by - Shivkumar Kumbhar

# These are all the imports that we are exporting from
# different module's from project or library.

import threading
from passlib.hash import django_pbkdf2_sha256 as handler
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
#pylint:disable=import-error
from sharedServices.constants import (
    DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
)
from adminServices.notifications.notifications_view import (
    filter_push_notifications_cron_job_function,
)
from adminServices.notifications.email_notifications_views import (
    filter_email_notifications_cron_job_function,
)


class PushNotificationSchedulingCRONJobAPI(APIView):
    """to trigger the scheduled Push and InApp Notification"""

    @classmethod
    def post(cls, cron_job_request):
        try:
            secret_key_azure = cron_job_request.data.get("secret_key", None)
            if secret_key_azure is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Secret key not provided.",
                    }
                )
            if not handler.verify(
                secret_key_azure, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
            ):
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Secret key is not valid.",
                    }
                )

            start_time = threading.Thread(
                target=filter_push_notifications_cron_job_function,
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
        except COMMON_ERRORS:
            return API_ERROR_OBJECT


class EmailSchedulingCRONJobAPI(APIView):
    """to trigger the scheduled emails"""

    @classmethod
    def post(cls, cron_job_request):
        try:
            secret_key_azure = cron_job_request.data.get("secret_key", None)
            if secret_key_azure is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Secret key not provided.",
                    }
                )
            if not handler.verify(
                secret_key_azure, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
            ):
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Secret key is not valid.",
                    }
                )

            start_time = threading.Thread(
                target=filter_email_notifications_cron_job_function,
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
        except COMMON_ERRORS:
            return API_ERROR_OBJECT
