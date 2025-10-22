"""bulk upload functions"""
# Date - 23/11/2021

# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on bulk upload of stations.
#   Name            - Station Bulk upload functions
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 26/06/2025

# imports required to create views
import threading
import concurrent.futures

from django.db import DataError, DatabaseError

# pylint:disable=import-error
from sharedServices.model_files.bulk_models import (
    BulkUploadErrorMessages,
    BulkUploadProgress,
)
from sharedServices.model_files.station_models import Stations
from sharedServices.model_files.audit_models import AuditTrail
from sharedServices.common import (
    array_to_string_converter,
    field_tracking_func,
    upload_progress_database,
    upload_progress_errors_database,
)
from sharedServices.common_audit_trail_functions import (
    add_audit_data,
    audit_data_formatter,
)
from sharedServices.constants import (
    STATION_ID,
    YES,
    SITES_CONST,
    AUDIT_ADD_CONSTANT,
    AUDIT_UPDATE_CONSTANT,
)
from adminServices.admin_app_level_constants import UPLOAD_RESPONSE

from .db_operators import (
    add_update_valeting_machines,
    create_station_func,
    station_working_hours_update_query_func,
    station_working_hours_create_query_func,
    add_station_services,
    add_station_chargepoints,
    add_station_connectors,
    update_station_details_from_mfg_tab,
    update_station_func,
    add_update_valeting_terminals,
    # update_location_mapping_func,
)
from .stations_helper_functions import (
    remove_stations_cached_data,
)
from .app_level_constants import (
    STATIONS_LIST_OF_FIELDS,
    STATIONS_IERATION_LIST_OF_FIELDS,
    SITE_DETAILS_LIST_OF_FIELDS,
    VALETING_MACHINES_LIST_OF_FIELDS,
    VALETING_TERMINALS_ITERATION_LIST_OF_FIELDS,
    VALETING_TERMINALS_LIST_OF_FIELDS,
    SITE_DETAILS_ITERATION_LIST_OF_FIELDS,
    DEVICES_LIST_OF_FIELDS,
    DEVICES_LIST_OF_FIELDS_EXPORT,
    DEVICES_ITERATION_LIST_OF_FIELDS,
    ONE,
    TWO,
    THREE,
    FOUR,
    FIVE,
    ZERO,
    LOCATION_MAPPING_ITERATION_LIST_OF_FIELDS,
    LOCATION_MAPPING_LIST_OF_FIELDS
)
from .bulk_upload_helper_functions import (
    upload_sites_data,
    upload_station_details_in_bulk,
    upload_station_devices,
    upload_valeting_details_in_bulk,
    # upload_location_mapping_details_in_bulk,
    upload_valeting_machines_in_bulk,
)


def add_audit_data_for_stations(station_ids, user):
    """this function adds audit data for bulk uploaded functions"""

    def add_station_audit_data(station_id):
        """this function adds station audit data in background"""
        station = Stations.objects.filter(station_id=station_id).first()

        if station is None:
            return None
        audit_entry = AuditTrail.objects.filter(
            data_db_id=f"{SITES_CONST}-{station.id}"
        ).last()
        new_data = audit_data_formatter(SITES_CONST, station.id)
        old_data = audit_entry.new_data if audit_entry else None
        if old_data == new_data:
            return None
        if audit_entry:
            add_audit_data(
                user,
                f"{station.station_id}, {station.station_name}",
                f"{SITES_CONST}-{station.id}",
                AUDIT_UPDATE_CONSTANT,
                SITES_CONST,
                new_data,
                old_data,
            )
        else:
            add_audit_data(
                user,
                f"{station.station_id}, {station.station_name}",
                f"{SITES_CONST}-{station.id}",
                AUDIT_ADD_CONSTANT,
                SITES_CONST,
                new_data,
                None,
            )
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
        executor.map(
            add_station_audit_data,
            list(station_ids),
        )


