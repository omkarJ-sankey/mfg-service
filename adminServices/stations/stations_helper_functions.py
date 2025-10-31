"""stations helper functions"""
# Date - 02/02/2022


# File details-
#   Author          - Manish Pawar
#   Description     - This file contains helper functions for stations.
#   Name            - Station helper functions
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 28/05/2025

# imports required to create views
import json
from types import SimpleNamespace
import threading
import itertools
import googlemaps
from decouple import config
import pandas as pd
from django.db.models import OuterRef, Subquery
from django.db.models import Value

from django.db import DataError, DatabaseError
from django.utils import timezone
from django.core.cache import cache
from django.http import JsonResponse
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.conf import settings
from django.db.models import Q
from django.urls import reverse
from django.forms.models import model_to_dict
import traceback


# pylint:disable=import-error
from sharedServices.model_files.valeting_models import ValetingMachine
from sharedServices.model_files.config_models import ConnectorConfiguration
from sharedServices.model_files.ocpi_credentials_models import OCPICredentials, OCPICredentialsRole
from sharedServices.model_files.station_models import (
    Stations,
    StationServices,
    StationConnector,
    StationWorkingHours,
    StationImages,
    ChargePoint,
    ValetingTerminals,
)
from sharedServices.common import (
    remove_all_cache,
    export_data_function_multi_tabs,
    remove_whitespace,
    remove_extra_spaces,
    error_messages_object_formatter,
    image_converter,
    randon_string_generator,
    redis_connection,
)
from sharedServices.common_audit_trail_functions import (
    add_audit_data,
    audit_data_formatter,
    add_references_to_audit_data,
)
from sharedServices.image_optimization_funcs import optimize_image
from sharedServices.shared_station_serializer import (
    caching_station_finder_data,
)
from adminServices.configurations.base_configurations_views import (
    return_already_added_ev_indictors
)
from sharedServices.ocpi_common_functions import (get_back_office_data,get_location_backoffice)

from sharedServices.constants import (
    ADDRESS_LINE_1,
    ADDRESS_LINE_2,
    ADDRESS_LINE_3,
    AZURE_BLOB_STORAGE_URL,
    GOOGLE_MAPS_EXCEPTION,
    HOURS_24,
    IS_EV_KEYS,
    IS_MFG_KEYS,
    STATION_ID,
    YES,
    NO,
    IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN,
    STATION_INFO_IMAGE,
    SITES_CONST,
    AUDIT_UPDATE_CONSTANT
)
from .db_operators import (
    insert_station_connector_data,
    insert_valeting_machines_data,
    insert_valeting_terminals_data,
    insert_station_services_data,
    insert_station_working_hours_entry,
    update_single_station_func,
    update_station_connector_data,
    update_station_services_data,
    update_station_valeting_machines,
    update_station_working_hours_entry,
    update_station_valeting_data,
)

from .app_level_constants import (
    DEVICES_LIST_OF_FIELDS_CHARGEPOINT,
    STATIONS_EXPORT,
    STATIONS_EXPORT_DETAILS,
    NO_CHARGEPOINTS_PROVIDED_MESSAGE,
    VALETING_MACHINES_LIST_OF_FIELDS,
    VALETING_TERMINAL_LIST_OF_FIELDS,
)

from sharedServices.model_files.ocpi_locations_models import OCPIConnector,OCPILocation,OCPIEVSE
from sharedServices.ocpi_common_functions import get_back_office_data


gmaps = googlemaps.Client(key=config("DJANGO_APP_GOOGLE_API_KEY"))
map_api_key = settings.GOOGLE_MAPS_API_KEY

CACHE_TTL = getattr(settings, "CACHE_TTL", DEFAULT_TIMEOUT)
# This function returns data such as operation regions, regions, area


def remove_stations_cached_data():
    """this function is used to remove cached data of stations views"""
    cache.expire("checkbox_for_assign_promotions", timeout=0)
    cache.expire("cache_station_for_filteration", timeout=0)
    cache.expire("promotion_cached_available_stations", timeout=0)
    cache.expire("cache_stations", timeout=0)
    redis_connection.delete("station_data_for_admin_loyalties_and_promotions")
    redis_connection.delete("station_data")
    redis_connection.delete("charge_points")
    redis_connection.delete("valeting_machines")
    start_caching_station_finder_data = threading.Thread(
        target=caching_station_finder_data,
        daemon=True
    )
    start_caching_station_finder_data.start()
    start_removing_all_cached_data = threading.Thread(
        target=remove_all_cache,
        daemon=True
    )
    start_removing_all_cached_data.start()



