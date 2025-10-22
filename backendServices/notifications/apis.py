"""Push notifications apis"""
# File details-
#   Author          - Shivkumar Kumbhar
#   Description     - This file is mainly focused on APIs related to push notifications.
#   Name            - Push notifications APIs
#   Modified by     - Shivkumar kumbhar
#   Modified date   - 29/03/2023


# These are all the imports that we are exporting from
# different module's from project or library.

import pytz
import base64
import threading
import concurrent.futures
from django.utils import timezone
from datetime import datetime
from passlib.hash import django_pbkdf2_sha256 as handler
from django.db import DatabaseError
from django.db.models import Q, F, Case, When, Value 
from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.response import Response
from backendServices.backend_app_constants import (
    MULTIPLE_LOGIN,
    UNAUTHORIZED,
)
from sharedServices.constants import (
    API_ERROR_OBJECT,
    COMMON_ERRORS,
    NOTIFICATIONS_EXPIRY_TIME_IN_HOURS,
    SECRET_KEY_IN_VALID,
    SECRET_KEY_NOT_PROVIDED,
    DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET,
)
from sharedServices.model_files.app_user_models import Profile
from sharedServices.model_files.config_models import BaseConfigurations
from sharedServices.common import (
    string_to_array_converter,
    array_to_string_converter,
    handle_concurrent_user_login,
    is_base64
)