def background_functions_of_bulk_upload(*arg):
    """this functions uploads bulk upload data in backkground"""
    list_of_arg = list(arg)
    total_data_lenght = (
        len(list_of_arg[0][0])
        + len(list_of_arg[1])
        + len(list_of_arg[2])
        + len(list_of_arg[3])
        + len(list_of_arg[4])
        + len(list_of_arg[5])
        + len(list_of_arg[6])
        + len(list_of_arg[7])
        + len(list_of_arg[9])
        # + len(list_of_arg[10])
        + len(list_of_arg[10])
    )
    station_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="stations", uploading_status="uploading"
    )
    if station_bulk_upload_progress.first():
        total_count = (
            int(station_bulk_upload_progress.first().total_rows_count)
            + total_data_lenght
        )
        station_bulk_upload_progress.update(
            total_rows_count=total_count, uploading_status="uploading"
        )
    try:
        create_station_func(list_of_arg[0])
        update_station_func(list_of_arg[1])

        station_working_hours_create_query_func(list_of_arg[2])
        station_working_hours_update_query_func(list_of_arg[3])

        add_station_chargepoints(list_of_arg[5])
        add_station_connectors(list_of_arg[6])

        update_station_details_from_mfg_tab(list_of_arg[7])

        add_station_services(list_of_arg[4])
        add_update_valeting_terminals(list_of_arg[9])
        add_update_valeting_machines(list_of_arg[10])


        add_audit_data_for_stations(
            [added_stations.station_id for added_stations in list_of_arg[0][0]]
            + [
                updated_stations["station_id"]
                for updated_stations in list_of_arg[1]
            ],
            list_of_arg[8],
        )
    except (DataError, DatabaseError):
        station_bulk_upload_progress.update(
            total_rows_count=0,
            uploaded_rows_count=0,
            uploading_status="completed",
        )

    after_station_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="stations", uploading_status="uploading"
    )
    after_station_bulk_upload_progress.update(
        total_rows_count=0, uploaded_rows_count=0, uploading_status="completed"
    )
    remove_stations_cached_data()


def stations_bulk_upload(*args):
    """this function is the base function of station bulk upload"""
    (
        sites_tab_arguments,
        devices_tab_arguments,
        mfg_tab_arguments,
        valeting_tab_arguments,
        # location_mapping_tab_arguments,
        valeting_machine_tab_arguments,
        user,
    ) = args

    sites_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="stations",
    )
    stations_error_records = BulkUploadErrorMessages.objects.filter(
        uploaded_for="stations"
    )
    upload_progress_errors_database("stations", stations_error_records)
    stations_errors = []
    # arrays to make db operations
    station_services_create_data = []
    # stations bulk upload
    (
        sites_error_tracker,
        station_data_for_create_upload,
        station_data_for_update_upload,
        station_data_for_create_working_hours_upload,
        station_data_for_update_working_hours_upload,
        station_amenities_create_data,
    ) = upload_sites_data(
        sites_tab_arguments[ZERO],
        sites_tab_arguments[ONE],
        sites_tab_arguments[TWO],
        sites_tab_arguments[THREE],
        sites_tab_arguments[FOUR],
    )
    station_services_create_data += station_amenities_create_data
    current_count = int(
        sites_bulk_upload_progress.first().uploaded_rows_count
    ) + len(sites_tab_arguments[FIVE])

    sites_bulk_upload_progress.update(uploaded_rows_count=current_count)
    stations_errors.append({"tab": "sites", "errors": sites_error_tracker})

    # devices bulk upload
    (
        devices_error_tracker,
        chargepoints_create_data,
        connectors_create_data,
    ) = upload_station_devices(
        sites_bulk_upload_progress,
        devices_tab_arguments[ZERO],
        devices_tab_arguments[ONE],
        devices_tab_arguments[TWO],
        devices_tab_arguments[THREE],
        devices_tab_arguments[FOUR],
    )

    current_count = int(
        sites_bulk_upload_progress.first().uploaded_rows_count
    ) + len(devices_tab_arguments[FIVE])
    sites_bulk_upload_progress.update(uploaded_rows_count=current_count)
    stations_errors.append(
        {"tab": "Chargepoint", "errors": devices_error_tracker}
    )

    # site details bulk upload
    (
        site_details_error_tracker,
        site_details_update_data,
        station_shops_create_data,
    ) = upload_station_details_in_bulk(
        sites_bulk_upload_progress,
        mfg_tab_arguments[ZERO],
        mfg_tab_arguments[ONE],
        mfg_tab_arguments[TWO],
        mfg_tab_arguments[THREE],
        mfg_tab_arguments[FOUR],
    )
    station_services_create_data += station_shops_create_data
    current_count = int(
        sites_bulk_upload_progress.first().uploaded_rows_count
    ) + len(mfg_tab_arguments[FIVE])
    sites_bulk_upload_progress.update(uploaded_rows_count=current_count)
    stations_errors.append(
        {"tab": "MFG", "errors": site_details_error_tracker}
    )

    # valeting details bulk upload
    (
        valeting_details_error_tracker,
        valeting_details_create_update_data,
    ) = upload_valeting_details_in_bulk(
        sites_bulk_upload_progress,
        valeting_tab_arguments[ZERO],
        valeting_tab_arguments[ONE],
        valeting_tab_arguments[TWO],
        valeting_tab_arguments[THREE],
        valeting_tab_arguments[FOUR],
    )
    current_count = int(
        sites_bulk_upload_progress.first().uploaded_rows_count
    ) + len(valeting_tab_arguments[FIVE])
    sites_bulk_upload_progress.update(uploaded_rows_count=current_count)
    stations_errors.append(
        {"tab": "Valeting Terminals", "errors": valeting_details_error_tracker}
    )

    # valeting machines bulk upload
    (
        valeting_machines_error_tracker,
        valeting_machines_create_update_data,
    ) = upload_valeting_machines_in_bulk(
        sites_bulk_upload_progress,
        valeting_machine_tab_arguments[ZERO],
        valeting_machine_tab_arguments[ONE],
        valeting_machine_tab_arguments[TWO],
        valeting_machine_tab_arguments[THREE],
        valeting_machine_tab_arguments[FOUR],
    )
    current_count = int(
        sites_bulk_upload_progress.first().uploaded_rows_count
    ) + len(valeting_machine_tab_arguments[FIVE])
    sites_bulk_upload_progress.update(uploaded_rows_count=current_count)
    stations_errors.append(
        {"tab": "Valeting Machines", "errors": valeting_machines_error_tracker}
    )


    stations_error_records = BulkUploadErrorMessages.objects.filter(
        uploaded_for="stations"
    )
    if stations_error_records.first():
        stations_error_records.update(
            errors=array_to_string_converter(stations_errors),
            ready_to_export=YES,
        )
    start_time_stations = threading.Thread(
        target=background_functions_of_bulk_upload,
        args=[
            station_data_for_create_upload,
            station_data_for_update_upload,
            station_data_for_create_working_hours_upload,
            station_data_for_update_working_hours_upload,
            station_services_create_data,
            chargepoints_create_data,
            connectors_create_data,
            site_details_update_data,
            user,
            valeting_details_create_update_data,
            # location_mapping_create_update_data,
            valeting_machines_create_update_data
        ],
        daemon=True
    )
    start_time_stations.start()