def station_site_locations_list():
    """site location list function"""
    stations = Stations.objects.all().values("station_id").distinct()
    operation_regions = (
        Stations.objects.all().values("operation_region").distinct()
    )
    regions = Stations.objects.all().values("region").distinct()
    area = Stations.objects.all().values("area").distinct()
    towns = Stations.objects.all().values("town").distinct()
    postal_codes = Stations.objects.all().values("post_code").distinct()
    brands = return_already_added_ev_indictors(True)
    owner = Stations.objects.all().values("owner").distinct()
    station_types = Stations.objects.all().values("station_type").distinct()
    types = []
    for station_type in station_types:
        if len(station_type["station_type"]) > 0:
            types.append(station_type)
    return [
        operation_regions,
        regions,
        area,
        towns,
        postal_codes,
        brands,
        owner,
        types,
        stations,
    ]


# This function returns all connector types (used in dropdown).
def connector_types():
    """connector types"""
    connectors = ConnectorConfiguration.objects.all().values(
        "connector_plug_type"
    ).distinct()
    return connectors


def split_opening_closing_timings(export_station, details):
    """this function helps to set timings"""
    if export_station is not None and export_station[details] is not None:
        opening = ""
        closing = ""
        open_time_split_working_hours = export_station[details][0:5].split(":")

        if len(open_time_split_working_hours) > 1:
            opening = (
                f"{open_time_split_working_hours[0]}"
                + ":"
                + f"{open_time_split_working_hours[1]}"
                + ":00"
            )
        else:
            opening = ""
        close_time_split_working_hours = export_station[details][6:11].split(":")

        if len(close_time_split_working_hours) > 1:
            closing = (
                f"{close_time_split_working_hours[0]}"
                + ":"
                + f"{close_time_split_working_hours[1]}"
                + ":00"
            )
        else:
            closing = ""
        return opening, closing
    return None, None


def stations_export_list(station_ids):
    """this function helps to list stations data"""
    location_qs = Subquery(
        OCPILocation.objects.filter(
        station_mapping_id=OuterRef('id')
    ).values('location_id')[:1])
    

    stations_for_export = (
        Stations.objects.filter(id__in=station_ids, deleted=NO)
        .values(
            "id",
            "station_id",
            "station_name",
            "brand",
            "owner",
            "station_address1",
            "station_address2",
            "station_address3",
            "post_code",
            "latitude",
            "longitude",
            "phone",
            "working_hours_details__monday_friday",
            "working_hours_details__saturday",
            "working_hours_details__sunday",
            "operation_region",
            "region",
            "area",
            "regional_manager",
            "area_regional_manager",
            "site_title",
            "station_type",
            "status",
            "created_date",
            "is_ev",
            "is_mfg",
            "email",
            "country",
            "site_id",
            "valeting",
            "payment_terminal",
            "receipt_hero_site_name",
            "overstay_fee",
            "valeting_site_id",
            "ampeco_site_id",
            "ampeco_site_title",
            # "station_connectors__back_office",
            "stations__id",
            "parking_details",
        ).annotate(
            location_id=Subquery(location_qs),
            
        )
        .distinct()
    )
    for obj in stations_for_export:
        location = OCPILocation.objects.filter(id = obj["stations__id"]).first()
        back_office = None
        if location:
            back_office = OCPICredentials.objects.filter(
                to_role__country_code = location.country_code,
                to_role__party_id = location.party_id,
                status = "Active"
            ).only("name").first()
        obj["back_office"] = str(back_office.name).upper() if back_office else ''
    

    for export_station in stations_for_export: 
        export_station["created_date"]=timezone.localtime(export_station["created_date"])
        export_station["amenities"] = '|'.join(
            [
                service.service_id.service_name
                for service in StationServices.objects.filter(
                    station_id=export_station["id"], service_name="Amenity", deleted=NO
                )
                if service.service_id
            ]
        )
        export_station["food_to_go"] = '&'.join([
            service.service_id.service_name
            for service in StationServices.objects.filter(
                station_id=export_station["id"],
                service_name="Food To Go",
                deleted=NO,
            )
            if service.service_id
        ])
        export_station["retail"] = '&'.join([
            service.service_id.service_name
            for service in StationServices.objects.filter(
                station_id=export_station["id"], service_name="Retail", deleted=NO
            )
            if service.service_id
        ])
        export_station["station_image"] = None
        export_station["monday_friday_opening_time"] = ""
        export_station["monday_friday_closing_time"] = ""
        export_station["saturday_opening_time"] = ""
        export_station["saturday_closing_time"] = ""
        export_station["sunday_opening_time"] = ""
        export_station["sunday_closing_time"] = ""
        # monday-friday working hours data to export
        if export_station["working_hours_details__monday_friday"] == HOURS_24:
            export_station["monday_friday_opening_status"] = "24-hours"
        else:
            export_station["monday_friday_opening_status"] = ""
            (
                export_station["monday_friday_opening_time"],
                export_station["monday_friday_closing_time"],
            ) = split_opening_closing_timings(
                export_station, "working_hours_details__monday_friday"
            )

        # saturday working hours data to export
        if export_station["working_hours_details__saturday"] == HOURS_24:
            export_station["saturday_opening_status"] = "24-hours"
        else:
            export_station["saturday_opening_status"] = ""
            (
                export_station["saturday_opening_time"],
                export_station["saturday_closing_time"],
            ) = split_opening_closing_timings(
                export_station,
                "working_hours_details__saturday",
            )
        # sunday working hours data to export
        if export_station["working_hours_details__sunday"] == HOURS_24:
            export_station["sunday_opening_status"] = "24-hours"
        else:
            export_station["sunday_opening_status"] = ""
            (
                export_station["sunday_opening_time"],
                export_station["sunday_closing_time"],
            ) = split_opening_closing_timings(
                export_station,
                "working_hours_details__sunday",
            )

        if export_station["station_type"] == "MFG EV plus Forecourt" and export_station["brand"] != 'EV Power':
            export_station["brand"] = f'{export_station["brand"]}|EV Power'
    return stations_for_export