class UpdateUserRegionAndDeviceToken(APIView):
    """This API will update user region and  device token"""

    permission_classes = [permissions.IsAuthenticated]

    @classmethod
    def post(cls, request):
        """post request to update user region and device token"""
        if not request.auth or not request.user:
            return UNAUTHORIZED

        if not handle_concurrent_user_login(request.user.id, request.auth):
            return MULTIPLE_LOGIN
        region = request.data.get("region", None)
        fcm_device_token = request.data.get("fcm_device_token", None)

        try:
            update_user_profile=None
            if fcm_device_token:
                if not is_base64(fcm_device_token):
                    fcm_device_token = base64.b64encode(
                        fcm_device_token.encode("utf-8")
                    ).decode("utf-8")
                update_user_profile = Profile.objects.filter(
                    Q(fcm_device_token=fcm_device_token) | Q(user=request.user)
                ).update(
                    fcm_device_token=Case(
                        When(user=request.user, then=Value(fcm_device_token)),
                        default=None
                    ),
                    region=Case(
                        When(user=request.user, then=Value(region)),
                        default=F('region')
                    )
                )
            else:
                update_user_profile = Profile.objects.filter(user=request.user).update(region=region)
            if update_user_profile:
                return Response(
                    {
                        "status_code": status.HTTP_201_CREATED,
                        "status": True,
                        "message": "User details updated successfully",
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                    "status": False,
                    "message": "Failed to update user details!",
                }
            )

        except COMMON_ERRORS as exception:
            print(
                f"Update User Region And Device Token API failed for user -> \
                    {request.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT

class GetUserInAppNotificationsList(APIView):
    """This API is used to get the list of in app notifications for a user"""

    permission_classes = [permissions.IsAuthenticated]

    @classmethod
    def get(cls, request):
        """get request to fetch list of in app notifications for a user"""

        if not request.auth or not request.user:
            return UNAUTHORIZED
        if not handle_concurrent_user_login(request.user.id, request.auth):
            return MULTIPLE_LOGIN
        try:
            inapp_notifications_list = (
                Profile.objects.filter(user=request.user)
                .first()
                .inapp_notification_object
            )
            if inapp_notifications_list:
                notifications_object_list = string_to_array_converter(
                    inapp_notifications_list
                )
                unseen_notification_list = [
                    notification_object
                    for notification_object in notifications_object_list
                    if not notification_object["read_status"]
                ]
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "successfully fetched in app notifications",
                        "data": {
                            "inapp_notifications_list": notifications_object_list,
                            "unseen_notification_count": len(
                                unseen_notification_list
                            ),
                        },
                    }
                )
            if not inapp_notifications_list:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "No notifications found",
                        "data": {
                            "inapp_notifications_list": [],
                            "unseen_notification_count": 0,
                        },
                    }
                )

            return Response(
                {
                    "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                    "status": False,
                    "message": "Failed to fetch in app notifications",
                }
            )

        except COMMON_ERRORS as exception:
            print(
                f"Get User In App Notifications List API failed for user -> \
                    {request.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


class UpdateNotificationReadStatus(APIView):
    """This API is used to update the status of notification(read/unread)"""

    permission_classes = [permissions.IsAuthenticated]

    @classmethod
    def post(cls, request):
        """post request to update the status of notification(read/unread)"""
        if not request.auth or not request.user:
            return UNAUTHORIZED

        if not handle_concurrent_user_login(request.user.id, request.auth):
            return MULTIPLE_LOGIN
        try:
            status_updated = False
            notification_id = request.data.get("notification_id", None)
            if not notification_id or not type(notification_id) == int:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Notification id not provided or its not a number",
                    }
                )
            notifications_object_list = (
                Profile.objects.filter(user=request.user)
                .first()
                .inapp_notification_object
            )
            if notifications_object_list:
                notifications_object_list = string_to_array_converter(
                    notifications_object_list
                )
                for notification in notifications_object_list:
                    if notification["id"] == notification_id:
                        notification["read_status"] = True
                        status_updated = (
                            True
                            if Profile.objects.filter(
                                user=request.user
                            ).update(
                                inapp_notification_object=array_to_string_converter(
                                    notifications_object_list
                                )
                            )
                            else False
                        )

            if status_updated:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "Successfully updated notification status",
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                    "status": False,
                    "message": "Failed to update notification status",
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Update Notification Read Status API failed for user -> \
                    {request.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


def delete_in_app_notifications_for_user(user):
    """delete expired 'in app notifications' for a user"""

    array_of_notifications = string_to_array_converter(
        user.inapp_notification_object
    )
    notifications_expiry_time_in_hours = BaseConfigurations.objects.filter(
        base_configuration_key=NOTIFICATIONS_EXPIRY_TIME_IN_HOURS
    ).first()
    notifications_expiry_time_in_hours = (
        int(notifications_expiry_time_in_hours.base_configuration_value)
        if notifications_expiry_time_in_hours
        and notifications_expiry_time_in_hours.base_configuration_value.isnumeric()
        else 24
    )
    array_of_unexpired_notifications = [
        notification
        for notification in array_of_notifications
        if int(
            (
                timezone.localtime(timezone.now())
                - datetime.strptime(
                    notification["delivered_time"], "%Y-%m-%dT%H:%M:%S"
                ).replace(tzinfo=pytz.UTC)
            ).total_seconds()
            // 3600
        )
        < (
            notification["expiry_in_hours"]
            if (
                "expiry_in_hours" in notification
                and notification["expiry_in_hours"]
            )
            else notifications_expiry_time_in_hours
        )
    ]
    (
        Profile.objects.filter(user_id=user.user_id).update(
            inapp_notification_object=array_to_string_converter(
                array_of_unexpired_notifications
            )
        )
        if len(array_of_unexpired_notifications)
        else Profile.objects.filter(user_id=user.user_id).update(
            inapp_notification_object=None
        )
    )


def delete_in_app_notifications_function():
    """this function collect all user and call
    delete_in_app_notifications_for_user function to
    delete expired in app notifications"""
    Users = Profile.objects.filter(~Q(inapp_notification_object=None))
    if len(Users):
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            executor.map(
                delete_in_app_notifications_for_user,
                list(Users),
            )
    print("**************** cron job completed ******************")


class DeleteInAppNotificationsCRONJobAPI(APIView):
    """This cron job will be triggered"""

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
                target=delete_in_app_notifications_function,
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
        except COMMON_ERRORS as exception:
            print(
                f"Delete In App Notifications CRON Job API failed \
                    due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


class UpdateUserNotificationPreferences(APIView):
    """This API will update user Preference"""

    permission_classes = [permissions.IsAuthenticated]

    @classmethod
    def post(cls, request):
        """post request to update user region and device token"""
        if not request.auth or not request.user:
            return UNAUTHORIZED

        if not handle_concurrent_user_login(request.user.id, request.auth):
            return MULTIPLE_LOGIN

        notification = request.data

        promotions = notification[0]["title"]
        promotions_status = notification[0]["status"]
        loyalty = notification[1]["title"]
        loyalty_status = notification[1]["status"]

        if not promotions:
            return Response(
                {
                    "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                    "status": False,
                    "message": "promotions not provided",
                }
            )
        if not loyalty:
            return Response(
                {
                    "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                    "status": False,
                    "message": "loyalty not provided",
                }
            )
        try:
            update_user_profile = Profile.objects.filter(
                user=request.user
            ).update(
                promotion_preference_status=promotions_status,
                loyalty_preference_status=loyalty_status,
            )

            if update_user_profile:
                return Response(
                    {
                        "status_code": status.HTTP_201_CREATED,
                        "status": True,
                        "message": "User details updated successfully",
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                    "status": False,
                    "message": "Failed to update user details!",
                }
            )

        except (IndexError, KeyError, DatabaseError):
            return API_ERROR_OBJECT


class GetUserNotificationPreference(APIView):
    """This API is used to get preference for a user"""

    permission_classes = [permissions.IsAuthenticated]

    @classmethod
    def get(cls, request):
        """get request to fetch preference for a user"""

        if not request.auth or not request.user:
            return UNAUTHORIZED
        if not handle_concurrent_user_login(request.user.id, request.auth):
            return MULTIPLE_LOGIN
        try:
            loyalty_preference_status = (
                Profile.objects.filter(user=request.user)
                .first()
                .loyalty_preference_status
            )

            promotion_preference_status = (
                Profile.objects.filter(user=request.user)
                .first()
                .promotion_preference_status
            )

            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "successfully fetched in app notifications",
                    "data": {
                        "notification": [
                            {
                                "status": promotion_preference_status,
                                "title": "Promotion",
                            },
                            {
                                "status": loyalty_preference_status,
                                "title": "Loyalty",
                            },
                        ],
                    },
                }
            )

        except (IndexError, KeyError, DatabaseError):
            return API_ERROR_OBJECT