def sites_bulk_upload(
    sheet, user_op, devices_sheet, site_details_sheet, valeting_details_sheet, valeting_machines_sheet#,location_mapping_details_sheet
):
    """sites bulk upload function"""
    data_frame = sheet
    field_tracker_stations = []
    sheet_have_field_errors = False
    sheet_field_errors_response = {
        "status": True,
        "data": {"fields": False, "data": []},
        "c_data": {"fields": False, "data": field_tracker_stations},
        "sites_data": {"fields": False, "data": []},
        "valeting_data": {"fields": False, "data": []},
        "valeting_machine_data": {"fields": False, "data": []},
        # "location_mapping_data": {"fields": False, "data": []},
    }

    if STATION_ID in devices_sheet:
        chargepoint_stations_from_sheet = list(devices_sheet[STATION_ID])
    if STATION_ID in sheet:
        stations_from_sheet = list(sheet[STATION_ID])
    if STATION_ID in site_details_sheet:
        stations_details_from_sheet = list(site_details_sheet[STATION_ID])
    if STATION_ID in valeting_details_sheet:
        valeting_details_from_sheet = list(valeting_details_sheet[STATION_ID])
    if STATION_ID in valeting_machines_sheet:
        valeting_machines_from_sheet = list(valeting_machines_sheet[STATION_ID])
    # if STATION_ID in location_mapping_details_sheet:
    #     location_mapping_details_from_sheet = list(location_mapping_details_sheet[STATION_ID])
    

    list_of_fields_stations = STATIONS_LIST_OF_FIELDS
    list_of_fields_for_iteration_stations = STATIONS_IERATION_LIST_OF_FIELDS
    field_tracker_stations = field_tracking_func(
        list_of_fields_for_iteration_stations, data_frame
    )

    if len(field_tracker_stations) > 0:
        sheet_have_field_errors = True
        sheet_field_errors_response["data"] = {
            "fields": True,
            "data": field_tracker_stations,
        }

    # Charging Point
    devices_data_frame = devices_sheet
    field_tracker_stations = []

    devices_list_of_fields = DEVICES_LIST_OF_FIELDS
    devices_list_of_fields_for_iteration = DEVICES_ITERATION_LIST_OF_FIELDS
    field_tracker_stations = field_tracking_func(
        devices_list_of_fields_for_iteration, devices_data_frame
    )

    if len(field_tracker_stations) > 0:
        sheet_have_field_errors = True
        sheet_field_errors_response["c_data"] = {
            "fields": True,
            "data": field_tracker_stations,
        }

    # MFG
    site_details_data_frame = site_details_sheet
    field_tracker = []
    site_details_list_of_fields = SITE_DETAILS_LIST_OF_FIELDS
    site_details_list_of_fields_for_iteration = (
        SITE_DETAILS_ITERATION_LIST_OF_FIELDS
    )

    field_tracker = field_tracking_func(
        site_details_list_of_fields_for_iteration, site_details_data_frame
    )
    if len(field_tracker) > 0:
        sheet_have_field_errors = True
        sheet_field_errors_response["sites_data"] = {
            "fields": True,
            "data": field_tracker,
        }

    # Valeting
    valeting_details_data_frame = valeting_details_sheet
    field_tracker = []
    valeting_details_list_of_fields = VALETING_TERMINALS_LIST_OF_FIELDS
    valeting_details_list_of_fields_for_iteration = (
        VALETING_TERMINALS_ITERATION_LIST_OF_FIELDS
    )

    field_tracker = field_tracking_func(
        valeting_details_list_of_fields_for_iteration,
        valeting_details_data_frame,
    )
    if len(field_tracker) > 0:
        sheet_have_field_errors = True
        sheet_field_errors_response["valeting_data"] = {
            "fields": True,
            "data": field_tracker,
        }

    # Valeting Machines
    valeting_machines_data_frame = valeting_machines_sheet
    field_tracker = []
    valeting_machines_list_of_fields = VALETING_MACHINES_LIST_OF_FIELDS
    valeting_machines_list_of_fields_for_iteration = (
        VALETING_MACHINES_LIST_OF_FIELDS
    )

    field_tracker = field_tracking_func(
        valeting_machines_list_of_fields_for_iteration,
        valeting_machines_data_frame,
    )
    if len(field_tracker) > 0:
        sheet_have_field_errors = True
        sheet_field_errors_response["valeting_machine_data"] = {
            "fields": True,
            "data": field_tracker,
        }

    # #Ocpi location mapping
    # location_mapping_details_data_frame = location_mapping_details_sheet
    # field_tracker = []
    # location_mapping_details_list_of_fields = LOCATION_MAPPING_LIST_OF_FIELDS
    # location_mapping_details_list_of_fields_for_iteration = (
    #     LOCATION_MAPPING_ITERATION_LIST_OF_FIELDS
    # )

    # field_tracker = field_tracking_func(
    #     location_mapping_details_list_of_fields_for_iteration,
    #     location_mapping_details_data_frame,
    # )
    
    # if len(field_tracker) > 0:
    #     sheet_have_field_errors = True
    #     sheet_field_errors_response["location_mapping_data"] = {
    #         "fields": True,
    #         "data": field_tracker,
    #     }

    if sheet_have_field_errors is True:
        return sheet_field_errors_response

    total_data_count = (
        len(chargepoint_stations_from_sheet)
        + len(stations_from_sheet)
        + len(stations_details_from_sheet)
        + len(valeting_details_from_sheet)
        + len(valeting_machines_from_sheet)
        # + len(location_mapping_details_from_sheet)
        + 150
    )
    station_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="stations",
    )
    upload_progress_database(
        "stations", station_bulk_upload_progress, total_data_count
    )

    start_time_stations = threading.Thread(
        target=stations_bulk_upload,
        args=[
            [
                data_frame,
                list_of_fields_stations,
                chargepoint_stations_from_sheet,
                user_op,
                list_of_fields_for_iteration_stations,
                stations_from_sheet,
            ],
            [
                devices_list_of_fields,
                devices_data_frame,
                stations_from_sheet,
                user_op,
                devices_list_of_fields_for_iteration,
                chargepoint_stations_from_sheet,
            ],
            [
                site_details_list_of_fields,
                site_details_data_frame,
                stations_from_sheet,
                user_op,
                site_details_list_of_fields_for_iteration,
                stations_details_from_sheet,
            ],
            [
                valeting_details_list_of_fields,
                valeting_details_data_frame,
                stations_from_sheet,
                user_op,
                valeting_details_list_of_fields_for_iteration,
                valeting_details_from_sheet,
            ],
            [
                valeting_machines_list_of_fields,
                valeting_machines_data_frame,
                stations_from_sheet,
                user_op,
                valeting_machines_list_of_fields_for_iteration,
                valeting_machines_from_sheet,
            ],
            # [
            #     location_mapping_details_list_of_fields,
            #     location_mapping_details_data_frame,
            #     stations_from_sheet,
            #     user_op,
            #     location_mapping_details_list_of_fields_for_iteration,
            #     location_mapping_details_from_sheet,
            # ],
            user_op,
        ],
        daemon=True
    )
    start_time_stations.start()

    return UPLOAD_RESPONSE