def export_station_data_function(stations_data):
    """this function helps to exports stations data"""
    station_ids = [st.id for st in stations_data]
    stations_for_export = stations_export_list(station_ids)
    
    ocpi_connector_subquery = Subquery(
        OCPIConnector.objects.filter(
            connector_mapping_id=OuterRef('id')
        ).values('connector_id')[:1]
    )
    ocpi_evse_subquery = Subquery(
        OCPIConnector.objects.filter(
            connector_mapping_id=OuterRef('id')
        ).values('evse_id__uid')[:1]
    )
    chargepoints = StationConnector.objects.filter(
        ~Q(charge_point_id=None),
        station_id_id__in=station_ids,
        deleted=NO,
    ).values(
        "id",
        "station_id__station_id",
        "charge_point_id__charger_point_id",
        "charge_point_id__charger_point_name",
        "charge_point_id__charger_point_status",
        "connector_id",
        "connector_name",
        "plug_type_name",
        "max_charge_rate",
        "connector_sorting_order",
        "tariff_amount",
        "tariff_currency",
        "connector_type",
        "charge_point_id__back_office",
        "charge_point_id__device_id",
        "charge_point_id__payter_terminal_id",
        "charge_point_id__worldline_terminal_id",
        "charge_point_id__ampeco_charge_point_id",
        "charge_point_id__ampeco_charge_point_name",
        "connector_evse_uid",
        "station_connectors__connector_id",
    ).annotate(
        evse_uid = Subquery(ocpi_evse_subquery),
        conn_id = Subquery(ocpi_connector_subquery)
    )
    valeting_terminals = ValetingTerminals.objects.filter(
        station_id_id__in=station_ids,
        deleted=NO,
    ).values(
        "id",
        "station_id__station_id",
        "payter_serial_number",
        "status",
        "amenities",
    )
    
    #Valeting machines data
    valeting_machines = ValetingMachine.objects.filter(
        station_id_id__in=station_ids,
        deleted=False,
    ).values(
        "machine_id",
        "station_id__station_id",
        "machine_name",
        "machine_number",
        "is_active",
        "created_date",
        "updated_date",
    )

    for machine in valeting_machines:
        machine["is_active"] = "Yes" if machine["is_active"] else "No"

    sheets_data = [
        stations_for_export,
        chargepoints,
        stations_for_export,
        valeting_terminals,
        valeting_machines,
    ]
    
    columns_config = [
        STATIONS_EXPORT,
        DEVICES_LIST_OF_FIELDS_CHARGEPOINT,
        STATIONS_EXPORT_DETAILS,
        VALETING_TERMINAL_LIST_OF_FIELDS,
        VALETING_MACHINES_LIST_OF_FIELDS,
    ]
    
    rows_config = [
        [
            "id",
            "station_id",
            "station_name",
            "brand",
            "owner",
            "station_address1",
            "station_address2",
            "station_address3",
            "post_code",
            "latitude",
            "longitude",
            "phone",
            "monday_friday_opening_status",
            "monday_friday_opening_time",
            "monday_friday_closing_time",
            "saturday_opening_status",
            "saturday_opening_time",
            "saturday_closing_time",
            "sunday_opening_status",
            "sunday_opening_time",
            "sunday_closing_time",
            "is_mfg",
            "is_ev",
            "amenities",
            "created_date",
            "site_id",
            "valeting",
            "payment_terminal",
            "receipt_hero_site_name",
            "overstay_fee",
            "ampeco_site_id",
            "ampeco_site_title",
            "back_office",
            "location_id",
            "parking_details",
        ],
        [
            "id",
            "station_id__station_id",
            "charge_point_id__charger_point_id",
            "charge_point_id__charger_point_name",
            "charge_point_id__charger_point_status",
            "connector_id",
            "connector_name",
            "plug_type_name",
            "max_charge_rate",
            "connector_sorting_order",
            "tariff_amount",
            "tariff_currency",
            "connector_type",
            # "charge_point_id__back_office",
            "charge_point_id__device_id",
            "charge_point_id__payter_terminal_id",
            "charge_point_id__worldline_terminal_id",
            "charge_point_id__ampeco_charge_point_id",
            "charge_point_id__ampeco_charge_point_name",
            "evse_uid",
            "station_connectors__connector_id",
        ],
        [
            "station_id",
            "station_name",
            "operation_region",
            "region",
            "area",
            "regional_manager",
            "area_regional_manager",
            "site_title",
            "station_type",
            "status",
            "email",
            "country",
            "food_to_go",
            "retail",
        ],
        [
            "id",
            "station_id__station_id",
            "payter_serial_number",
            "status",
            "amenities",
        ],
        [
            "machine_id",
            "station_id__station_id",
            "machine_name",
            "machine_number",
            "is_active"
        ],
    ]
    
    sheet_names = [
        "Sites", 
        "Chargepoint", 
        "MFG", 
        "Valeting Terminals",
        "Valeting Machines"
    ]
    
    response = export_data_function_multi_tabs(
        sheets_data,
        columns_config,
        rows_config,
        sheet_names,
    )
    return response

