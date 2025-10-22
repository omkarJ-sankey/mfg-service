# Date - 20/11/2022
# File details-
#   Author          - Shivkumar kumbhar
#   Description     - This file is mainly focused on
#                      creating form for custom email body
#   Name            - notifications module related models
#   Modified by     - Shivkumar kumbhar
#   Modified date   - 26/12/2022

from django.urls import path
from .notifications_view import (
    notifications_list_func,
    add_new_push_notification,
    view_push_notification,
    delete_push_notification,
    send_push_notification_now,
    update_push_notification,
    draft_push_notification,
    schedule_push_notification,
)
from .email_notifications_views import (
    email_list_func,
    add_new_email_notification,
    delete_email_notification,
    update_email_notification,
    view_email_notification,
    schedule_email_notification,
    send_email_notification_now,
    draft_email_notification,
    unsubscribe_to_email_notification,
    validate_user_email,
)

from .bulk_upload_views import (
    bulk_unsubscribe_to_email_notifications,
    get_unsubscribe_progress_bar_details,
)

urlpatterns = [
    path("", notifications_list_func, name="notifications_list"),
    path(
        "add_new_push_notification/",
        add_new_push_notification,
        name="add_new_push_notification",
    ),
    path(
        "send_push_notification_now/<int:id>",
        send_push_notification_now,
        name="send_push_notification_now",
    ),
    path("email-list/", email_list_func, name="email_list"),
    path(
        "add-new-email-notification/",
        add_new_email_notification,
        name="add_new_email_notification",
    ),
    path(
        "delete-email-notification/<int:id>",
        delete_email_notification,
        name="delete_email_notification",
    ),
    path(
        "delete_push_notification/<int:id>",
        delete_push_notification,
        name="delete_push_notification",
    ),
    path(
        "update-email-notification/<int:id>",
        update_email_notification,
        name="update_email_notification",
    ),
    path(
        "view-email-notification/<int:id>",
        view_email_notification,
        name="view_email_notification",
    ),
    path(
        "send-email-notification-now/<int:id>",
        send_email_notification_now,
        name="send_email_notification_now",
    ),
    path(
        "schedule-email-notification/<int:id>",
        schedule_email_notification,
        name="schedule_email_notification",
    ),
    path(
        "schedule-push-notification/<int:id>",
        schedule_push_notification,
        name="schedule_push_notification",
    ),
    path(
        "draft-email-notification/<int:id>",
        draft_email_notification,
        name="draft_email_notification",
    ),
    path(
        "draft_push_notification/<int:id>",
        draft_push_notification,
        name="draft_push_notification",
    ),
    path(
        "view-push-notification/<int:id>",
        view_push_notification,
        name="view_push_notification",
    ),
    path(
        "update_push_notification/<int:id>",
        update_push_notification,
        name="update_push_notification",
    ),
    path(
        "bulk_unsubscribe-to-email-notifications/",
        bulk_unsubscribe_to_email_notifications,
        name="bulk_unsubscribe_to_email_notifications",
    ),
    path(
        "unsubscribe-to-email-notifications/",
        unsubscribe_to_email_notification,
        name="unsubscribe_to_email_notifications",
    ),
    path(
        "get-unsubscribe-progress-bar-details/",
        get_unsubscribe_progress_bar_details,
        name="get_unsubscribe_progress_bar_details",
    ),
    path(
        "validate-user-email/",
        validate_user_email,
        name="validate-user-email",
    ),
]
