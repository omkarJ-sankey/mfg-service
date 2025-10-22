"""charging sessions """
# Date - 21/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on defining
#                        url path to access particular view or API.
#   Name            - Charging session Urls
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 16/07/2025


# Imports required to make urls are below
from django.urls import path


# Views and APIs used for particular action and operation
from .apis import (
    AzureFunctionCRONJobAPI,
    CheckUserRunningSessions,
    SessionInfoAndFeedback,
    StartSession,
    StartSessionOCPI,
    StopSession,
    StopSessionOCPI,
    ForcedStopSessionsAPI,
    SubmitIntermediateSubmitData,
    UserAutomaticallyStoppedSessions,
    AzureFunctionCRONJobAPIOCPI
)
from .session_due_payments_apis import (
    MakeDueSessionPayment,
    SendDuePaymentMails,
)
from .v4_apis import (
    CloseFailedPreAuth,
    CloseInvalidCdrSessions
)
# Assigning Views and APIs to particular url to access there functionality

v3_urlpatterns = [
    path("api/start-session/", StartSession.as_view()),
    path(
        "api/submit-itermediate-session-data/",
        SubmitIntermediateSubmitData.as_view(),
    ),
    path("api/stop-session/", StopSession.as_view()),
    path("api/submit-session-info/", SessionInfoAndFeedback.as_view()),
    path("api/close-session/", ForcedStopSessionsAPI.as_view()),
    path(
        "api/check-user-running-sessions/", CheckUserRunningSessions.as_view()
    ),
    path(
        "api/check-force-stopped-session/",
        UserAutomaticallyStoppedSessions.as_view(),
    ),
    path(
        "api/azure-function-cron-job-trigger-api/",
        AzureFunctionCRONJobAPIOCPI.as_view(),
    ),
    path(
        "api/azure-function-cron-job-trigger-api-ocpi/",
        AzureFunctionCRONJobAPIOCPI.as_view(),
    ),
    path("api/make-due-session-payment/", MakeDueSessionPayment.as_view()),
    path(
        "api/send-due-payment-emails/",
        SendDuePaymentMails.as_view(),
    ),
]

v4_urlpatterns = [
    path("api/v4/start-session/", StartSession.as_view()),
    path("api/v4/start-ocpi-session/", StartSessionOCPI.as_view()),
    path("api/v4/stop-session/", StopSession.as_view()),

    path("api/v4/stop-ocpi-session/", StopSessionOCPI.as_view()),
    path(
        "api/v4/check-user-running-sessions/", CheckUserRunningSessions.as_view()
    ),
    path("api/v4/make-due-session-payment/", MakeDueSessionPayment.as_view()),
    path("api/v4/close-failed-pre-auth/", CloseFailedPreAuth.as_view()),
    path(
        "api/v4/complete-invalid-cdr-payments/",
        CloseInvalidCdrSessions.as_view(),
    ),
]

urlpatterns = v3_urlpatterns + v4_urlpatterns
