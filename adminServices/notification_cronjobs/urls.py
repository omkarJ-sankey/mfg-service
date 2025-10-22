# Date - 20/11/2022
# File details-
#   Author          - Shivkumar kumbhar
#   Description     - This file is mainly focused on
#                      creating form for custom email body
#   Name            - notifications module related models
#   Modified by     - Shivkumar kumbhar
#   Modified date   - 26/12/2022

from django.urls import path
from .apis import (
    PushNotificationSchedulingCRONJobAPI,
    EmailSchedulingCRONJobAPI,
)

urlpatterns = [
    path(
        "api/email-scheduling-cron-job-api",
        EmailSchedulingCRONJobAPI.as_view(),
        name="email_scheduling_cron_job_api",
    ),
    path(
        "api/push-notification-scheduling-cron-job-api",
        PushNotificationSchedulingCRONJobAPI.as_view(),
        name="push_notification_scheduling_cronjob_api",
    ),
]