def bulk_dates_weekday_status(
    data_frame,
    i,
    error_tracker_dates,
    opening_status,
    opening_time,
    closing_time,
    text,
):
    """this function formats working hours for stations"""
    status = ""
    if not pd.isna(data_frame[opening_status][i]):
        if data_frame["Monday - Friday Opening Status"][i] == "24-hours":
            status = HOURS_24
        else:
            error_tracker_dates.append(
                error_messages_object_formatter(
                    [STATION_ID, "Error"],
                    [
                        f"{data_frame['Station ID'][i]} (Sites Tab)",
                        '24 hours format error ->" {text} "Opening\
                            Status is not matched with /"24hours/"',
                    ],
                )
            )
    if pd.isna(data_frame[opening_status][i]):
        opening = ""
        issue = ""
        if not pd.isna(data_frame[opening_time][i]):
            opening = str(data_frame[opening_time][i])[:5]
        else:
            issue += "Opening time is not provided for " + text
        closing = ""

        if not pd.isna(data_frame[closing_time][i]):
            closing = str(data_frame[closing_time][i])[:5]
        else:
            if len(issue) > 0:
                issue += ", Closing time is not provided for " + text
            else:
                issue += "Closing time is not provided for " + text
        if len(issue) > 0:
            error_tracker_dates.append(
                error_messages_object_formatter(
                    [STATION_ID, "Error"],
                    [
                        f"{data_frame['Station ID'][i]} (Sites Tab)",
                        issue,
                    ],
                )
            )
        else:
            status = f"{opening}-{closing}"
    return [status, error_tracker_dates]


def bulk_dates_weekend_status(
    data_frame, i, opening_status, opening_time, closing_time
):
    """this function formats working hours for stations"""
    status = ""
    if not pd.isna(data_frame[opening_status][i]):
        if data_frame[opening_status][i] == "24-hours":
            status = HOURS_24
    if pd.isna(data_frame[opening_status][i]):
        if not pd.isna(data_frame[opening_time][i]) and not pd.isna(
            data_frame[closing_time][i]
        ):
            status = f"{str(data_frame[opening_time][i])[:5]}\
                    -{str(data_frame[closing_time][i])[:5]}"

        elif not pd.isna(data_frame[opening_time][i]):
            status = f"{str(data_frame[opening_time][i])[:5]}- null"
        elif not pd.isna(data_frame[closing_time][i]):
            status = f"null -{str(data_frame[closing_time][i])[:5]}"
    return status


