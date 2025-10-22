"""bulk upload helper functions"""

# Date - 23/11/2021

# File details-
#   Author          - Manish Pawar
#   Description     - This file is contains bulk upload helper functions.
#   Name            - Station Bulk upload helper functions
#   Modified by     - Vismay Raul
#   Modified date   - 23/11/2023

# imports required to create views
import concurrent.futures
import math
import pandas as pd
from django.utils import timezone

# pylint:disable=import-error
from sharedServices.model_files.valeting_models import ValetingMachine
from sharedServices.model_files.station_models import Stations, ChargePoint

from sharedServices.model_files.config_models import (
    MapMarkerConfigurations,
    ServiceConfiguration,
)

from sharedServices.common import (
    array_string_striper,
    field_checker_func,
    field_checker_func_with_ignore_fields,
    remove_whitespace,
    error_messages_object_formatter,
    array_to_string_converter,
)

from sharedServices.constants import (
    FOOD_TO_GO,
    FUEL_BRANDS,
    IS_EV_KEYS,
    IS_MFG_KEYS,
    STATION_ID,
    YES,
    NO,
)

from .stations_helper_functions import (
    bulk_upload_working_hours_formatter_and_validator,
    get_station_address_from_post_code,
)
from .app_level_constants import (
    NO_CHARGEPOINTS_PROVIDED_MESSAGE,
    NON_EV_STATION_TYPE,
)
from sharedServices.model_files.ocpi_credentials_models import OCPICredentials
from sharedServices.model_files.ocpi_locations_models import (OCPILocation,OCPIConnector,OCPIEVSE)
from sharedServices.ocpi_common_functions import (get_back_office_data,get_location_backoffice)



def fields_errors(list_of_fields_for_iteration, data_frame, i, validator, tab):
    """this fuction returns errors of missing fields"""
    error_tracker = []
    validator_one = field_checker_func(
        list_of_fields_for_iteration, data_frame, i
    )
    if len(list_of_fields_for_iteration) != len(validator_one[1]):
        error_message_text = ""
        for f_error in validator[1]:
            if len(error_message_text) > 0:
                error_message_text += f", {f_error}"
            else:
                error_message_text = f_error
        error_tracker.append(
            error_messages_object_formatter(
                [STATION_ID, "Error"],
                [
                    f"{data_frame['Station ID'][i]} ({tab})",
                    f'Please provide these required fields \
                        ->"{error_message_text}"',
                ],
            )
        )
    return error_tracker


def return_station_addition_status(
    data_frame, i, chargepoint_stations_from_sheet
):
    """this function return whether station  can be added or not"""

    stations_queryset = Stations.objects.filter()
    charepoints = ChargePoint.objects.filter()
    station_exists = stations_queryset.filter(
        station_id__exact=remove_whitespace(str(data_frame[STATION_ID][i]))
    )
    station_type = "MFG Forecourt"
    if data_frame[FUEL_BRANDS][i].split("|")[0] == "EV Power":
        station_type = "MFG EV"
    try:
        if data_frame[FUEL_BRANDS][i].split("|")[1]:
            station_type = "MFG EV plus Forecourt"
    except (KeyError, ValueError, IndexError):
        pass
    is_mfg_helper = NO
    if station_type in IS_MFG_KEYS:
        is_mfg_helper = YES
    # Station insert operation
    is_ev_helper = NO
    if station_type in IS_EV_KEYS:
        is_ev_helper = YES
    station_can_be_added = True
    if is_ev_helper == YES:
        if station_exists.first():
            station_have_cp = charepoints.filter(
                station_id=station_exists.first(), deleted=NO
            )
            if station_have_cp.first() is None:
                if (
                    data_frame[STATION_ID][i]
                    not in chargepoint_stations_from_sheet
                ):
                    station_can_be_added = False

        else:
            if (
                data_frame[STATION_ID][i]
                not in chargepoint_stations_from_sheet
            ):
                station_can_be_added = False
    return [
        station_can_be_added,
        is_ev_helper,
        is_mfg_helper,
        station_exists,
        station_type,
    ]


