"""push notifications api urls"""
from django.urls import path

# Views and APIs used for particular action and operation
from .apis import (
    UpdateUserRegionAndDeviceToken,
    GetUserInAppNotificationsList,
    UpdateNotificationReadStatus,
    DeleteInAppNotificationsCRONJobAPI,
    UpdateUserNotificationPreferences,
    GetUserNotificationPreference,
    UpdateUserEmailPreferences,
    GetUserEmailPreference,
)


# Assigning Views and APIs to particular url to access there functionality
urlpatterns = [
    path(
        "api/update-user-region-and-device-token/",
        UpdateUserRegionAndDeviceToken.as_view(),
    ),
    path(
        "api/get-user-in-app-notifications-list/",
        GetUserInAppNotificationsList.as_view(),
    ),
    path(
        "api/update-notification-read-status/",
        UpdateNotificationReadStatus.as_view(),
    ),
    path(
        "api/delete-in-app-notifications-cron-job/",
        DeleteInAppNotificationsCRONJobAPI.as_view(),
    ),
    path(
        "api/update-user-preferences/",
        UpdateUserNotificationPreferences.as_view(),
    ),
    path(
        "api/get-user-preferences/",
        GetUserNotificationPreference.as_view(),
    ),
    path(
        "api/update-user-email-preferences/",
        UpdateUserEmailPreferences.as_view(),
    ),
    path(
        "api/get-user-email-preferences/",
        GetUserEmailPreference.as_view(),
    ),
]