def bulk_upload_working_hours_formatter_and_validator(data_frame, i):
    """this function formats working hours for stations"""
    error_tracker = []
    monday_friday = ""
    saturday = ""
    sunday = ""
    [monday_friday, error_tracker] = bulk_dates_weekday_status(
        data_frame,
        i,
        error_tracker,
        "Monday - Friday Opening Status",
        "Monday - Friday Opening Time",
        "Monday - Friday Closing Time",
        "Monday-Friday",
    )
    saturday = bulk_dates_weekend_status(
        data_frame,
        i,
        "Saturday Opening Status",
        "Saturday Opening Time",
        "Saturday Closing Time",
    )
    sunday = bulk_dates_weekend_status(
        data_frame,
        i,
        "Sunday Opening Status",
        "Sunday Opening Time",
        "Sunday Closing Time",
    )
    if len(monday_friday) > 0:
        if len(saturday) == 0:
            saturday = "Closed"
        if len(sunday) == 0:
            sunday = "Closed"
        if saturday != HOURS_24:
            saturday = remove_whitespace(saturday)
        if sunday != HOURS_24:
            sunday = remove_whitespace(sunday)
        working_hours_exists_for_station = StationWorkingHours.objects.filter(
            station_id__station_id=remove_whitespace(
                str(data_frame[STATION_ID][i])
            )
        )
        return [
            working_hours_exists_for_station,
            monday_friday,
            saturday,
            sunday,
            error_tracker,
        ]

    return None


def get_geo_location(data_frame, error_tracker, i):
    """this functions returns address details for particular station
    with the help of google API"""
    try:
        reverse_geocode = gmaps.reverse_geocode(
            (
                data_frame["Location Latitude"][i],
                data_frame["Location Longitude"][i],
            )
        )
        found_address = False
        for j in reverse_geocode:
            for rev in range(len(j["address_components"])):
                if "postal_code" in j["address_components"][rev]["types"]:
                    if remove_whitespace(
                        str(data_frame["Postcode"][i])
                    ) == remove_whitespace(
                        j["address_components"][rev]["long_name"]
                    ):
                        postal_code = j["address_components"][rev]["long_name"]
                        found_address = True
                if (
                    "street_number" in j["address_components"][rev]["types"]
                ) and found_address:
                    address_line1 = j["address_components"][rev]["long_name"]

                if (
                    "route" in j["address_components"][rev]["types"]
                ) and found_address:
                    if len(address_line1) > 0:
                        address_line1 += f",\
                            {j['address_components'][rev]['long_name']}"
                    else:
                        address_line1 = j["address_components"][rev][
                            "long_name"
                        ]
                if (
                    "postal_town" in j["address_components"][rev]["types"]
                ) and found_address:
                    town = j["address_components"][rev]["long_name"]
                    address_line2 = j["address_components"][rev]["long_name"]

                if (
                    "administrative_area_level_2"
                    in j["address_components"][rev]["types"]
                ) and found_address:
                    address_line3 = j["address_components"][rev]["long_name"]
        if not found_address:
            error_tracker.append(
                error_messages_object_formatter(
                    [STATION_ID, "Error"],
                    [
                        f"{data_frame['Station ID'][i]} (Sites Tab)",
                        "Provided postcode is not \
                            available in the given coordinates",
                    ],
                )
            )
    except GOOGLE_MAPS_EXCEPTION:
        error_tracker.append(
            error_messages_object_formatter(
                [STATION_ID, "Error"],
                [
                    f"{data_frame['Station ID'][i]} (Sites Tab)",
                    "Google API Failed to process coordinates",
                ],
            )
        )
    return [
        error_tracker,
        town,
        address_line1,
        address_line2,
        address_line3,
        postal_code,
    ]


