"""dashboard urls"""
# File details-
#   Author      - Shubham Dhumal
#   Description - This file is declare urlpatterns of dashboard
#   Name        - Dashboard urls
#   Modified by - Vismay Raul

from django.urls import path

# pylint: disable-msg=E0611
from .apis import (
    StationListAutoCompleteAPI,
    SendSessionDataEmail,
    StoreThirdpartyDataCRONJobAPI,
    GetUserSessionsListAPIForApp,
    GetUserSessionsListAPIForPortal,
)

from .api_v2 import (
    GetUserSessionsListAPIForPortalV5,
    GetUserSessionsListAPIForAppV5,
    StationListAutoCompleteAPI_V5,
    UpdateDriivzCRONJobAPI,
    UpdateAdvamCRONJobAPI,
    EmailReceipt,
    RH_Driivz,
    UpdateAmpecoCRONJobAPI,
)


urlpatterns = [
    path("api/get-station-list/", StationListAutoCompleteAPI.as_view()),
    path("api/v2/get-station-list/", StationListAutoCompleteAPI_V5.as_view()),
    path(
        "api/v3/get-user-sessions-receipt-list/",
        GetUserSessionsListAPIForApp.as_view(),
    ),
    path(
        "api/v4/get-user-sessions-receipt-list/",
        GetUserSessionsListAPIForPortal.as_view(),
    ),
    path(
        "api/v5/get-user-sessions-receipt-list/",
        GetUserSessionsListAPIForPortalV5.as_view(),
    ),
    path(
        "api/v5/get-user-sessions-receipt-list/app/",
        GetUserSessionsListAPIForAppV5.as_view(),
    ),
    path("api/v2/email-receipt/", EmailReceipt.as_view()),
    path("api/send-session-data-email/", SendSessionDataEmail.as_view()),
    path(
        "api/store-thirdparty-data-cron-job-trigger-api/",
        StoreThirdpartyDataCRONJobAPI.as_view(),
    ),
    path(
        "api/update-driivz-cache-and-db-cron-job-trigger-api/",
        UpdateDriivzCRONJobAPI.as_view(),
    ),
    path(
        "api/update-advam-cache-and-db-cron-job-trigger-api/",
        UpdateAdvamCRONJobAPI.as_view(),
    ),
    path(
        "api/update-ampeco-cache-and-db-cron-job-trigger-api/",
        UpdateAmpecoCRONJobAPI.as_view(),
    ),
    path(
        "api/rh-driivz/",
        RH_Driivz.as_view(),
    ),
]
