"""bulk upload views"""
# Date - 23/11/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on bulk upload of views
#   Name            - Station Bulk upload views
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 26/06/2025

# imports required to create views
# pylint:disable=import-error
import sys
import traceback
import zipfile
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from sharedServices.model_files.bulk_models import (
    BulkUploadProgress,
)
from sharedServices.decorators import authenticated_user
from sharedServices.constants import GET_METHOD_ALLOWED, POST_METHOD_ALLOWED
from adminServices.stations.views import export_errors
from .bulk_upload_functions import sites_bulk_upload


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def progress_bar_info(_):
    """progress checker function"""

    errors_export_ready_stations = export_errors()
    station_bulk_upload_progress_view = BulkUploadProgress.objects.filter(
        uploaded_for="stations",
        uploading_status="uploading",
    )
    if station_bulk_upload_progress_view.first():
        percentage_view = (
            int(station_bulk_upload_progress_view.first().total_rows_count)
            * int(
                station_bulk_upload_progress_view.first().uploaded_rows_count
            )
            / 100
        )
        if percentage_view > 100:
            percentage_view = 85
        return JsonResponse(
            {
                "status": True,
                "percentage": percentage_view,
                "errors_export_ready": errors_export_ready_stations,
            }
        )
    return JsonResponse(
        {
            "status": False,
            "percentage": 0,
            "errors_export_ready": errors_export_ready_stations,
        }
    )


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def upload_sheet(request):
    """bulk upload function"""
    excel_file_station = request.body
    data_stations = []
    tab_errors_stations = []
    try:
        xls = pd.ExcelFile(excel_file_station, engine="openpyxl")
        try:
            sites = pd.read_excel(xls, "Sites", dtype=str)
        except ValueError:
            tab_errors_stations.append('"Sites" tab')
        try:
            devices = pd.read_excel(xls, "Chargepoint")
        except ValueError:
            tab_errors_stations.append('"Chargepoint" tab')
        try:
            site_details = pd.read_excel(xls, "MFG")
        except ValueError:
            tab_errors_stations.append('"MFG" tab')
        try:
            valeting_details = pd.read_excel(xls, "Valeting Terminals")
        except ValueError:
            tab_errors_stations.append('"Valeting Terminals" tab')
        try:
            valeting_machines = pd.read_excel(xls, "Valeting Machines")
        except ValueError:
            tab_errors_stations.append('"Valeting Machines" tab')
        # try:
        #     location_mapping_details = pd.read_excel(xls, "Location Mapping")
        # except ValueError:
        #     tab_errors_stations.append('"Location Mapping" tab')

        if len(tab_errors_stations) > 0:
            error_station = ""
            for count, tab_error_s in enumerate(tab_errors_stations):
                if count == (len(tab_errors_stations) - 1):
                    error_station += tab_error_s
                else:
                    error_station += f"{tab_error_s} &"
            error_station = f"Sheet must include {error_station}"
            return JsonResponse(
                {"response": {"status": False, "error": error_station}}
            )
        try:
            data_stations = sites_bulk_upload(
                sites, request.user, devices, site_details, valeting_details, valeting_machines#,location_mapping_details
            )
        except (KeyError, AttributeError, TimeoutError) as station_error:
            (
                exception_type_station,
                exception_objet_station,
                exception_traceback_station,
            ) = sys.exc_info()
            filename = exception_traceback_station.tb_frame.f_code.co_filename
            line_number = exception_traceback_station.tb_lineno
            print(exception_objet_station, "**execption_object")
            print("Exception type: ", exception_type_station)
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
    except zipfile.BadZipFile:
        traceback.print_exc()
        return JsonResponse(
            {
                "response": {
                    "status": False,
                    "error": "File not recognized as excel file.",
                }
            }
        )
    return JsonResponse({"response": data_stations})