def get_station_address_from_post_code(data_frame, i):
    """this functions returns address details for particular station
    with the help of google API"""
    error_tracker = []
    postal_code_address = ""
    town_address = ""
    address_line1_address = ""
    address_line2_address = ""
    address_line3_address = ""
    if (
        pd.isna(data_frame[ADDRESS_LINE_1][i])
        and pd.isna(data_frame[ADDRESS_LINE_2][i])
        and pd.isna(data_frame[ADDRESS_LINE_3][i])
    ):
        (
            error_tracker,
            town_address,
            address_line1_address,
            address_line2_address,
            address_line3_address,
            postal_code_address,
        ) = get_geo_location(data_frame, error_tracker, i)

        address_issue = ""
        if len(postal_code_address) == 0:
            address_issue += "Postal code,"
        if len(town_address) == 0:
            address_issue += "Town,"
        if len(address_line1_address) == 0:
            address_issue += "Address line 1,"
        if len(address_line2_address) == 0:
            address_issue += "Address line 2,"
        if len(address_line3_address) == 0:
            address_issue += "Address line 3"
        if len(address_issue) > 0:
            error_tracker.append(
                error_messages_object_formatter(
                    [STATION_ID, "Error"],
                    [
                        f"{data_frame['Station ID'][i]} (Sites Tab)",
                        f"Failed to fetch {address_issue}\
                            through coordinates.",
                    ],
                )
            )

    else:
        address_line1_address = data_frame[ADDRESS_LINE_1][i]
        address_line2_address = data_frame[ADDRESS_LINE_2][i]
        address_line3_address = data_frame[ADDRESS_LINE_3][i]
        town_address = data_frame[ADDRESS_LINE_2][i]
        postal_code_address = str(data_frame["Postcode"][i])
    postal_code_address = remove_extra_spaces(postal_code_address)
    town_address = remove_extra_spaces(town_address)
    address_line1_address = remove_extra_spaces(address_line1_address)
    address_line2_address = remove_extra_spaces(address_line2_address)
    address_line3_address = remove_extra_spaces(address_line3_address)

    return [
        postal_code_address,
        town_address,
        address_line1_address,
        address_line2_address,
        address_line3_address,
        error_tracker,
    ]


# # This functionnis used to handle the creation of station
# def create_station(request, station_create, postdata_from_front_end,location_data,back_office_name):
#     """add station view"""
#     # Insertion of Working hours details of station.
#     # Insertion in database
#     response_op = None
#     try:
#         insert_station_working_hours_entry(
#             postdata_from_front_end, request.user, station_create
#         )
#     except (DataError, DatabaseError) as error:
#         print(f'While inserting station working hours error occured as-> {str(error)}')
#         response_op = {
#             "status": False,
#             # "message": str(error),
#             "message": "Error while inserting station working hours",
#             "url": reverse("station_list"),
#         }

#     # working hour details insertion logic end
#     try:
#         insert_station_connector_data(
#             postdata_from_front_end, request.user, station_create,location_data,back_office_name
#         )
#     except (DataError, DatabaseError) as error:
#         print(f'While inserting station connector data error occured as -> {str(error)}')
#         response_op = {
#             "status": False,
#             # "message": str(error),
#             "message": "Error while inserting station connector data",
#             "url": reverse("station_list"),
#         }

#     for image in postdata_from_front_end.images:
#         image_data_stations = image_converter(image)
#         if not (
#             image_data_stations[2] > 700
#             or image_data_stations[3] > 1400
#             or image_data_stations[2] < 400
#             or image_data_stations[3] < 700
#         ):
#             response_op = {
#                 "status": False,
#                 "message": "Image with improper size is provided.",
#                 "url": reverse("station_list"),
#             }
#         image = optimize_image(
#             image_data_stations[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
#             str(station_create.station_id)
#             + randon_string_generator()
#             + "."
#             + image_data_stations[1],
#             STATION_INFO_IMAGE,
#         )
#         StationImages.objects.create(
#             station_id=station_create,
#             image=image,
#             image_width=image_data_stations[2],
#             image_height=image_data_stations[3],
#             created_date=timezone.localtime(timezone.now()),
#             updated_by=request.user.full_name,
#         )

#     # inserting station services
#     insert_station_services_data(
#         postdata_from_front_end, request.user, station_create
#     )

#     # inserting valeting data
#     try:
#         insert_valeting_terminals_data(
#             postdata_from_front_end, request.user, station_create
#         )
#     except (DataError, DatabaseError) as error:
#         print(f'While inserting valeting terminals data error occured as -> {str(error)}')
#         response_op = {
#             "status": False,
#             # "message": str(error),
#             "message": "Error occured while inserting valeting terminals data",
#             "url": reverse("station_list"),
#         }

#     # inserting valeting machines data
#     try:
#         insert_valeting_machines_data(
#             postdata_from_front_end, request.user, station_create
#         )
#     except (DataError, DatabaseError) as error:
#         print(f'While inserting valeting machines data error occurred as -> {str(error)}')
#         response_op = {
#             "status": False,
#             "message": "Error occurred while inserting valeting machines data",
#             "url": reverse("station_list"),
#         }
#     return response_op

from django.db import transaction, DatabaseError, DataError
from sharedServices.constants import ConstantMessage as CM

# def create_station(postdata, user, station_obj, location_data, back_office_name):
#     """
#     Optimized version: batch DB operations, avoid repeated queries
#     Returns: dict with status and message
#     """
#     response = None
#     try:
#         with transaction.atomic():
#             # 1. Working hours insertion
#             insert_station_working_hours_entry(postdata, user, station_obj)