class UpdateUserEmailPreferences(APIView):
    """This API will update user Email Preference"""

    permission_classes = [permissions.IsAuthenticated]

    @classmethod
    def post(cls, request):
        """post request to update user region and device token"""
        if not request.auth or not request.user:
            return UNAUTHORIZED

        if not handle_concurrent_user_login(request.user.id, request.auth):
            return MULTIPLE_LOGIN

        email = request.data

        news_letter = email[0]["title"]
        news_letter_status = email[0]["status"]
        marketing_updates = email[1]["title"]
        marketing_updates_status = email[1]["status"]
        promotions = email[2]["title"]
        promotions_status = email[2]["status"]
        ev_updates = email[3]["title"]
        ev_updates_status = email[3]["status"]
        if not news_letter:
            return Response(
                {
                    "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                    "status": False,
                    "message": "news_letter not provided",
                }
            )
        if not marketing_updates:
            return Response(
                {
                    "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                    "status": False,
                    "message": "marketing_updates not provided",
                }
            )
        if not promotions:
            return Response(
                {
                    "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                    "status": False,
                    "message": "promotions not provided",
                }
            )
        if not ev_updates:
            return Response(
                {
                    "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                    "status": False,
                    "message": "ev_updates not provided",
                }
            )
        try:
            update_user_profile = Profile.objects.filter(
                user=request.user
            ).update(
                email_news_letter_preference_status=news_letter_status,
                email_promotion_preference_status=promotions_status,
                email_marketing_update_preference_status=marketing_updates_status,
                email_ev_updates_preference_status=ev_updates_status,
            )

            if update_user_profile:
                return Response(
                    {
                        "status_code": status.HTTP_201_CREATED,
                        "status": True,
                        "message": "User details updated successfully",
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                    "status": False,
                    "message": "Failed to update user details!",
                }
            )

        except (IndexError, KeyError, DatabaseError):
            return API_ERROR_OBJECT


class GetUserEmailPreference(APIView):
    """This API is used to get user Email preference"""

    permission_classes = [permissions.IsAuthenticated]

    @classmethod
    def get(cls, request):
        """get request to fetch user Email preference"""

        if not request.auth or not request.user:
            return UNAUTHORIZED
        if not handle_concurrent_user_login(request.user.id, request.auth):
            return MULTIPLE_LOGIN
        try:
            email_news_letter_preference_status = (
                Profile.objects.filter(user=request.user)
                .first()
                .email_news_letter_preference_status
            )

            email_marketing_update_preference_status = (
                Profile.objects.filter(user=request.user)
                .first()
                .email_marketing_update_preference_status
            )

            email_promotion_preference_status = (
                Profile.objects.filter(user=request.user)
                .first()
                .email_promotion_preference_status
            )
            email_ev_updates_preference_status = (
                Profile.objects.filter(user=request.user)
                .first()
                .email_ev_updates_preference_status
            )

            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "successfully fetched in app notifications",
                    "data": {
                        "email": [
                            {
                                "status": email_news_letter_preference_status,
                                "title": "News Letter",
                            },
                            {
                                "status": email_marketing_update_preference_status,
                                "title": "Marketing Updates",
                            },
                            {
                                "status": email_promotion_preference_status,
                                "title": "Promotions",
                            },
                            {
                                "status": email_ev_updates_preference_status,
                                "title": "EV Updates",
                            },
                        ],
                    },
                }
            )

        except (IndexError, KeyError, DatabaseError):
            return API_ERROR_OBJECT
