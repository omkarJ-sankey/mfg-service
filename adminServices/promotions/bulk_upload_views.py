"""bulk upload views"""
# Date - 23/11/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on bulk upload of promotions.
#   Name            - Promotions Bulk upload views
#   Modified by     - Manish Pawar
#   Modified date   - 23/11/2021

# imports required to create views

import sys
import zipfile
import pandas as pd

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

# pylint:disable=import-error
from sharedServices.model_files.bulk_models import (
    BulkUploadErrorMessages,
    BulkUploadProgress,
)
from sharedServices.decorators import authenticated_user
from sharedServices.common import (
    string_to_array_converter,
)
from sharedServices.constants import (
    YES,
    GET_METHOD_ALLOWED,
    POST_METHOD_ALLOWED
)

from .bulk_upload_functions import promotions_bulk_upload_function


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def progress_bar_info(_):
    """progress checker function"""
    errors_export_ready_promotions = False
    promotions_error_records = BulkUploadErrorMessages.objects.filter(
        uploaded_for="promotions",
        ready_to_export=YES,
    )
    if promotions_error_records.first():
        errors = string_to_array_converter(
            promotions_error_records.first().errors
        )
        if len(errors[0]["errors"]) > 0 or len(errors[1]["errors"]) > 0:
            errors_export_ready_promotions = True
    promotion_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="promotions",
        uploading_status="uploading",
    )
    if promotion_bulk_upload_progress.first():
        percentage_promotion = (
            int(promotion_bulk_upload_progress.first().total_rows_count)
            * int(promotion_bulk_upload_progress.first().uploaded_rows_count)
            / 100
        )
        if percentage_promotion > 100:
            percentage_promotion = 85
        return JsonResponse(
            {
                "status": True,
                "percentage": percentage_promotion,
                "errors_export_ready": errors_export_ready_promotions,
            }
        )
    return JsonResponse(
        {
            "status": False,
            "percentage": 0,
            "errors_export_ready": errors_export_ready_promotions,
        }
    )


# Bulk upload under development
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def upload_sheet_promotions(request):
    """bulk upload promotions view"""
    excel_file = request.body
    data = []
    tab_errors = []

    try:
        xls = pd.ExcelFile(excel_file, engine="openpyxl")
        try:
            promotions = pd.read_excel(xls, "Promotions")
        except ValueError:
            tab_errors.append('"Promotions" tab')
        try:
            promotion_assign = pd.read_excel(xls, "Promotion assign")
        except ValueError:
            tab_errors.append('"Promotion assign" tab')
        if len(tab_errors) > 0:
            error = ""
            for count, tab_error in enumerate(tab_errors):
                if count == (len(tab_errors) - 1):
                    error += tab_error
                else:
                    error += f"{tab_error} &"
            error = f"Sheet must include {error}"
            return JsonResponse(
                {"response": {"status": False, "error": error}}
            )
        try:
            data = promotions_bulk_upload_function(
                promotions, request.user, promotion_assign
            )
        except (KeyError, AttributeError, TimeoutError) as promotion_error:
            (
                exception_type_promotions,
                exception_object_promotions,
                exception_traceback_promotions,
            ) = sys.exc_info()
            filename_promotions = (
                exception_traceback_promotions.tb_frame.f_code.co_filename
            )
            line_number_promotions = exception_traceback_promotions.tb_lineno
            print(exception_object_promotions, "ignore")
            print("Exception type: ", exception_type_promotions)
            print("File name: ", filename_promotions)
            print("Line number: ", line_number_promotions)
            print("Error", str(promotion_error))
            print(f'While bulk uploading promotions error occured as-> {str(promotion_error)}')
            return JsonResponse(
                {
                    "response": {
                        "status": False,
                        "error": f"Error occured on promotions bulk upload",
                    }
                }
            )
    except zipfile.BadZipFile:
        return JsonResponse(
            {
                "response": {
                    "status": False,
                    "error": "File not recognized as excel file.",
                }
            }
        )
    return JsonResponse({"response": data})