#             # 2. Connector data insertion
#             insert_station_connector_data(postdata, user, station_obj, location_data, back_office_name)

#             # 3. Images processing
#             image_objects = []
#             for image in getattr(postdata, 'images', []):
#                 img_data = image_converter(image)
#                 w, h = img_data[2], img_data[3]
#                 if not (400 <= w <= 700 and 700 <= h <= 1400):
#                     raise ValueError("Image with improper size is provided")
#                 optimized_img = optimize_image(
#                     img_data[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
#                     f"{station_obj.station_id}{randon_string_generator()}.{img_data[1]}",
#                     STATION_INFO_IMAGE
#                 )
#                 image_objects.append(
#                     StationImages(
#                         station_id=station_obj,
#                         image=optimized_img,
#                         image_width=w,
#                         image_height=h,
#                         created_date=timezone.localtime(timezone.now()),
#                         updated_by=user.full_name
#                     )
#                 )
#             # Bulk create images
#             if image_objects:
#                 StationImages.objects.bulk_create(image_objects)

#             # 4. Insert services
#             insert_station_services_data(postdata, user, station_obj)

#             # 5. Valeting terminals & machines
#             insert_valeting_terminals_data(postdata, user, station_obj)
#             insert_valeting_machines_data(postdata, user, station_obj)

#     except (DataError, DatabaseError, ValueError) as e:
#         return {"status": False, "message": str(e)}

#     return {"status": True, "message": CM.STATION_CREATED_SUCCESSFULLY}

