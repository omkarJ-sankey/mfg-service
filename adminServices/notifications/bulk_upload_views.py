#  File details-
#   Author      - Shivkumar Kumbhar
#   Description - This file is mainly focused Bulk Unsubscribe users from email notifications
#   Name        - Bulk upload view
#   Modified by - Shivkumar Kumbhar
#   last modified - 13/03/23

# These are all the imports that we are exporting from
# different module's from project or library.

import sys
import zipfile
import pandas as pd
from django.db.models import Q
from decimal import Decimal
from .bulk_upload_functions import email_notifications_bulk_upload

from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from sharedServices.model_files.bulk_models import (
    BulkUploadErrorMessages,
    BulkUploadProgress,
)
from sharedServices.common import (
    filter_url,
    export_data_function,
    string_to_array_converter,
    custom_round_function,
)
from sharedServices.decorators import allowed_users, authenticated_user
from sharedServices.constants import (
    NOTIFICATION_CONST,
    GET_METHOD_ALLOWED,
    POST_METHOD_ALLOWED,
    COMMON_ERRORS,
    ERROR_TEMPLATE_URL,
)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=NOTIFICATION_CONST)
def bulk_unsubscribe_to_email_notifications(request):
    "this function validates the sheet and starts bulk uplad process"
    try:
        export_errors = request.GET.get("export_errors", None)
        if export_errors == "Yes":
            errors = string_to_array_converter(
                BulkUploadErrorMessages.objects.filter(
                    uploaded_for="email_notifications", ready_to_export="Yes"
                )
                .first()
                .errors
            )[0]["errors"]
            if errors:
                response = export_data_function(
                    errors,
                    ["Row number", "Column name", "Error message"],
                    ["row number", "column name", "error message"],
                    "Unsubscribe Error Sheet",
                )
                if response:
                    return response
        if request.method == "POST":
            unsubscribe_email_sheet = request.body
            data = []
            tab_errors = []
            try:
                xls = pd.ExcelFile(unsubscribe_email_sheet, engine="openpyxl")
                try:
                    emails_to_unsubscribe = pd.read_excel(
                        xls, "Unsubscribe emails"
                    )
                except ValueError:
                    tab_errors.append('"Unsubscribe emails" tab')

                if len(tab_errors) > 0:
                    error_tab = ""
                    for count, tab_error_s in enumerate(tab_errors):
                        if count == (len(tab_errors) - 1):
                            error_tab += tab_error_s
                        else:
                            error_tab += f"{tab_error_s} &"
                    error_tab = f"Sheet must include {error_tab}"
                    return JsonResponse(
                        {"response": {"status": False, "error": error_tab}}
                    )
                try:
                    data = email_notifications_bulk_upload(
                        emails_to_unsubscribe, request.user
                    )
                except (
                    KeyError,
                    AttributeError,
                    TimeoutError,
                ) as station_error:
                    (
                        exception_type_unsubscribe_email,
                        exception_objet_unsubscribe_email,
                        exception_traceback_unsubscribe_email,
                    ) = sys.exc_info()
                    filename = (
                        exception_traceback_unsubscribe_email.tb_frame.f_code.co_filename
                    )
                    line_number = (
                        exception_traceback_unsubscribe_email.tb_lineno
                    )
                    print(
                        exception_objet_unsubscribe_email, "**execption_object"
                    )
                    print("Exception type: ", exception_type_unsubscribe_email)
                    print("File name: ", filename)
                    print("Line number: ", line_number)
                    print("Error", str(station_error))
                    return JsonResponse(
                        {
                            "response": {
                                "status": False,
                                "error": "Something went wrong.",
                            }
                        }
                    )
            except (zipfile.BadZipFile, IOError) as _:
                return JsonResponse(
                    {
                        "response": {
                            "status": False,
                            "error": "File not recognized as excel file.",
                        }
                    }
                )
            return JsonResponse({"response": data})

        url_data = filter_url(
            request.user.role_id.access_content.all(), NOTIFICATION_CONST
        )
        return render(
            request,
            "notifications/unsubscribe_to_email_notifications.html",
            {"data": url_data, "active_tab": "Unsubscribe"},
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


def get_unsubscribe_progress_bar_details(request):
    "this function is used to get the progress of file uplaod"
    try:
        bulk_progess_queryset = BulkUploadProgress.objects.filter(
            ~Q(
                uploading_status="completed",
            ),
            uploaded_for="email_notifications",
        )
        if bulk_progess_queryset.first():
            total_rows_count = bulk_progess_queryset.first().total_rows_count
            uploaded_rows_count = (
                bulk_progess_queryset.first().uploaded_rows_count
            )
            progess_value = custom_round_function(
                Decimal(str(uploaded_rows_count))
                * 100
                / Decimal(str(total_rows_count))
            )
            if progess_value == 100:
                bulk_progess_queryset.update(uploading_status="completed")
            return JsonResponse(
                {"response": {"progress_value": f"{progess_value}"}}
            )
        else:
            return JsonResponse({"response": {"progress_value": "0"}})
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)