def station_add_or_update_function_for_bulk(*args):
    """this is the function to add or update station in bulk upload"""
    (
        data_frame,
        i,
        station_exists,
        is_mfg_helper,
        is_ev_helper,
        station_type,
        user,
    ) = args
    error_tracker = []
    station_id_for_create = None
    location_id = None
    station_data_for_update = None
    station_data_for_create = None
    station_brand_marker_exists = False
    marker = MapMarkerConfigurations.objects.filter(
        map_marker_key=str(data_frame[FUEL_BRANDS][i].split("|")[0])
    )
    if marker.first():
        station_brand_marker_exists = True

    (
        postal_code,
        town,
        address_line1,
        address_line2,
        address_line3,
        address_error_tracker,
    ) = get_station_address_from_post_code(data_frame, i)

    error_tracker += address_error_tracker
    phone_number = remove_whitespace(str(data_frame["Phone Number"][i]))
    created_date_helper = timezone.localtime(timezone.now())
    user_name = user.full_name
    if station_brand_marker_exists:
        if station_exists.first():
            station_data_for_update = {
                "station_id": remove_whitespace(
                    str(data_frame[STATION_ID][i])
                ),
                "station_name": data_frame["Station Name"][i],
                "station_address1": address_line1,
                "station_address2": address_line2,
                "station_address3": address_line3,
                "post_code": postal_code,
                "town": town,
                "brand": data_frame[FUEL_BRANDS][i].split("|")[0],
                "owner": "MFG",
                "latitude": data_frame["Location Latitude"][i],
                "longitude": data_frame["Location Longitude"][i],
                "phone": phone_number,
                "status": "Active",
                "station_type": station_type,
                "is_mfg": is_mfg_helper,
                "is_ev": is_ev_helper,
                "created_date": created_date_helper,
                "updated_by": user_name,
                "valeting": str(data_frame["Valeting"][i]),
                "site_id": (
                    None
                    if math.isnan(float(data_frame["Site Id"][i]))
                    else int(data_frame["Site Id"][i])
                ),
                "payment_terminal": array_to_string_converter(
                    data_frame["Payment Terminal"][i]
                    .replace("Receipt Hero", "Worldline")
                    .strip()
                    .split("|")
                ),
                "receipt_hero_site_name": data_frame["RH Site Name"][i],
                "overstay_fee": (
                    None
                    if math.isnan(float(data_frame["Overstay Fee"][i]))
                    else int(float(data_frame["Overstay Fee"][i]))
                ),
                "valeting_site_id": str(data_frame["Valeting Site ID"][i]) if "Valeting Site ID" in data_frame.columns else None,# if data_frame["Valeting Site ID"][i] else None,
                "ampeco_site_title": data_frame["Ampeco Site Title"][i],
                "ampeco_site_id": (
                    # None
                    # if math.isnan(data_frame["Ampeco Site ID"][i])
                    # else str(data_frame["Ampeco Site ID"][i])
                    None
                    if pd.isna(data_frame["Ampeco Site ID"][i])
                    else str(data_frame["Ampeco Site ID"][i])
                ),
                "parking_details":data_frame["Parking Details"][i] if data_frame["Parking Details"][i] else None
            }

            country_code,party_id = get_back_office_data(str(data_frame["Back Office"][i]).upper())
            location = OCPILocation.objects.filter(
                country_code = country_code,
                party_id = party_id,
                location_id = str(data_frame["Location ID"][i])
            ).update(
                station_mapping_id = station_exists.first()
            )
            if OCPILocation.objects.filter(
                country_code = country_code,
                party_id = party_id,
                location_id = str(data_frame["Location ID"][i])
                ).first() is None:
                error_tracker.append(
                    error_messages_object_formatter(
                        [STATION_ID, "Error"],
                        [
                            f"{data_frame['Station ID'][i]} (Sites Tab)",
                            f"{data_frame['Location ID'][i]}\
                                Location is not available\
                                for back office {data_frame['Back Office'][i]}" 
                        ],
                    )
                )
        else:
            station_data_for_create = Stations(
                station_id=remove_whitespace(str(data_frame[STATION_ID][i])),
                station_name=data_frame["Station Name"][i],
                station_address1=address_line1,
                station_address2=address_line2,
                station_address3=address_line3,
                post_code=postal_code,
                town=town,
                brand=data_frame[FUEL_BRANDS][i].split("|")[0],
                owner="MFG",
                latitude=data_frame["Location Latitude"][i],
                longitude=data_frame["Location Longitude"][i],
                phone=phone_number,
                status="Active",
                station_type=station_type,
                is_mfg=is_mfg_helper,
                is_ev=is_ev_helper,
                created_date=created_date_helper,
                updated_by=user_name,
                valeting=str(data_frame["Valeting"][i]),
                site_id=(
                    None
                    if math.isnan(float(data_frame["Site Id"][i]))
                    else int(data_frame["Site Id"][i])
                ),
                payment_terminal=array_to_string_converter(
                    data_frame["Payment Terminal"][i]
                    .replace("Receipt Hero", "Worldline")
                    .strip()
                    .split("|")
                ),
                receipt_hero_site_name=data_frame["RH Site Name"][i],
                overstay_fee=(
                    None
                    if math.isnan(float(data_frame["Overstay Fee"][i]))
                    else int(float(data_frame["Overstay Fee"][i]))
                ),
                valeting_site_id=str(data_frame["Valeting Site ID"][i]) if "Valeting Site ID" in data_frame.columns else None,#if data_frame["Valeting Site ID"][i] else None,
                ampeco_site_title=data_frame["Ampeco Site Title"][i],
                ampeco_site_id=(
                    # None
                    # if math.isnan(data_frame["Ampeco Site ID"][i])
                    # else str(data_frame["Ampeco Site ID"][i])
                    None
                    if pd.isna(data_frame["Ampeco Site ID"][i])
                    else str(data_frame["Ampeco Site ID"][i])
                ),
                parking_details=data_frame["Parking Details"][i]
            )
            back_office = None if pd.isna(data_frame["Back Office"][i]) else str(data_frame["Back Office"][i]).upper()
            station_id_for_create = remove_whitespace(str(data_frame[STATION_ID][i]))
            country_code,party_id = get_back_office_data(back_office)
            location = OCPILocation.objects.filter(
                country_code = country_code,
                party_id = party_id,
                location_id = str(data_frame["Location ID"][i])
            )
            if location.first():
                location_id = location.first().id
            else :
                error_tracker.append(
                    error_messages_object_formatter(
                        [STATION_ID, "Error"],
                        [
                            f"{data_frame['Station ID'][i]} (Sites Tab)",
                            f"{data_frame['Back Office'][i]}\
                                Location is not available\
                                for back office {data_frame['Location ID'][i]}" 
                        ],
                    )
                )
    else:
        error_tracker.append(
            error_messages_object_formatter(
                [STATION_ID, "Error"],
                [
                    f"{data_frame['Station ID'][i]} (Sites Tab)",
                    f"{data_frame['Fuel Brands'][i].split('|')[0]}\
                        brand is not added in the admin \
                            sites configuration",
                ],
            )
        )
    return [station_data_for_create, station_data_for_update, error_tracker,station_id_for_create,location_id]