def create_station(postdata, user, station_obj, location_data, back_office_name):
    try:
        with transaction.atomic():
            insert_station_working_hours_entry(postdata, user, station_obj)
            insert_station_connector_data(postdata, user, station_obj, location_data, back_office_name)
            print("true1")
            image_objects = []
            for image in getattr(postdata, 'station_images', []):
                img_data = image_converter(image)
                optimized_img = optimize_image(
                    img_data[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
                    f"{station_obj.station_id}{randon_string_generator()}.{img_data[1]}",
                    STATION_INFO_IMAGE
                )
                print("true2-->",img_data, "and optimize-->",optimized_img)
                image_objects.append(
                    StationImages(
                        station_id=station_obj,
                        image=optimized_img,
                        image_width=img_data[2],
                        image_height=img_data[3],
                        created_date=timezone.localtime(timezone.now()),
                        updated_by=user.full_name
                    )
                )
            if image_objects:
                StationImages.objects.bulk_create(image_objects)
            insert_station_services_data(postdata, user, station_obj)
            insert_valeting_terminals_data(postdata, user, station_obj)
            insert_valeting_machines_data(postdata, user, station_obj)

    except (DataError, DatabaseError, ValueError) as e:
        return {"status": False, "message": str(e)}

    return {"status": True, "message": CM.STATION_CREATED_SUCCESSFULLY}


def check_is_ev_status(postdata_from_front_end):
    """Check if the station is EV based on type and chargepoints"""
    charge_points = filter(
        lambda charge_point: not charge_point.get("deleted", False),
        postdata_from_front_end.get("chargepoints", [])
    )

    return bool(
        (
            postdata_from_front_end.get("station_type") == "Non MFG"
            or postdata_from_front_end.get("station_type") in IS_EV_KEYS
        )
        and len(list(charge_points)) > 0
    )



def update_database_stations(
    request,
    station_pk,
    station,
    amenities_services_helper,
    retails_services_helper,
    food_to_go_services_helper,
    query_params_str,
):
    """update database stations"""
    # Decoding json data from frontend.
    old_data = audit_data_formatter(SITES_CONST, station_pk)
    postdata_from_front_end = json.loads(
        request.POST["getdata"], object_hook=lambda d: SimpleNamespace(**d)
    )
    if (
        postdata_from_front_end.station_id
        != postdata_from_front_end.prev_station_id
    ):
        station_exists_helper = Stations.objects.filter(
            station_id=postdata_from_front_end.station_id
        )
        if station_exists_helper.first():
            response_op = {
                "status": False,
                "message": "Station with this id already exists",
                "url": reverse("station_list"),
            }
            return JsonResponse(response_op)
    # To Delete previous images which is removed from update
    for url in postdata_from_front_end.removeImages:
        image_split = url.split(AZURE_BLOB_STORAGE_URL)
        if len(image_split) > 1:
            station_image = StationImages.objects.filter(
                station_id=station_pk, image=image_split[1]
            )
            dl_id = station_image.first().id
            station_image.first().image.delete()
            StationImages.objects.filter(id=dl_id).delete()
    is_mfg_helper = NO
    if postdata_from_front_end.station_type in IS_MFG_KEYS:
        is_mfg_helper = YES
    # Station insert operation
    is_ev_helper = NO
    if check_is_ev_status(postdata_from_front_end):
        is_ev_helper = YES
    station_can_be_added_helper = True
    locations = []
    back_office_key =''
    if is_ev_helper == YES :#and postdata_from_front_end.brand == "EV Power":
        
        #need to update mappings from location,evse and connector to avoid same station or connector
        # being mapped to multiple locations or connectors in same cpo
        
        back_office_data = {item.back_office: item.location_id for item in postdata_from_front_end.backoffice}
        back_office_key = list(back_office_data.keys())[0]
        if station_pk is not None:
            for back_office,location_id in back_office_data.items():
                if back_office != '':
                    country_code,party_id = get_back_office_data(back_office)
                    location_data = OCPILocation.objects.filter(location_id = location_id, country_code = country_code, party_id = party_id).first()
                    
                    prev_locations = OCPILocation.objects.filter(station_mapping_id = station)
                    evses = OCPIEVSE.objects.filter(location_id__in = prev_locations)
                    ocpi_connector = OCPIConnector.objects.filter(evse_id__in = evses)
                    
                    evses.update(chargepoint_mapping_id = None)
                    ocpi_connector.update(connector_mapping_id = None)
                    prev_locations.update(
                        station_mapping_id = None
                    )
                    location_data.station_mapping_id = station
                    location_data.save()
                    locations.append(location_data)
        station_have_cp = ChargePoint.objects.filter(
            deleted=NO, station_id_id=station_pk
        )
        if station_have_cp.first() is None:
            if len(postdata_from_front_end.chargepoints) == 0:
                station_can_be_added_helper = False
    if not station_can_be_added_helper:
        response_op = {
            "status": False,
            "message": NO_CHARGEPOINTS_PROVIDED_MESSAGE,
            "url": reverse("station_list"),
        }
        return JsonResponse(response_op)
        # The following condition is used to differentiate
        # station according to station owner.
    update_single_station_func(
        postdata_from_front_end,
        is_mfg_helper,
        is_ev_helper,
        request.user,
        station_pk,
    )
    # update query on station dependencies
    update_station_working_hours_entry(
        postdata_from_front_end, request.user, station_pk
    )
    # update station devices function
    update_station_connector_data(
        postdata_from_front_end, request.user, station, locations,back_office_key
    )

    for image in postdata_from_front_end.images:
        split = image.split(AZURE_BLOB_STORAGE_URL)
        if len(split) < 2:
            image_data_stations = image_converter(image)
            if not (
                image_data_stations[2] > 700
                or image_data_stations[3] > 1400
                or image_data_stations[2] < 400
                or image_data_stations[3] < 700
            ):
                response_op = {
                    "status": False,
                    "message": "Image with improper size is provided.",
                    "url": reverse("station_list"),
                }
                return JsonResponse(response_op)
            image = optimize_image(
                image_data_stations[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
                str(station.station_id)
                + randon_string_generator()
                + "."
                + image_data_stations[1],
                STATION_INFO_IMAGE,
            )
            StationImages.objects.create(
                station_id=station,
                image=image,
                image_width=image_data_stations[2],
                image_height=image_data_stations[3],
                created_date=timezone.localtime(timezone.now()),
                updated_by=request.user.full_name,
            )
    # Services updation logic
    audit_data_generated = update_station_services_data(
        postdata_from_front_end,
        request.user,
        station_pk,
        station,
        amenities_services_helper,
        retails_services_helper,
        food_to_go_services_helper,
    )
    update_station_valeting_data(
        postdata_from_front_end, request.user, station
    )
    update_station_valeting_machines(
        postdata_from_front_end, request.user, station
    )
    new_data = audit_data_formatter(SITES_CONST, station_pk)
    if old_data != new_data:
        station_audit_data_id = add_audit_data(
            request.user,
            f"{station.station_id}, {station.station_name}",
            f"{SITES_CONST}-{station_pk}",
            AUDIT_UPDATE_CONSTANT,
            SITES_CONST,
            new_data,
            old_data,
        )
        add_references_to_audit_data(
            audit_data_generated, station_audit_data_id
        )

    response_op = {
        "status": 1,
        "message": "ok",
        "url": reverse("station_list"),
        "query_params_str": query_params_str,
    }
    remove_stations_cached_data()
    return JsonResponse(response_op)
