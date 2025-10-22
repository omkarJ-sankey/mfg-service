#  File details-
#   Author      - Shivkumar Kumbhar
#   Description - This file contains functions needed for bulk unsubscribe.
#   Name        - Bulk upload functions
#   Modified by - Shivkumar Kumbhar
#   last modified - 13/03/23

# These are all the imports that we are exporting from
# different module's from project or library.

import threading
from django.utils import timezone
from django.db.models import Q

from sharedServices.common import (
    remove_whitespace,
    upload_progress_database,
    array_to_string_converter,
)

# pylint:disable=import-error
from sharedServices.model_files.bulk_models import (
    BulkUploadErrorMessages,
    BulkUploadProgress,
)
from sharedServices.model_files.audit_models import AuditTrail
from sharedServices.model_files.app_user_models import MFGUserEV, Profile
from sharedServices.common import (
    hasher,
)
from sharedServices.common_audit_trail_functions import add_audit_data
from sharedServices.constants import (
    YES,
    AUDIT_UPDATE_CONSTANT,
)
from adminServices.configurations.app_level_constants import UNSUBSCRIBE_EMAIL


def unsubscribe_email_notifications_bulk_upload(valid_emails_list, user):
    """this function is used to unsubscribe the user from emails"""
    updated_users = ""
    for count, hashed_email in enumerate(valid_emails_list):
        updated_user = Profile.objects.filter(user_id__user_email=hashed_email)
        if updated_user:
            updated_user.update(
                updated_by=user.full_name,
                email_marketing_update_preference_status=False,
                email_news_letter_preference_status=False,
                email_promotion_preference_status=False,
                email_ev_updates_preference_status=False,
            )
            updated_users += (
                f"{updated_user.first().user.id}"
                if len(updated_users) == 0
                else f",{updated_user.first().user.id}"
            )
        BulkUploadProgress.objects.filter(
            ~Q(
                uploading_status="completed",
            ),
            uploaded_for="email_notifications",
        ).update(uploaded_rows_count=f"{count+1}")
    add_audit_data(
        user,
        updated_users,
        "bulk-unsubscribe",
        AUDIT_UPDATE_CONSTANT,
        UNSUBSCRIBE_EMAIL,
        array_to_string_converter(
            [
                {
                    "unsubscribe status": YES,
                    "unsubscribed users": updated_users,
                }
            ]
        ),
        None,
    )


def email_notifications_bulk_upload(emails_to_unsubscribe_sheet, user):
    """this function validated emails and stores error in case any"""
    if "Emails" in emails_to_unsubscribe_sheet:
        unsubscribe_emails_set = list(emails_to_unsubscribe_sheet["Emails"])
        unsubscribe_emails_set = [
            remove_whitespace(str(email)) for email in unsubscribe_emails_set
        ]
    else:
        return {
            "status": False,
            "error": "'Emails' column not present in sheet",
        }

    error_object_list = []
    valid_emails_list = []
    for count, email in enumerate(unsubscribe_emails_set):
        email = email.lower()
        hashed_user_email = hasher(email)
        if email == "nan":
            continue
        elif not MFGUserEV.objects.filter(
            user_email=hashed_user_email
        ).first():
            error_object_list.append(
                {
                    "row number": f"{count+1}",
                    "column name": "Emails",
                    "error message": f"User with emailID '{email}' NOT FOUND",
                }
            )
        else:
            valid_emails_list.append(hashed_user_email)
    if len(valid_emails_list) == 0:
        return {
            "status": False,
            "error": "All the Emails in sheet are invalid or Emails column is blank",
        }

    total_data_count = len(valid_emails_list)
    promotion_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="email_notifications",
    )
    upload_progress_database(
        "email_notifications", promotion_bulk_upload_progress, total_data_count
    )
    error_object_list_with_tab_name = [
        {
            "tab": "Unsubscribe emails Tab",
            "errors": error_object_list,
        }
    ]
    unsubscribe_emails_error_records = BulkUploadErrorMessages.objects.filter(
        uploaded_for="email_notifications"
    )

    if unsubscribe_emails_error_records.first():
        unsubscribe_emails_error_records.update(
            errors=array_to_string_converter(error_object_list_with_tab_name),
            ready_to_export=YES,
        )
    else:
        BulkUploadErrorMessages.objects.create(
            uploaded_for="email_notifications",
            errors=array_to_string_converter(error_object_list_with_tab_name),
            ready_to_export=YES,
            created_date=timezone.localtime(timezone.now()),
        )

    start_time = threading.Thread(
        target=unsubscribe_email_notifications_bulk_upload,
        args=[valid_emails_list, user],
        daemon=True
    )
    start_time.start()
    if len(error_object_list):
        return {
            "status": True,
            "error": "Some error found in email column, Please click on Export errors to review the errors",
        }
    else:
        return {"status": True, "error": ""}