def add_or_update_bulk_station_working_hours_func(data_frame, i, user):
    """this function add or updates station working hours in bulk"""
    error_tracker = []
    station_data_for_create_working_hours = None
    station_data_for_update_working_hours = None
    working_hours_result = bulk_upload_working_hours_formatter_and_validator(
        data_frame, i
    )
    if working_hours_result:
        (
            working_hours_exists_for_station,
            monday_friday,
            saturday,
            sunday,
            working_hours_error_tracker,
        ) = working_hours_result
        error_tracker += working_hours_error_tracker
    else:
        (
            monday_friday,
            saturday,
            sunday,
            working_hours_exists_for_station,
        ) = ("", "", "", None)
        error_tracker.append(
            error_messages_object_formatter(
                [STATION_ID, "Error"],
                [
                    f"{data_frame['Station ID'][i]} (Sites Tab)",
                    "Not able to get working hours",
                ],
            )
        )
    if (
        working_hours_exists_for_station
        and working_hours_exists_for_station.first()
    ):
        station_data_for_update_working_hours = {
            "id": working_hours_exists_for_station.first().id,
            "monday_friday": monday_friday,
            "saturday": saturday,
            "sunday": sunday,
            "updated_date": timezone.localtime(timezone.now()),
            "updated_by": user.full_name,
        }

    else:
        station_data_for_create_working_hours = {
            "station_id": remove_whitespace(str(data_frame[STATION_ID][i])),
            "monday_friday": monday_friday,
            "saturday": saturday,
            "sunday": sunday,
            "updated_date": timezone.localtime(timezone.now()),
            "updated_by": user.full_name,
        }

    return [
        station_data_for_create_working_hours,
        station_data_for_update_working_hours,
        error_tracker,
    ]


def upload_sites_data(*args):
    """upload sites data"""
    (
        data_frame,
        list_of_fields,
        chargepoint_stations_from_sheet,
        user,
        list_of_fields_for_iteration,
    ) = args
    station_data_for_update = []
    station_data_for_create = []
    location_mapping_for_create = {}
    station_data_for_create_working_hours = []
    station_data_for_update_working_hours = []
    station_services_create_data = []
    sheet_overall_services = []

    sites_error_tracker = []

    service_configurations = ServiceConfiguration.objects.filter()

    def upload_station_data(i):
        error_tracker = []
        validator = field_checker_func(list_of_fields, data_frame, i)
        if validator[0]:
            error_tracker += fields_errors(
                list_of_fields_for_iteration,
                data_frame,
                i,
                validator,
                "Sites tab",
            )
            return error_tracker
        (
            station_can_be_added,
            is_ev_helper,
            is_mfg_helper,
            station_exists,
            station_type,
        ) = return_station_addition_status(
            data_frame, i, chargepoint_stations_from_sheet
        )

        if station_can_be_added:
            (
                create_station_data,
                update_station_data,
                errors,
                station_id_for_create,
                station_create_location_mapping
            ) = station_add_or_update_function_for_bulk(
                data_frame,
                i,
                station_exists,
                is_mfg_helper,
                is_ev_helper,
                station_type,
                user,
            )
            if create_station_data:
                station_data_for_create.append(create_station_data)
            if station_create_location_mapping:
                location_mapping_for_create[station_id_for_create]=station_create_location_mapping
            if update_station_data:
                station_data_for_update.append(update_station_data)
            error_tracker += errors

            (
                create_station_working_hours_data,
                update_station_working_hours_data,
                working_hours_errors,
            ) = add_or_update_bulk_station_working_hours_func(
                data_frame, i, user
            )
            if create_station_working_hours_data:
                station_data_for_create_working_hours.append(
                    create_station_working_hours_data
                )
            if update_station_working_hours_data:
                station_data_for_update_working_hours.append(
                    update_station_working_hours_data
                )
            services = []
            error_tracker += working_hours_errors
            if not pd.isna(data_frame["Services"][i]):
                if "|" in data_frame["Services"][i]:
                    services = data_frame["Services"][i].split("|")
                else:
                    services = [data_frame["Services"][i]]
                services = array_string_striper(services)

                # assigning service to station
                for service in services:
                    if service.strip() not in sheet_overall_services:
                        sheet_overall_services.append(service.strip())

            station_services_create_data.append(
                {
                    "services": services,
                    "station_id": remove_whitespace(
                        str(data_frame[STATION_ID][i])
                    ),
                    "created_date": timezone.localtime(timezone.now()),
                    "updated_by": user.full_name,
                    "service_type": "Amenity",
                }
            )

        else:
            error_tracker.append(
                error_messages_object_formatter(
                    [STATION_ID, "Error"],
                    [
                        f"{data_frame['Station ID'][i]} (Sites Tab)",
                        NO_CHARGEPOINTS_PROVIDED_MESSAGE,
                    ],
                )
            )

        return error_tracker

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(
            upload_station_data,
            list(range(0, len(data_frame[STATION_ID]))),
        )
        for result in results:
            if len(result) > 0:
                sites_error_tracker += result

    for service in sheet_overall_services:
        service_from_configuration = service_configurations.filter(
            service_name__exact=service.strip(), service_type="Amenity"
        )
        if service_from_configuration.first() is None:
            sites_error_tracker.append(
                error_messages_object_formatter(
                    [STATION_ID, "Error"],
                    [
                        "All sites (Sites Tab)",
                        f'Services column -> "{service}" is not added\
                            in Admin Portal Amenity configurations.',
                    ],
                )
            )
    # location_mapping_for_create_obj = {"data": location_mapping_for_create}
    station_data_for_create_and_location = [
        station_data_for_create,                   
        [location_mapping_for_create]
    ]
    return [
        sites_error_tracker,
        station_data_for_create_and_location,
        station_data_for_update,
        station_data_for_create_working_hours,
        station_data_for_update_working_hours,
        station_services_create_data,
    ]


def upload_station_devices(*args):
    """upload station chargepoints and connectors"""
    (
        sites_bulk_upload_progress,
        devices_list_of_fields_helper,
        devices_data_frame_helper,
        stations_from_sheet_helper,
        user,
        device_list_of_field_for_iteration,
    ) = args

    chargepoints_create_data = []
    connectors_create_data = []
    devices_error_tracker = []

    def upload_device_data(i):
        current_count = (
            int(sites_bulk_upload_progress.first().uploaded_rows_count) + 1
        )
        sites_bulk_upload_progress.update(uploaded_rows_count=current_count)
        error_tracker = []
        validator = field_checker_func(
            devices_list_of_fields_helper, devices_data_frame_helper, i
        )
        if validator[0]:
            error_tracker += fields_errors(
                device_list_of_field_for_iteration,
                devices_data_frame_helper,
                i,
                validator,
                "Chargepoint tab",
            )
            return error_tracker
        station = None
        try:
            station_exists = Stations.objects.filter(
                station_id=remove_whitespace(
                    str(devices_data_frame_helper[STATION_ID][i])
                )
            )
            if station_exists.first():
                station = True
            elif (
                remove_whitespace(
                    str(devices_data_frame_helper[STATION_ID][i])
                )
                in stations_from_sheet_helper
            ):
                station = True
        except TimeoutError:
            pass
        if station:
            location = OCPILocation.objects.filter(station_mapping_id = station_exists.first()).first()
            if location:
                evse = OCPIEVSE.objects.filter(uid = devices_data_frame_helper["Evse UID"][i], location_id =  location).first()
                if evse:
                    ocpi_connector = OCPIConnector.objects.filter(connector_id = devices_data_frame_helper["Ocpi Connector ID"][i], evse_id =  evse).first()
                    if not ocpi_connector:
                        error_tracker.append(
                            error_messages_object_formatter(
                                [STATION_ID, "Error"],
                                [
                                    f"{devices_data_frame_helper['Station ID'][i]}\
                                        (Chargepoint Tab)",
                                    f"Invalid EVSE - Connector mapping\
                                    {evse.uid}\
                                    -> {devices_data_frame_helper['Ocpi Connector ID'][i]}",
                                ],
                            )
                        )
                else:
                    error_tracker.append(
                        error_messages_object_formatter(
                            [STATION_ID, "Error"],
                            [
                                f"{devices_data_frame_helper['Station ID'][i]}\
                                    (Chargepoint Tab)",
                                f"Invalid Location - EVSE mapping\
                                    {location.location_id}\
                                    -> {devices_data_frame_helper['Evse UID'][i]}",

                            ],
                        )
                    )
            else:
                error_tracker.append(
                    error_messages_object_formatter(
                        [STATION_ID, "Error"],
                        [
                            f"{devices_data_frame_helper['Station ID'][i]}\
                                (Chargepoint Tab)",
                            f"Station not mapped to a location",
                        ],
                    )
                )
            chargepoint_id = ""
            back_office = get_location_backoffice(location)
            try:
                chargepoint_id = remove_whitespace(
                    str(int(devices_data_frame_helper["Charge point ID"][i]))
                )
            except (KeyError, ValueError):
                chargepoint_id = remove_whitespace(
                    str(devices_data_frame_helper["Charge point ID"][i])
                )
            chargepoints_create_data.append(
                {
                    "station_id": remove_whitespace(
                        str(devices_data_frame_helper[STATION_ID][i])
                    ),
                    "charger_point_id": remove_whitespace(chargepoint_id),
                    "charger_point_name": devices_data_frame_helper[
                        "Chargepoint name"
                    ][i],
                    "charger_point_status": devices_data_frame_helper[
                        "Chargepoint activation status"
                    ][i],
                    "back_office": back_office,
                    "device_id": devices_data_frame_helper["Device ID"][i],
                    "payter_terminal_id": devices_data_frame_helper[
                        "Payter Terminal ID"
                    ][i],
                    "worldline_terminal_id": devices_data_frame_helper[
                        "Worldline Terminal ID"
                    ][i],
                    "created_date": timezone.localtime(timezone.now()),
                    "updated_by": user.full_name,
                    "ampeco_charge_point_id": (
                        devices_data_frame_helper["Ampeco Chargepoint ID"][i]
                    ),
                    "ampeco_charge_point_name": (
                        devices_data_frame_helper["Ampeco Chargepoint Name"][i]
                    )
                }
            )
            connector_id = ""
            try:
                connector_id = remove_whitespace(
                    str(int(devices_data_frame_helper["Connecter Id"][i]))
                )
            except (KeyError, ValueError):
                connector_id = remove_whitespace(
                    str(devices_data_frame_helper["Connecter Id"][i])
                )
            tariff_currencies = ["GBP(£)", "Euro(€)"]
            tariff_currency = devices_data_frame_helper["Tariff currency"][i]
            for tariff_currenci in tariff_currencies:
                if (
                    devices_data_frame_helper["Tariff currency"][i]
                    in tariff_currenci
                ):
                    tariff_currency = tariff_currenci
            connectors_create_data.append(
                {
                    "station_id": remove_whitespace(
                        str(devices_data_frame_helper[STATION_ID][i])
                    ),
                    "charger_point_id": remove_whitespace(chargepoint_id),
                    "connector_id": connector_id,
                    "connector_name": devices_data_frame_helper["Socket name"][
                        i
                    ],
                    "connector_type": devices_data_frame_helper[
                        "Connector Type"
                    ][i],
                    "plug_type_name": devices_data_frame_helper[
                        "Connecter Plug type"
                    ][i],
                    "status": "Active",
                    "max_charge_rate": remove_whitespace(
                        str(devices_data_frame_helper["Power in kw"][i])
                    ),
                    "connector_sorting_order": remove_whitespace(
                        str(
                            devices_data_frame_helper["Connector Sort order"][
                                i
                            ]
                        )
                    ),
                    "tariff_amount": float(
                        devices_data_frame_helper["Tariff amount"][i]
                    ),
                    "tariff_currency": remove_whitespace(str(tariff_currency)),
                    "created_date": timezone.localtime(timezone.now()),
                    "updated_by": user.full_name,
                    "evse_uid":devices_data_frame_helper[
                        "Evse UID"
                    ][i],
                    "ocpi_connector_id":devices_data_frame_helper[
                        "Ocpi Connector ID"
                    ][i],
                    "back_office" : back_office
                }
            )

        else:
            error_tracker.append(
                error_messages_object_formatter(
                    [STATION_ID, "Error"],
                    [
                        f"{devices_data_frame_helper['Station ID'][i]}\
                            (Chargepoint Tab)",
                        f"Not able to fetch station for chargepoint->\
                            {devices_data_frame_helper['Charge point ID'][i]}\
                            with connector ->\
                                {devices_data_frame_helper['Connecter Id'][i]}\
                                    with provided Station Id",
                    ],
                )
            )

        return error_tracker

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(
            upload_device_data,
            list(range(0, len(devices_data_frame_helper[STATION_ID]))),
        )
        for result in results:
            if len(result) > 0:
                devices_error_tracker += result
    return [
        devices_error_tracker,
        chargepoints_create_data,
        connectors_create_data,
    ]


def upload_valeting_details_in_bulk(*args):
    (
        sites_bulk_upload_progress,
        valeting_list_of_fields_helper,
        valeting_data_frame_helper,
        stations_from_sheet_helper,
        user,
        valeting_list_of_field_for_iteration,
    ) = args
    valeting_terminals_create_data = []
    valeting_details_error_tracker = []

    def upload_valeting_data(i):
        current_count = (
            int(sites_bulk_upload_progress.first().uploaded_rows_count) + 1
        )
        sites_bulk_upload_progress.update(uploaded_rows_count=current_count)
        error_tracker = []
        validator = field_checker_func(
            valeting_list_of_fields_helper, valeting_data_frame_helper, i
        )
        if validator[0]:
            error_tracker += fields_errors(
                valeting_list_of_field_for_iteration,
                valeting_data_frame_helper,
                i,
                validator,
                "Valeting Terminals tab",
            )
            return error_tracker
        station = False
        if (
            Stations.objects.filter(
                station_id=remove_whitespace(
                    str(valeting_data_frame_helper[STATION_ID][i])
                )
            ).first()
            or remove_whitespace(
                str(valeting_data_frame_helper[STATION_ID][i])
            )
            in stations_from_sheet_helper
        ):
            station = True
        if station:
            all_amenities = ServiceConfiguration.objects.filter(
                service_type="Amenity"
            ).values_list("service_name", flat=True)
            valid_station_amenities = []
            if not pd.isna(valeting_data_frame_helper["Amenities"][i]):
                if "|" in valeting_data_frame_helper["Amenities"][i]:
                    station_amenities = valeting_data_frame_helper[
                        "Amenities"
                    ][i].split("|")
                else:
                    station_amenities = [
                        valeting_data_frame_helper["Amenities"][i]
                    ]
                station_amenities = array_string_striper(station_amenities)
            for amenity in station_amenities:
                if amenity not in all_amenities:
                    error_tracker.append(
                        error_messages_object_formatter(
                            [STATION_ID, "Error"],
                            [
                                f"{valeting_data_frame_helper['Station ID'][i]}\
                            (Valeting Terminals Tab)",
                                f"Invalid amenity -> {amenity} in \
                                    {valeting_data_frame_helper['Amenities'][i]}",
                            ],
                        )
                    )
                else:
                    valid_station_amenities.append(amenity)
            valeting_terminals_create_data.append(
                {
                    "station_id": remove_whitespace(
                        str(valeting_data_frame_helper[STATION_ID][i])
                    ),
                    "payter_serial_number": remove_whitespace(
                        str(
                            valeting_data_frame_helper["Payter Serial Number"][
                                i
                            ]
                        )
                    ),
                    "status": valeting_data_frame_helper["Status"][i],
                    "amenities": valid_station_amenities,
                    "created_updated_date": timezone.localtime(timezone.now()),
                    "updated_by": user.full_name,
                }
            )
        else:
            error_tracker.append(
                error_messages_object_formatter(
                    [STATION_ID, "Error"],
                    [
                        f"{valeting_data_frame_helper['Station ID'][i]}\
                            (Valeting Terminals Tab)",
                        f"Not able to fetch station for valeting terminal->\
                            {valeting_data_frame_helper['Payter serial Number'][i]}\
                                with provided Station Id",
                    ],
                )
            )
        return error_tracker

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(
            upload_valeting_data,
            list(range(0, len(valeting_data_frame_helper[STATION_ID]))),
        )
        for result in results:
            if len(result) > 0:
                valeting_details_error_tracker += result
    return [
        valeting_details_error_tracker,
        valeting_terminals_create_data,
    ]


def upload_station_services_in_bulk(
    site_details_data_frame, i, user, service_key, service_type
):
    """this function upload station  services in bulk upload"""
    shops = []
    if not pd.isna(site_details_data_frame[service_key][i]):
        if "&" in site_details_data_frame[service_key][i]:
            shops = site_details_data_frame[service_key][i].split("&")
        else:
            if len(site_details_data_frame[service_key][i].strip()) > 0:
                shops = [site_details_data_frame[service_key][i]]
    # Removing extra spaces from strings within array
    if len(shops) > 0:
        shops = array_string_striper(shops)

    return [
        shops,
        {
            "services": shops,
            "station_id": remove_whitespace(
                str(site_details_data_frame[STATION_ID][i])
            ),
            "created_date": timezone.localtime(timezone.now()),
            "updated_by": user.full_name,
            "service_type": service_type,
        },
    ]


def upload_station_details_in_bulk(*args):
    """this function adds stations details in bulk"""
    (
        sites_bulk_upload_progress,
        site_details_list_of_fields,
        site_details_data_frame,
        stations_from_sheet_helper,
        user,
        site_details_list_of_fields_for_iteration,
    ) = args
    service_configurations = ServiceConfiguration.objects.filter()

    site_details_update_data = []
    station_services_create_data = []
    sheet_overall_food_to_go_shops = []
    sheet_overall_retail_shop = []
    site_details_error_tracker = []

    def upload_station_details_data(i):
        current_count = (
            int(sites_bulk_upload_progress.first().uploaded_rows_count) + 1
        )
        sites_bulk_upload_progress.update(uploaded_rows_count=current_count)
        error_tracker = []
        validator = field_checker_func(
            site_details_list_of_fields, site_details_data_frame, i
        )
        if validator[0]:
            error_tracker += fields_errors(
                site_details_list_of_fields_for_iteration,
                site_details_data_frame,
                i,
                validator,
                "MFG tab",
            )
            return error_tracker
        station = None
        station_exists = Stations.objects.filter(
            station_id=remove_whitespace(
                str(site_details_data_frame[STATION_ID][i])
            )
        )
        if station_exists.first():
            station = True
        elif (
            remove_whitespace(str(site_details_data_frame[STATION_ID][i]))
            in stations_from_sheet_helper
        ):
            station = True
        if station:
            site_details_update_data.append(
                {
                    "station_id": remove_whitespace(
                        str(site_details_data_frame[STATION_ID][i])
                    ),
                    "site_title": str(
                        site_details_data_frame["Title"][i]
                    ).strip() if  pd.notna(site_details_data_frame["Title"][i]) else None,
                    "operation_region": (
                        site_details_data_frame["Ops Region"][i]
                    ).strip(),
                    "region": (site_details_data_frame["Region"][i]).strip(),
                    "regional_manager": (
                        site_details_data_frame["Regional Managers"][i]
                    ).strip(),
                    "area": remove_whitespace(
                        str(site_details_data_frame["Area"][i])
                    ),
                    "area_regional_manager": (
                        site_details_data_frame["ARM"][i]
                    ).strip(),
                    "email": remove_whitespace(
                        str(site_details_data_frame["Email Address"][i])
                    ),
                    "country": (site_details_data_frame["Country"][i]).strip(),
                    "updated_date": timezone.localtime(timezone.now()),
                    "updated_by": user.full_name,
                }
            )
            (
                food_to_go_shops,
                insert_station_food_to_gos,
            ) = upload_station_services_in_bulk(
                site_details_data_frame, i, user, "Food to Go", FOOD_TO_GO
            )
            station_services_create_data.append(insert_station_food_to_gos)
            # Assigning service to station
            for shop in food_to_go_shops:
                if shop.strip() not in sheet_overall_food_to_go_shops:
                    sheet_overall_food_to_go_shops.append(shop.strip())

            (
                retail_shops,
                insert_station_retaisl_shops,
            ) = upload_station_services_in_bulk(
                site_details_data_frame, i, user, "Retail", "Retail"
            )

            # Assigning service to station
            for shop in retail_shops:
                if shop.strip() not in sheet_overall_retail_shop:
                    sheet_overall_retail_shop.append(shop.strip())
            station_services_create_data.append(insert_station_retaisl_shops)
        else:
            error_tracker.append(
                error_messages_object_formatter(
                    [STATION_ID, "Error"],
                    [
                        f"{site_details_data_frame['Station ID'][i]}\
                            (MFG Tab)",
                        "Station with provided station id not\
                            found make sure its added earlier.",
                    ],
                )
            )
        return error_tracker

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(
            upload_station_details_data,
            list(range(0, len(site_details_data_frame[STATION_ID]))),
        )
        for result in results:
            if len(result) > 0:
                site_details_error_tracker += result

    for shop in sheet_overall_food_to_go_shops:
        service_from_configuration = service_configurations.filter(
            service_name__exact=shop.strip(), service_type=FOOD_TO_GO
        )
        if service_from_configuration.first() is None:
            site_details_error_tracker.append(
                error_messages_object_formatter(
                    [STATION_ID, "Error"],
                    [
                        "All sites (MFG Tab)",
                        f'Food to go column -> "{shop}" is not added\
                            in Admin Portal Food to go configurations.',
                    ],
                )
            )

    for shop in sheet_overall_retail_shop:
        service_from_configuration = service_configurations.filter(
            service_name__exact=shop.strip(), service_type="Retail"
        )
        if service_from_configuration.first() is None:
            site_details_error_tracker.append(
                error_messages_object_formatter(
                    [STATION_ID, "Error"],
                    [
                        "All sites (MFG Tab)",
                        f'Retail column -> "{shop}" is not added\
                            in Admin Portal Retail configurations.',
                    ],
                )
            )
    return [
        site_details_error_tracker,
        site_details_update_data,
        station_services_create_data,
    ]

def upload_valeting_machines_in_bulk(*args):
    """Bulk upload/update valeting machines data"""
    (
        sites_bulk_upload_progress,
        list_of_fields,
        data_frame,
        stations_from_sheet,
        user,
        fields_for_iteration,
    ) = args
    
    create_update_data = []
    error_tracker = []

    print("DataFrame Contents For Valeting Machines:")
    print(data_frame.to_string())

    def process_machine_row(i):
        current_count = int(sites_bulk_upload_progress.first().uploaded_rows_count) + 1
        sites_bulk_upload_progress.update(uploaded_rows_count=current_count)
        row_errors = []
        
        # Field validation
        validator = field_checker_func_with_ignore_fields(list_of_fields, data_frame, i, [3])
        if validator[0]:
            row_errors += fields_errors(
                fields_for_iteration,
                data_frame,
                i,
                validator,
                "Valeting Machines tab",
            )
            return row_errors

        # Get and clean values
        machine_id_raw = data_frame["Machine ID"][i]
        try:
            machine_id = int(remove_whitespace(str(machine_id_raw)))
        except (ValueError, TypeError):
            machine_id = 0
        station_id = remove_whitespace(str(data_frame["Station ID"][i]))
        
        # Station validation
        if not (Stations.objects.filter(station_id=station_id).exists() or 
               station_id in stations_from_sheet):
            row_errors.append(
                error_messages_object_formatter(
                    ["Station ID", "Error"],
                    [
                        f"{station_id} (Valeting Machines)",
                        f"Station not found for machine ID: {machine_id}"
                    ],
                )
            )
            return row_errors

        # Prepare data for upsert
        machine_data = {
            "machine_id": machine_id,
            "station_id": station_id,
            "machine_name": str(data_frame["Machine Name"][i]) if not pd.isna(data_frame["Machine Name"][i]) else None,
            "machine_number": str(data_frame["Machine Number"][i]) if not pd.isna(data_frame["Machine Number"][i]) else None,
            "is_active": True if str(data_frame["Active"][i]).strip().lower() == "yes" else False if not pd.isna(data_frame["Active"][i]) else True,
            "updated_by": user.full_name,
            "updated_date": timezone.localtime(timezone.now()),
        }
        
        # Only add created_date for new records
        if not ValetingMachine.objects.filter(machine_id=machine_id).exists():
            machine_data["created_date"] = timezone.localtime(timezone.now())

        create_update_data.append(machine_data)
        return row_errors

    # Process rows with thread pool
    for i in range(len(data_frame["Machine ID"])):
        result = process_machine_row(i)
        if result:
            error_tracker.extend(result)

    return [error_tracker, create_update_data]