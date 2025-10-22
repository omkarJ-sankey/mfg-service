"""DB operators (create, update)"""

# Date - 23/11/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused db operations
#                       such as create and update.
#   Name            - Db operators
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 23/07/2025

# imports required to create views
from django.utils import timezone
from django.db import IntegrityError, transaction
import json
import logging
import traceback
from django.db.models.query import QuerySet
from django.db.models import Q


# pylint:disable=import-error
from sharedServices.model_files.valeting_models import ValetingMachine
from sharedServices.model_files.station_models import (
    ChargePoint,
    ServiceConfiguration,
    StationConnector,
    StationServices,
    StationWorkingHours,
    Stations,
    ValetingTerminals,
)

from sharedServices.model_files.promotions_models import PromotionsAvailableOn
from sharedServices.model_files.loyalty_models import LoyaltyAvailableOn
from sharedServices.model_files.bulk_models import BulkUploadProgress
from sharedServices.model_files.ocpi_locations_models import (OCPIConnector,OCPIEVSE,OCPILocation)

from sharedServices.ocpi_common_functions import (get_back_office_data,get_location_backoffice)


from sharedServices.common import (
    string_to_array_converter,
    array_to_string_converter,
)
from sharedServices.common_audit_trail_functions import (
    add_audit_data,
    audit_data_formatter,
)
from sharedServices.constants import (
    FOOD_TO_GO,
    YES,
    NO,
    HOURS_24,
    IS_EV_KEYS,
    PROMOTIONS_CONST,
    LOYALTY_CONST,
    AUDIT_UPDATE_CONSTANT,
    WORLDLINE_PAYMENT_TERMINAL,
    PAYTER_PAYMENT_TERMINAL,
)
from .app_level_constants import NON_EV_STATION_TYPE

logger = logging.getLogger(__name__)


# This function returns service from configuration
def return_service_instance_from_configuration(service_id):
    """returns service instance from service id"""
    service = ServiceConfiguration.objects.get(id=service_id)
    return service


def create_station_func(stations_array):
    """bulk create function for Stations"""
    station_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="stations",
    )
    length_of_stations_array = len(stations_array[0])
    stations = Stations.objects.bulk_create(stations_array[0])

    for station in stations:
        # if station.is_ev == YES:
        station_data = Stations.objects.filter(station_id = station.station_id).first()
        location = OCPILocation.objects.filter(
            ~Q(id = stations_array[1][0][station.station_id]),
            station_mapping_id = station_data
        )
        evses = OCPIEVSE.objects.filter(location_id__in = location)
        ocpi_connector = OCPIConnector.objects.filter(evse_id__in = evses)
        
        location.update(
            station_mapping_id = None
        )
        evses.update(chargepoint_mapping_id = None)
        ocpi_connector.update(connector_mapping_id = None)

        OCPILocation.objects.filter(
            id = stations_array[1][0][station.station_id]
        ).update(
            station_mapping_id = station_data
        )

    current_count = (
        int(station_bulk_upload_progress.first().uploaded_rows_count)
        + length_of_stations_array
    )
    station_bulk_upload_progress.update(uploaded_rows_count=current_count)


def update_station_func(stations_array):
    """bulk update function for stations"""
    station_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="stations",
    )
    length_of_stations_array = len(stations_array)
    with transaction.atomic():
        for station in stations_array:
            Stations.objects.filter(station_id=station["station_id"]).update(
                deleted=NO,
                station_name=station["station_name"],
                station_address1=station["station_address1"],
                station_address2=station["station_address2"],
                station_address3=station["station_address3"],
                post_code=station["post_code"],
                town=station["town"],
                brand=station["brand"],
                owner=station["owner"],
                latitude=station["latitude"],
                longitude=station["longitude"],
                phone=station["phone"],
                status=station["status"],
                station_type=station["station_type"],
                is_mfg=station["is_mfg"],
                is_ev=station["is_ev"],
                updated_date=station["created_date"],
                updated_by=station["updated_by"],
                site_id=station["site_id"],
                valeting=station["valeting"],
                payment_terminal=station["payment_terminal"],
                receipt_hero_site_name=station["receipt_hero_site_name"],
                valeting_site_id=station["valeting_site_id"],
                ampeco_site_id=station["ampeco_site_id"],
                ampeco_site_title=station["ampeco_site_title"],
                parking_details=station["parking_details"],
            )
    current_count = (
        int(station_bulk_upload_progress.first().uploaded_rows_count)
        + length_of_stations_array
    )
    station_bulk_upload_progress.update(uploaded_rows_count=current_count)


# def update_location_mapping_func(location_mapping_obj):
#     """bulk update function for stations"""
#     station_bulk_upload_progress = BulkUploadProgress.objects.filter(
#         uploaded_for="stations",
#     )
#     stations_array = list(location_mapping_obj.keys())
#     length_of_stations_array = len(stations_array)
#     with transaction.atomic():
#         for station in stations_array:
#             station_data = Stations.objects.filter(
#                 station_id = station
#             )
#             location_obj = location_mapping_obj[station_data.first().station_id]
#             if station_data.first() is not None:
#                 for key in list(location_obj.keys()):
#                     country_code,party_id = get_back_office_data(key)
#                     location = OCPILocation.objects.filter(
#                         location_id = location_obj[key],
#                         country_code = country_code,
#                         party_id = party_id
#                     ).update(station_mapping_id = station_data.first())
#             


#             if station_data.first():
#                 if station_data.first().ocpi_locations is None:
#                     
#                     station_data.update(ocpi_locations = location_mapping_obj[station])
#                     
#                 else:
#                     
#                     combined = station_data.ocpi_locations.copy()
#                     
#                     mapping_obj = combined.update(location_mapping_obj[station])
#                     # mapping_obj = station_data.ocpi_locations
#                     # for key, val in location_mapping_obj[station]:
#                     #     mapping_obj[key] = val
#                     
#                     station_data.update(ocpi_locations = mapping_obj)
#     current_count = (
#         int(station_bulk_upload_progress.first().uploaded_rows_count)
#         + length_of_stations_array
#     )
#     station_bulk_upload_progress.update(uploaded_rows_count=current_count)



def update_station_details_from_mfg_tab(stations_array):
    """bulk update functions to add/update station details"""
    station_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="stations",
    )
    length_of_stations_array = len(stations_array)
    with transaction.atomic():
        for station in stations_array:
            Stations.objects.filter(station_id=station["station_id"]).update(
                site_title=station["site_title"],
                operation_region=station["operation_region"],
                region=station["region"],
                regional_manager=station["regional_manager"],
                area=station["area"],
                area_regional_manager=station["area_regional_manager"],
                email=station["email"],
                country=station["country"],
                updated_date=station["updated_date"],
                updated_by=station["updated_by"],
            )
    current_count = (
        int(station_bulk_upload_progress.first().uploaded_rows_count)
        + length_of_stations_array
    )
    station_bulk_upload_progress.update(uploaded_rows_count=current_count)


def station_working_hours_create_query_func(station_working_hours):
    """function to add station working hours in bulk"""
    station_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="stations",
    )
    length_of_stations_array = len(station_working_hours)
    station_working_hours = [
        StationWorkingHours(
            station_id=Stations.objects.filter(
                station_id=working_hours["station_id"]
            ).first(),
            monday_friday=working_hours["monday_friday"],
            saturday=working_hours["saturday"],
            sunday=working_hours["sunday"],
            updated_date=working_hours["updated_date"],
            updated_by=working_hours["updated_by"],
        )
        for working_hours in station_working_hours
    ]
    StationWorkingHours.objects.bulk_create(station_working_hours)
    current_count = (
        int(station_bulk_upload_progress.first().uploaded_rows_count)
        + length_of_stations_array
    )
    station_bulk_upload_progress.update(uploaded_rows_count=current_count)


def station_working_hours_update_query_func(station_working_hours):
    """function to update station working hours in bulk"""
    station_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="stations",
    )
    length_of_stations_array = len(station_working_hours)
    with transaction.atomic():
        for station in station_working_hours:
            StationWorkingHours.objects.filter(id=station["id"]).update(
                monday_friday=station["monday_friday"],
                saturday=station["saturday"],
                sunday=station["sunday"],
                updated_date=station["updated_date"],
                updated_by=station["updated_by"],
            )
    current_count = (
        int(station_bulk_upload_progress.first().uploaded_rows_count)
        + length_of_stations_array
    )
    station_bulk_upload_progress.update(uploaded_rows_count=current_count)


def return_station_service_create_object(service_from_configuration, service):
    """this function returns station service object for creation"""
    return StationServices(
        service_id=service_from_configuration,
        station_id=Stations.objects.filter(
            station_id=service["station_id"]
        ).first(),
        service_name=service_from_configuration.service_type,
        created_date=timezone.localtime(timezone.now()),
        updated_by=service["updated_by"],
    )


def add_station_services(services):
    """function to add station services in bulk"""
    service_configurations = ServiceConfiguration.objects.filter()
    station_services_queryset = StationServices.objects.filter()
    add_services_list = []
    update_services_list = []
    for service in services:
        services_list = list(set(service["services"]))
        for shop in services_list:
            service_from_configuration = service_configurations.filter(
                service_name__exact=shop.strip(),
                service_type=service["service_type"],
            )
            if len(service_from_configuration) > 0:
                previous_service = station_services_queryset.filter(
                    station_id__station_id=service["station_id"],
                    service_id=service_from_configuration.first(),
                )
                if previous_service.first():
                    if previous_service.first().deleted == YES:
                        update_services_list.append(
                            {"id": previous_service.first().id, "deleted": NO}
                        )
                else:
                    add_services_list.append(
                        return_station_service_create_object(
                            service_from_configuration.first(), service
                        )
                    )
        # Removing services from stations
        station_food_to_go_shops = station_services_queryset.filter(
            station_id__station_id=service["station_id"],
            service_name=service["service_type"],
        )
        for station_service in station_food_to_go_shops:
            if station_service.service_id:
                service_from_configuration = service_configurations.filter(
                    id=station_service.service_id.id, service_type=FOOD_TO_GO
                )
                if service_from_configuration.first():
                    if (
                        not service_from_configuration.first().service_name
                        in services_list
                    ):
                        update_services_list.append(
                            {"id": station_service.id, "deleted": YES}
                        )
    station_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="stations",
    )
    length_of_services = len(services)
    # add services
    StationServices.objects.bulk_create(add_services_list)
    # update srvices
    with transaction.atomic():
        for service_to_be_updated in update_services_list:
            StationServices.objects.filter(
                id=service_to_be_updated["id"]
            ).update(deleted=service_to_be_updated["deleted"])
    current_count = (
        int(station_bulk_upload_progress.first().uploaded_rows_count)
        + length_of_services
    )
    station_bulk_upload_progress.update(uploaded_rows_count=current_count)


def add_update_valeting_terminals(valeting_terminals):
    station_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="stations",
    )
    length_of_valeting_terminals = len(valeting_terminals)
    stations = Stations.objects.filter()
    create_valeting_array = []
    added_valeting_terminal = []
    with transaction.atomic():
        for valeting_terminal in valeting_terminals:
            station_bulk_upload_progress = BulkUploadProgress.objects.filter(
                uploaded_for="stations",
            )
            station = None
            station_exists = stations.filter(
                station_id=valeting_terminal["station_id"], valeting="Yes"
            )
            if station_exists.first():
                station = station_exists.first()
            if station:
                station_amenities_ids = StationServices.objects.filter(
                    station_id=station,
                    service_id__service_name__in=valeting_terminal[
                        "amenities"
                    ],
                    service_name="Amenity",
                ).values_list("service_id_id", flat=True)
                if station_amenities_ids:
                    already_added_valeting_terminal = (
                        ValetingTerminals.objects.filter(
                            station_id=station,
                            payter_serial_number=valeting_terminal[
                                "payter_serial_number"
                            ],
                        )
                    )
                    if len(already_added_valeting_terminal) > 0:
                        already_added_valeting_terminal.update(
                            payter_serial_number=valeting_terminal[
                                "payter_serial_number"
                            ],
                            status=valeting_terminal["status"],
                            deleted=NO,
                            amenities=array_to_string_converter(
                                list(station_amenities_ids)
                            ),
                            updated_date=valeting_terminal[
                                "created_updated_date"
                            ],
                            updated_by=valeting_terminal["updated_by"],
                        )
                    else:
                        if (
                            valeting_terminal["payter_serial_number"]
                            not in added_valeting_terminal
                        ):
                            added_valeting_terminal.append(
                                valeting_terminal["payter_serial_number"]
                            )
                            create_valeting_array.append(
                                ValetingTerminals(
                                    station_id=station,
                                    payter_serial_number=valeting_terminal[
                                        "payter_serial_number"
                                    ],
                                    status=valeting_terminal["status"],
                                    amenities=array_to_string_converter(
                                        list(station_amenities_ids)
                                    ),
                                    created_date=valeting_terminal[
                                        "created_updated_date"
                                    ],
                                    updated_by=valeting_terminal["updated_by"],
                                )
                            )
    ValetingTerminals.objects.bulk_create(create_valeting_array)
    current_count = (
        int(station_bulk_upload_progress.first().uploaded_rows_count)
        + length_of_valeting_terminals
    )
    station_bulk_upload_progress.update(uploaded_rows_count=current_count)


def add_station_chargepoints(chargepoints):
    """function to add Charge points in bulks"""
    station_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="stations",
    )
    length_of_chargepoints = len(chargepoints)
    stations = Stations.objects.filter()
    create_chargepoint_array = []
    added_chrgepoints = []
    with transaction.atomic():
        for chargepoint in chargepoints:
            station_bulk_upload_progress = BulkUploadProgress.objects.filter(
                uploaded_for="stations",
            )
            station = None
            station_exists = stations.filter(
                station_id=chargepoint["station_id"]
            )
            if station_exists.first():
                station = station_exists.first()
            if station:
                device_already_added = ChargePoint.objects.filter(
                    station_id=station,
                    charger_point_id=chargepoint["charger_point_id"],
                )
                if len(device_already_added) > 0:
                    device_already_added.update(
                        charger_point_name=chargepoint["charger_point_name"],
                        charger_point_status=chargepoint[
                            "charger_point_status"
                        ],
                        deleted=NO,
                        back_office=chargepoint["back_office"],
                        device_id=chargepoint["device_id"],
                        payter_terminal_id=chargepoint["payter_terminal_id"],
                        ampeco_charge_point_id=chargepoint.get("ampeco_charge_point_id", ""),
                        ampeco_charge_point_name=chargepoint.get("ampeco_charge_point_name", ""),
                        worldline_terminal_id=chargepoint["worldline_terminal_id"],
                        updated_date=chargepoint["created_date"],
                        updated_by=chargepoint["updated_by"],
                    )
                else:
                    if (
                        chargepoint["charger_point_id"]
                        not in added_chrgepoints
                    ):
                        added_chrgepoints.append(
                            chargepoint["charger_point_id"]
                        )
                        create_chargepoint_array.append(
                            ChargePoint(
                                station_id=station,
                                charger_point_id=chargepoint[
                                    "charger_point_id"
                                ],
                                charger_point_name=chargepoint[
                                    "charger_point_name"
                                ],
                                charger_point_status=chargepoint[
                                    "charger_point_status"
                                ],
                                back_office=chargepoint["back_office"],
                                device_id=chargepoint["device_id"],
                                payter_terminal_id=chargepoint[
                                    "payter_terminal_id"
                                ],
                                ampeco_charge_point_id=chargepoint.get("ampeco_charge_point_id", ""),
                                ampeco_charge_point_name=chargepoint.get("ampeco_charge_point_name", ""),
                                worldline_terminal_id=chargepoint[
                                    "worldline_terminal_id"
                                ],
                                updated_date=chargepoint["created_date"],
                                updated_by=chargepoint["updated_by"],
                            )
                        )
    ChargePoint.objects.bulk_create(create_chargepoint_array)
    current_count = (
        int(station_bulk_upload_progress.first().uploaded_rows_count)
        + length_of_chargepoints
    )
    station_bulk_upload_progress.update(uploaded_rows_count=current_count)


def add_station_connectors(connectors):
    """function to add connectors in bulk"""
    station_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="stations",
    )
    length_of_connectors = len(connectors)
    stations = Stations.objects.filter()
    locations = OCPILocation.objects.filter()
    create_connectors_array = []
    ocpi_connectors_array = []
    with transaction.atomic():
        for connector in connectors:
            station_bulk_upload_progress = BulkUploadProgress.objects.filter(
                uploaded_for="stations",
            )
            station = None
            location = None
            back_office = None
            station_exists = stations.filter(
                station_id=connector["station_id"]
            )
            if station_exists.first():
                station = station_exists.first()
                location = locations.filter(station_mapping_id =  station_exists.first()).first()
                back_office = get_location_backoffice(location)
                connector_already_added = StationConnector.objects.filter(
                    station_id=station,
                    charge_point_id__charger_point_id=connector[
                        "charger_point_id"
                    ],
                    connector_id=connector["connector_id"],
                )
                
                if len(connector_already_added) > 0:
                    connector_already_added.update(
                        connector_id=connector["connector_id"],
                        connector_name=connector["connector_name"],
                        connector_type=connector["connector_type"],
                        plug_type_name=connector["plug_type_name"],
                        status="Active",
                        deleted=NO,
                        max_charge_rate=connector["max_charge_rate"],
                        connector_sorting_order=connector[
                            "connector_sorting_order"
                        ],
                        tariff_amount=connector["tariff_amount"],
                        tariff_currency=connector["tariff_currency"],
                        updated_date=connector["created_date"],
                        updated_by=connector["updated_by"],
                        back_office = back_office
                    )
                    charge_point = ChargePoint.objects.filter(
                        charger_point_id=connector["charger_point_id"]
                    ).first()
                    if location:
                        evse = OCPIEVSE.objects.filter(
                            location_id = location,
                            uid = connector["evse_uid"]
                        )
                        evse.update(
                            chargepoint_mapping_id = charge_point,
                        )

                        ocpi_connector = OCPIConnector.objects.filter(
                            connector_id = connector["ocpi_connector_id"],
                            evse_id = evse.first()
                        )
                        ocpi_connector.update(connector_mapping_id = connector_already_added.first())

                        OCPIConnector.objects.filter(
                            ~Q(id = ocpi_connector.first().id),
                            connector_mapping_id = connector_already_added.first()
                        ).update(connector_mapping_id = None)

                else:
                    
                    create_connectors_array.append(
                        StationConnector(
                            station_id=station,
                            charge_point_id=ChargePoint.objects.filter(
                                charger_point_id=connector["charger_point_id"]
                            ).first(),
                            connector_id=connector["connector_id"],
                            connector_name=connector["connector_name"],
                            connector_type=connector["connector_type"],
                            plug_type_name=connector["plug_type_name"],
                            status="Active",
                            max_charge_rate=connector["max_charge_rate"],
                            connector_sorting_order=connector[
                                "connector_sorting_order"
                            ],
                            tariff_amount=connector["tariff_amount"],
                            tariff_currency=connector["tariff_currency"],
                            updated_date=connector["created_date"],
                            updated_by=connector["updated_by"],
                            back_office = back_office
                        )
                    )                    

                    ocpi_connector = OCPIConnector.objects.filter(
                        evse_id__location_id = location,
                        connector_id = connector["ocpi_connector_id"]
                    )
                    if ocpi_connector.first():
                        
                        connector_obj = {}
                        connector_obj["chargepoint_id"] = ChargePoint.objects.filter(
                                    charger_point_id=connector["charger_point_id"]
                                ).first().id

                        connector_obj["connector_id"] = connector["connector_id"]
                        connector_obj["ocpi_connector_id"] = ocpi_connector.first().id
                        ocpi_connectors_array.append(connector_obj)

                if station.is_ev == NO and station.station_type in IS_EV_KEYS:
                    station_exists.update(is_ev=YES)
    station_connectors = StationConnector.objects.bulk_create(create_connectors_array)

    for station_connector in station_connectors:
        for obj in ocpi_connectors_array:
            if (station_connector.charge_point_id == obj["chargepoint_id"] 
                and station_connector.connector_id == connector_obj["connector_id"]):
                
                OCPIConnector.objects.filter(
                    id = obj["ocpi_connector_id"]
                ).update(connector_mapping_id = station_connector)
                
                OCPIConnector.objects.filter(
                    ~Q(id = obj["ocpi_connector_id"]),
                    connector_mapping_id = station_connector
                ).update(connector_mapping_id = None)
                

    
    current_count = (
        int(station_bulk_upload_progress.first().uploaded_rows_count)
        + length_of_connectors
    )
    for connector_data in connectors:
        connector = StationConnector.objects.filter(
            station_id = station, 
            connector_id = connector_data["connector_id"]
        )
        
        connector_obj = connector.first()
        if connector.first() is not None:
            country_code,party_id = get_back_office_data(connector.first().back_office)
            if country_code is not None and party_id is not None:
                evse = OCPIEVSE.objects.filter(
                    location_id__country_code = country_code,
                    location_id__party_id = party_id,
                    uid = connector_data["evse_uid"]
                )
                evse.update(chargepoint_mapping_id = connector.first().charge_point_id)
                
                OCPIConnector.objects.filter(
                    evse_id = evse.first(),
                    connector_id = int(connector_data["ocpi_connector_id"])               
                ).update(
                    connector_mapping_id = connector.first()
                )
                
    station_bulk_upload_progress.update(uploaded_rows_count=current_count)


def create_single_station_func(data, is_mfg, is_ev, user, back_office_data):
    """this functions inserts stations in db"""

    station_create = None
    if data.station_type_is_mfg:
        site_details = data.stationTypeSiteData
        try:
            station_create = Stations.objects.create(
                station_id=data.station_id,
                station_name=data.station_name,
                station_address1=data.address_line1,
                station_address2=data.address_line2,
                station_address3=data.address_line3,
                town=data.town,
                post_code=data.postal_code,
                country=data.country,
                brand=data.brand,
                owner=data.owner,
                latitude=data.latitude,
                longitude=data.longitude,
                email=data.email,
                phone=data.phone,
                status=data.status,
                overstay_fee=data.overstay_fee,
                station_type=data.station_type,
                site_title=site_details.site_title,
                operation_region=site_details.operation_region,
                region=site_details.region,
                regional_manager=site_details.regional_manager,
                area=site_details.area,
                area_regional_manager=site_details.area_regional_manager,
                is_mfg=is_mfg,
                is_ev=is_ev,
                created_date=timezone.localtime(timezone.now()),
                updated_by=user.full_name,
                valeting=data.valeting,
                site_id=(
                    None
                    if data.station_type in NON_EV_STATION_TYPE
                    else data.site_id
                ),
                ocpi_locations = (None if data.station_type in NON_EV_STATION_TYPE
                    else back_office_data
                ),
                payment_terminal=array_to_string_converter(
                    data.payment_terminal if data.payment_terminal else []
                ),
                receipt_hero_site_name=(
                    data.rh_site_name
                    if data.rh_site_name
                    and WORLDLINE_PAYMENT_TERMINAL in data.payment_terminal
                    else None
                ),
                valeting_site_id=data.valeting_site_id,
                ampeco_site_id=data.ampeco_site_id,
                ampeco_site_title=data.ampeco_site_title,
                parking_details=data.parking_details,
            )
        except Exception as e:
            print(f"Failed to create station: {e}")
    else:
        station_create = Stations.objects.create(
            station_id=data.station_id,
            station_name=data.station_name,
            station_address1=data.address_line1,
            station_address2=data.address_line2,
            station_address3=data.address_line3,
            town=data.town,
            post_code=data.postal_code,
            country=data.country,
            brand=data.brand,
            owner=data.owner,
            latitude=data.latitude,
            longitude=data.longitude,
            email=data.email,
            phone=data.phone,
            status=data.status,
            overstay_fee=data.overstay_fee,
            station_type=data.station_type,
            is_mfg=is_mfg,
            is_ev=is_ev,
            created_date=timezone.localtime(timezone.now()),
            updated_by=user.full_name,
            valeting=data.valeting,
            site_id=(
                None
                if data.station_type in NON_EV_STATION_TYPE
                else data.site_id
            ),
            payment_terminal=array_to_string_converter(
                data.payment_terminal if data.payment_terminal else []
            ),
            receipt_hero_site_name=(
                data.rh_site_name
                if data.rh_site_name
                and WORLDLINE_PAYMENT_TERMINAL in data.payment_terminal
                else None
            ),
            valeting_site_id=data.valeting_site_id,
            ampeco_site_id=data.ampeco_site_id,
            ampeco_site_title=data.ampeco_site_title,
            parking_details=data.parking_details,
        )
    locations = []
    try:
        if back_office_data is not None and is_ev == YES:
            for key,value in back_office_data.items():
                country_code,party_id = get_back_office_data(key)
                OCPILocation.objects.filter(
                    country_code = country_code, party_id = party_id, location_id = value
                ).update(
                    station_mapping_id = station_create
                )
                location = OCPILocation.objects.filter(
                    country_code = country_code, party_id = party_id, location_id = value
                )
                evses = OCPIEVSE.objects.filter(location_id__in = location)
                ocpi_connector = OCPIConnector.objects.filter(evse_id__in = evses)
                evses.update(chargepoint_mapping_id = None)
                ocpi_connector.update(connector_mapping_id = None)
                locations.append(location.first().id)
        return station_create, locations
    except Exception as e :
        traceback.print_exc()
    


def update_single_station_func(data, is_mfg, is_ev, user, station_pk_operator):
    """this functions updates stations in db"""
    # The following condition is used to differentiate station
    #   according to station owner.
    
    if data.station_type_is_mfg:
        site_details = data.stationTypeSiteData
        # Update query on station database.
        result = Stations.objects.filter(id=station_pk_operator).update(
            station_id=data.station_id,
            station_name=data.station_name,
            station_address1=data.address_line1,
            station_address2=data.address_line2,
            station_address3=data.address_line3,
            town=data.town,
            post_code=data.postal_code,
            country=data.country,
            brand=data.brand,
            owner=data.owner,
            latitude=data.latitude,
            longitude=data.longitude,
            email=data.email,
            phone=data.phone,
            status=data.status,
            overstay_fee=data.overstay_fee,
            station_type=data.station_type,
            site_title=site_details.site_title,
            operation_region=site_details.operation_region,
            region=site_details.region,
            regional_manager=site_details.regional_manager,
            area=site_details.area,
            area_regional_manager=site_details.area_regional_manager,
            is_mfg=is_mfg,
            is_ev=is_ev,
            updated_date=timezone.localtime(timezone.now()),
            updated_by=user.full_name,
            valeting=data.valeting,
            site_id=(
                None
                if data.station_type in NON_EV_STATION_TYPE
                else data.site_id
            ),
            payment_terminal=array_to_string_converter(
                data.payment_terminal if data.payment_terminal else []
            ),
            receipt_hero_site_name=(
                data.rh_site_name
                if data.rh_site_name
                and WORLDLINE_PAYMENT_TERMINAL in data.payment_terminal
                else None
            ),
            valeting_site_id=data.valeting_site_id,
            ampeco_site_id=getattr(data, 'ampeco_site_id', ''),
            ampeco_site_title=getattr(data, 'ampeco_site_title', ''),
            parking_details=data.parking_details,
            # ocpi_locations = (None if data.station_type in NON_EV_STATION_TYPE
            #     else data["back_office_data"]
            # ),
        )
    else:
        result = Stations.objects.filter(id=station_pk_operator).update(
            station_id=data.station_id,
            station_name=data.station_name,
            station_address1=data.address_line1,
            station_address2=data.address_line2,
            station_address3=data.address_line3,
            town=data.town,
            post_code=data.postal_code,
            country=data.country,
            brand=data.brand,
            owner=data.owner,
            latitude=data.latitude,
            longitude=data.longitude,
            email=data.email,
            phone=data.phone,
            status=data.status,
            overstay_fee=data.overstay_fee,
            station_type=data.station_type,
            is_mfg=is_mfg,
            is_ev=is_ev,
            updated_date=timezone.localtime(timezone.now()),
            updated_by=user.full_name,
            site_id=(
                None
                if data.station_type in NON_EV_STATION_TYPE
                else data.site_id
            ),
            payment_terminal=array_to_string_converter(
                data.payment_terminal if data.payment_terminal else []
            ),
            receipt_hero_site_name=(
                data.rh_site_name
                if data.rh_site_name
                and WORLDLINE_PAYMENT_TERMINAL in data.payment_terminal
                else None
            ),
            valeting_site_id=data.valeting_site_id,
            ampeco_site_id=getattr(data, 'ampeco_site_id', ''),
            ampeco_site_title=getattr(data, 'ampeco_site_title', ''),
            parking_details=data.parking_details,
            # ocpi_locations = (None if data.station_type in NON_EV_STATION_TYPE
            #     else data["back_office_data"]
            # ),
        )


def working_hours_handler(start_time, end_time):
    """working hours handler function"""
    status = ""
    if (
        len(str(start_time)) > 0
        and str(start_time) != "null "
        and len(str(end_time)) > 0
        and str(end_time) != " null"
    ):
        status = f"{start_time}-{end_time}"
    elif len(str(start_time)) > 0 and str(start_time) != "null ":
        status = f"{start_time}- null"
    elif len(str(end_time)) > 0 and str(end_time) != " null":
        status = f"null -{end_time}"
    else:
        status = "Closed"
    return status


def insert_station_working_hours_entry(data, user, station_create):
    """this function help to insert working hour details for station"""
    monday_friday = ""
    saturday = ""
    sunday = ""
    # Checking whether station is 24 hours open or not
    if data.working_hours.monday_friday.full_hours:
        monday_friday = HOURS_24
    else:
        monday_friday = working_hours_handler(
            data.working_hours.monday_friday.start_time,
            data.working_hours.monday_friday.end_time,
        )

    if data.working_hours.saturday.full_hours:
        saturday = HOURS_24
    else:
        saturday = working_hours_handler(
            data.working_hours.saturday.start_time,
            data.working_hours.saturday.end_time,
        )

    if data.working_hours.sunday.full_hours:
        sunday = HOURS_24
    else:
        sunday = working_hours_handler(
            data.working_hours.sunday.start_time,
            data.working_hours.sunday.end_time,
        )

    # Insertion in database
    StationWorkingHours.objects.create(
        station_id=station_create,
        monday_friday=monday_friday,
        saturday=saturday,
        sunday=sunday,
        created_date=timezone.localtime(timezone.now()),
        updated_by=user.full_name,
    )


def insert_station_connector_data(data, user, station_create,location_ids,back_office_name):
    """this function helps to insert station chargepoints"""

    # Condition to check the station is not forecourt so
    # that we can add chargepoints to the station
    try:
        evses = OCPIEVSE.objects.filter(
            location_id__in = location_ids
        )
        ocpi_connectors = OCPIConnector.objects.filter(evse_id__in = evses)
        if data.station_type != "MFG Forecourt":
            # Logic to insert chargepoints
            for chargepoint in data.chargepoints:
                if not chargepoint.deleted:
                    charge_point = ChargePoint.objects.create(
                        station_id=station_create,
                        charger_point_id=chargepoint.charge_point_id,
                        charger_point_name=chargepoint.charge_point_name,
                        charger_point_status=chargepoint.status,
                        back_office=back_office_name.upper(),
                        device_id=chargepoint.device_id,
                        payter_terminal_id=(
                            chargepoint.payter_terminal_id
                            if PAYTER_PAYMENT_TERMINAL in data.payment_terminal
                            else None
                        ),
                        created_date=timezone.localtime(timezone.now()),
                        updated_by=user.full_name,
                        ampeco_charge_point_id=chargepoint.ampeco_charge_point_id,
                        ampeco_charge_point_name=chargepoint.ampeco_charge_point_name,    
                        worldline_terminal_id=(
                            chargepoint.worldline_terminal_id
                            if WORLDLINE_PAYMENT_TERMINAL in data.payment_terminal
                            else None
                        ),                    
                    )
                    for connector in chargepoint.connectors:
                        if not connector.deleted:
                            tariff_amount = (
                                float(connector.tariff_amount)
                                if connector.tariff_amount
                                else 0
                            )
                            station_connector = StationConnector.objects.create(
                                station_id=station_create,
                                charge_point_id=charge_point,
                                connector_id=connector.connector_id,
                                connector_name=connector.connector_name,
                                connector_type=connector.connector_type,
                                plug_type_name=connector.plug_type_name,
                                status=connector.status,
                                max_charge_rate=connector.maximum_charge_rate,
                                connector_sorting_order=(
                                    connector.connector_sorting_order
                                ),
                                tariff_amount=tariff_amount,
                                tariff_currency=connector.tariff_currency,
                                created_date=timezone.localtime(timezone.now()),
                                updated_by=user.full_name,
                                back_office = back_office_name.upper(),
                                connector_evse_uid = connector.evse_uid
                            )
                            update_evse_and_connectors(
                                evses,
                                ocpi_connectors,
                                connector,
                                charge_point,
                                station_connector,
                                station_create
                            )
        
    except Exception as e:
        print("Failed to insert station connector data: ", e)            


def insert_valeting_terminals_data(data, user, station_create):
    if data.valeting == YES:
        # Logic to insert valeting terminals
        for valeting_terminal in data.valeting_terminals:
            if not valeting_terminal.deleted:
                valeting_terminal = ValetingTerminals.objects.create(
                    station_id=station_create,
                    payter_serial_number=valeting_terminal.payter_serial_number,
                    status=valeting_terminal.status,
                    amenities=array_to_string_converter(
                        valeting_terminal.amenities
                    ),
                    created_date=timezone.localtime(timezone.now()),
                    updated_by=user.full_name,
                )

def insert_valeting_machines_data(data, user, station_create):
    if data.valeting == YES and hasattr(data, 'valeting_machines'):
        for valeting_machine in data.valeting_machines:
            if not valeting_machine.deleted:
                is_active = (valeting_machine.status == "Active" if hasattr(valeting_machine, 'status')
                            else valeting_machine.is_active)
                
                ValetingMachine.objects.create(
                    station_id=station_create,
                    machine_id=valeting_machine.machine_id,
                    machine_name=valeting_machine.machine_name,
                    machine_number=valeting_machine.machine_number,
                    is_active=is_active,
                    created_date=timezone.localtime(timezone.now()),
                    updated_by=user.full_name,
                )


def insert_station_services_data(data, user, station_create):
    """this function helps to insert services data for station"""
    # Inserting amenities
    for amenity in list(set(data.amenities)):
        StationServices.objects.create(
            service_id=return_service_instance_from_configuration(amenity),
            station_id=station_create,
            service_name="Amenity",
            created_date=timezone.localtime(timezone.now()),
            updated_by=user.full_name,
        )
    # Inserting retail shops
    for retail in list(set(data.retail)):
        StationServices.objects.create(
            service_id=return_service_instance_from_configuration(retail),
            station_id=station_create,
            service_name="Retail",
            created_date=timezone.localtime(timezone.now()),
            updated_by=user.full_name,
        )

    # Inserting food service shops
    for food in list(set(data.food_to_go)):
        StationServices.objects.create(
            service_id=return_service_instance_from_configuration(food),
            station_id=station_create,
            service_name=FOOD_TO_GO,
            created_date=timezone.localtime(timezone.now()),
            updated_by=user.full_name,
        )


def update_station_working_hours_entry(data, user, station_pk_operator):
    """this function help to update working hour details for station"""

    monday_friday = ""
    saturday = ""
    sunday = ""
    # Checking whether station is 24 hours open or not
    if data.working_hours.monday_friday.full_hours:
        monday_friday = HOURS_24
    else:
        monday_friday = working_hours_handler(
            data.working_hours.monday_friday.start_time,
            data.working_hours.monday_friday.end_time,
        )

    if data.working_hours.saturday.full_hours:
        saturday = HOURS_24
    else:
        saturday = working_hours_handler(
            data.working_hours.saturday.start_time,
            data.working_hours.saturday.end_time,
        )

    if data.working_hours.sunday.full_hours:
        sunday = HOURS_24
    else:
        sunday = working_hours_handler(
            data.working_hours.sunday.start_time,
            data.working_hours.sunday.end_time,
        )

    # Working hours update query.
    StationWorkingHours.objects.filter(
        station_id_id=station_pk_operator
    ).update(
        monday_friday=monday_friday,
        saturday=saturday,
        sunday=sunday,
        updated_date=timezone.localtime(timezone.now()),
        updated_by=user.full_name,
    )


def create_station_connector_function(
    station, chargepoint, connector, tariff_amount, user, evses, ocpi_connectors,back_office_key
):
    """this function creates station connector"""
    station_connector = StationConnector.objects.create(
        station_id=station,
        charge_point_id=chargepoint,
        connector_id=connector.connector_id,
        connector_name=connector.connector_name,
        connector_type=connector.connector_type,
        plug_type_name=connector.plug_type_name,
        status=connector.status,
        max_charge_rate=connector.maximum_charge_rate,
        connector_sorting_order=connector.connector_sorting_order,
        tariff_amount=tariff_amount,
        tariff_currency=connector.tariff_currency,
        created_date=timezone.localtime(timezone.now()),
        updated_by=user.full_name,
        back_office = back_office_key.upper()
    )
    
    update_evse_and_connectors(
        evses,
        ocpi_connectors,
        connector,
        chargepoint,
        station_connector,
        station
        )

def update_station_connector_function(connector, user, tariff_amount, old_chargepoint, evses, ocpi_connectors,back_office_key,station):
    """this function updates station connector"""
    station_connector = StationConnector.objects.filter(id=connector.con_id)
    station_connector.update(
        connector_id=connector.connector_id,
        connector_name=connector.connector_name,
        connector_type=connector.connector_type,
        plug_type_name=connector.plug_type_name,
        status=connector.status,
        max_charge_rate=connector.maximum_charge_rate,
        connector_sorting_order=connector.connector_sorting_order,
        tariff_amount=tariff_amount,
        tariff_currency=connector.tariff_currency,
        updated_date=timezone.localtime(timezone.now()),
        updated_by=user.full_name,
        back_office = back_office_key.upper(),
        connector_evse_uid = connector.evse_uid
    )

    update_evse_and_connectors(
        evses,
        ocpi_connectors,
        connector,
        old_chargepoint,
        station_connector.first(),
        station
        )

def update_station_connector_data(data, user, station, location_ids,back_office_key):
    """this function helps to update station chargepoints"""
    if data.station_type != "MFG Forecourt":
        # OCPIConnector.objects.filter(
        #     connector_mapping_id=connector.con_id
        # )
        evses = OCPIEVSE.objects.filter(
            location_id__in = location_ids
        )
        ocpi_connectors = OCPIConnector.objects.filter(evse_id__in = evses)       


        # Looping over chargepoints sent from frontend
        for chargepoint in data.chargepoints:
            # Condition to check whether chargepoint is already
            # present for station in databse or newly added while updation
            if chargepoint.cp_id:
                # Fetching chagepoint if chargepoint alredy exists for station
                old_chargepoint = ChargePoint.objects.filter(
                    id=chargepoint.cp_id
                )
                if chargepoint.deleted:
                    StationConnector.objects.filter(
                        charge_point_id=old_chargepoint.first()
                    ).update(
                        deleted=YES,
                        updated_date=timezone.localtime(timezone.now()),
                        updated_by=user.full_name,
                    )
                    old_chargepoint.update(
                        deleted=YES,
                        updated_date=timezone.localtime(timezone.now()),
                        updated_by=user.full_name,
                    )
                else:
                    old_chargepoint.update(
                        charger_point_id=chargepoint.charge_point_id,
                        charger_point_name=chargepoint.charge_point_name,
                        charger_point_status=chargepoint.status,
                        back_office=back_office_key.upper(),
                        device_id=chargepoint.device_id,
                        payter_terminal_id=(
                            chargepoint.payter_terminal_id
                            if PAYTER_PAYMENT_TERMINAL in data.payment_terminal
                            else None
                        ),
                        ampeco_charge_point_id=getattr(chargepoint, "ampeco_charge_point_id", ""),
                        ampeco_charge_point_name=getattr(chargepoint, "ampeco_charge_point_name", ""),
                        worldline_terminal_id=(
                            chargepoint.worldline_terminal_id
                            if WORLDLINE_PAYMENT_TERMINAL in data.payment_terminal
                            else None
                        ),
                        updated_date=timezone.localtime(timezone.now()),
                        updated_by=user.full_name,
                    )
                    # Looping over chargepoint connectors sent from frontend
                    for connector in chargepoint.connectors:
                        # Condition to check whether chargepoint
                        # connector is already present for station in databse
                        # or newly added while updation
                        tariff_amount = (
                            float(connector.tariff_amount)
                            if connector.tariff_amount
                            else 0
                        )
                        if connector.con_id:
                            if connector.deleted:
                                StationConnector.objects.filter(
                                    id=connector.con_id
                                ).update(
                                    deleted=YES,
                                    updated_date=timezone.localtime(
                                        timezone.now()
                                    ),
                                    updated_by=user.full_name,
                                )
                            else:
                                update_station_connector_function(
                                    connector, user, tariff_amount, old_chargepoint, evses, ocpi_connectors,back_office_key,station
                                )

                        else:
                            # If connectors were not present for particular
                            # chargepoint then we have to add them.
                            if not connector.deleted:
                                create_station_connector_function(
                                    station,
                                    old_chargepoint.first(),
                                    connector,
                                    tariff_amount,
                                    user,
                                    evses,
                                    ocpi_connectors,
                                    back_office_key
                                )
            else:
                # If the chargepoint is added newly while updating the station
                # then we have to add it. Below are the queries to add
                # chargepoint and connectors to station.

                if not chargepoint.deleted:
                    newly_added_chargepoint = ChargePoint.objects.create(
                        station_id=station,
                        charger_point_id=chargepoint.charge_point_id,
                        charger_point_name=chargepoint.charge_point_name,
                        charger_point_status=chargepoint.status,
                        back_office=back_office_key,
                        device_id=chargepoint.device_id,
                        payter_terminal_id=(
                            chargepoint.payter_terminal_id
                            if PAYTER_PAYMENT_TERMINAL in data.payment_terminal
                            else None
                        ),
                        ampeco_charge_point_id=getattr(chargepoint, "ampeco_charge_point_id", ""),
                        ampeco_charge_point_name=getattr(chargepoint, "ampeco_charge_point_name", ""),
                        worldline_terminal_id=(
                            chargepoint.worldline_terminal_id
                            if WORLDLINE_PAYMENT_TERMINAL in data.payment_terminal
                            else None
                        ),
                        updated_date=timezone.localtime(timezone.now()),
                        updated_by=user.full_name,
                    )

                    for connector in chargepoint.connectors:
                        if not connector.deleted:
                            tariff_amount = (
                                float(connector.tariff_amount)
                                if connector.tariff_amount
                                else 0
                            )
                            create_station_connector_function(
                                station,
                                newly_added_chargepoint,
                                connector,
                                tariff_amount,
                                user,
                                evses,
                                ocpi_connectors,
                                back_office_key
                            )                            


def update_station_serives_sub_data(*args):
    """this function helps to update services sub data for station"""
    (
        services,
        previous,
        station_pk_operator,
        user,
        service_name,
        current_services,
    ) = args
    for service_from_configuration in services:
        for service in previous:
            if service.service_id_id == service_from_configuration["id"]:
                if service.service_id_id in current_services:
                    if service.deleted == YES:
                        StationServices.objects.filter(
                            station_id_id=station_pk_operator,
                            service_name=service_name,
                            service_id=service.service_id,
                        ).update(
                            deleted=NO,
                            updated_date=timezone.localtime(timezone.now()),
                            updated_by=user.full_name,
                        )
                else:
                    StationServices.objects.filter(
                        station_id_id=station_pk_operator,
                        service_name=service_name,
                        service_id=service.service_id,
                    ).update(
                        deleted=YES,
                        updated_date=timezone.localtime(timezone.now()),
                        updated_by=user.full_name,
                    )


def update_station_services_data(*args):
    """this function helps to update services data for station"""
    (
        data,
        user,
        station_pk_operator,
        station_operator,
        amenities_services_operator,
        retails_services_operator,
        food_to_go_services_operator,
    ) = args
    # updation logic for amenities
    previous_amenities = StationServices.objects.filter(
        station_id_id=station_pk_operator, service_name="Amenity"
    )
    previous_amenities_list = []
    for amenity in previous_amenities:
        previous_amenities_list.append(amenity.service_id_id)
    station_shops = []
    for amenity in list(set(data.amenities)):
        amenity_instance = return_service_instance_from_configuration(amenity)
        station_shops.append(amenity_instance.service_name)
        if amenity not in previous_amenities_list:
            StationServices.objects.create(
                service_id=amenity_instance,
                station_id=station_operator,
                service_name="Amenity",
                created_date=timezone.localtime(timezone.now()),
                updated_by=user.full_name,
            )
    update_station_serives_sub_data(
        amenities_services_operator,
        previous_amenities,
        station_pk_operator,
        user,
        "Amenity",
        data.amenities,
    )
    previous_retail = StationServices.objects.filter(
        station_id_id=station_pk_operator, service_name="Retail"
    )

    previous_retail_list = []
    for retail in previous_retail:
        previous_retail_list.append(retail.service_id_id)

    for retail in list(set(data.retail)):
        retail_instance = return_service_instance_from_configuration(retail)
        station_shops.append(retail_instance.service_name)
        if retail not in previous_retail_list:
            StationServices.objects.create(
                service_id=retail_instance,
                station_id=station_operator,
                service_name="Retail",
                created_date=timezone.localtime(timezone.now()),
                updated_by=user.full_name,
            )

    update_station_serives_sub_data(
        retails_services_operator,
        previous_retail,
        station_pk_operator,
        user,
        "Retail",
        data.retail,
    )

    previous_food = StationServices.objects.filter(
        station_id_id=station_pk_operator, service_name=FOOD_TO_GO
    )
    previous_food_list = []
    for food in previous_food:
        previous_food_list.append(food.service_id_id)

    for food in list(set(data.food_to_go)):
        food_to_go_instance = return_service_instance_from_configuration(food)
        station_shops.append(food_to_go_instance.service_name)
        if food not in previous_food_list:
            StationServices.objects.create(
                service_id=food_to_go_instance,
                station_id=station_operator,
                service_name=FOOD_TO_GO,
                created_date=timezone.localtime(timezone.now()),
                updated_by=user.full_name,
            )

    update_station_serives_sub_data(
        food_to_go_services_operator,
        previous_food,
        station_pk_operator,
        user,
        FOOD_TO_GO,
        data.food_to_go,
    )
    station_promotions = PromotionsAvailableOn.objects.filter(
        station_id_id=station_pk_operator, deleted=NO
    )
    audit_data_generated = []
    for station_promotion in station_promotions:
        if station_promotion.promotion_id:
            station_promotion_shops = string_to_array_converter(
                station_promotion.promotion_id.shop_ids
            )
            for station_promotion_shop in station_promotion_shops:
                if station_promotion_shop in station_shops:
                    break
            else:
                old_data = audit_data_formatter(
                    PROMOTIONS_CONST, station_promotion.promotion_id.id
                )
                station_promotions.filter(id=station_promotion.id).update(
                    deleted=YES
                )
                new_data = audit_data_formatter(
                    PROMOTIONS_CONST, station_promotion.promotion_id.id
                )
                if old_data != new_data:
                    audit_data_generated.append(
                        add_audit_data(
                            user,
                            (
                                station_promotion.promotion_id.unique_code
                                + ", "
                                + station_promotion.promotion_id.promotion_title
                            ),
                            (
                                PROMOTIONS_CONST
                                + "-"
                                + str(station_promotion.promotion_id.id)
                            ),
                            AUDIT_UPDATE_CONSTANT,
                            PROMOTIONS_CONST,
                            new_data,
                            old_data,
                        )
                    )
    station_loyalties = LoyaltyAvailableOn.objects.filter(
        station_id_id=station_pk_operator, deleted=NO
    )
    for station_loyalty in station_loyalties:
        if station_loyalty.loyalty_id and station_loyalty.loyalty_id.shop_ids:
              
            station_loyalty_shops = string_to_array_converter(
                station_loyalty.loyalty_id.shop_ids
            )
            for station_loyalty_shop in station_loyalty_shops:
                if station_loyalty_shop in station_shops:
                    break
            else:
                old_data = audit_data_formatter(
                    LOYALTY_CONST, station_loyalty.loyalty_id.id
                )
                station_loyalties.filter(id=station_loyalty.id).update(deleted=YES)
                new_data = audit_data_formatter(
                    LOYALTY_CONST, station_loyalty.loyalty_id.id
                )
                if old_data != new_data:
                    audit_data_generated.append(
                        add_audit_data(
                            user,
                            (
                                station_loyalty.loyalty_id.unique_code
                                + ", "
                                + station_loyalty.loyalty_id.loyalty_title
                            ),
                            (
                                LOYALTY_CONST
                                + "_"
                                + str(station_loyalty.loyalty_id.id)
                            ),
                            AUDIT_UPDATE_CONSTANT,
                            LOYALTY_CONST,
                            new_data,
                            old_data,
                        )
                    )
    return audit_data_generated


def update_station_valeting_data(data, user, station):
    if data.valeting == YES and data.valeting_terminals:
        for valeting_terminal in data.valeting_terminals:
            if valeting_terminal.db_id:
                ValetingTerminals.objects.filter(
                    station_id=station, id=valeting_terminal.db_id
                ).update(
                    payter_serial_number=valeting_terminal.payter_serial_number,
                    amenities=array_to_string_converter(
                        valeting_terminal.amenities
                    ),
                    status=valeting_terminal.status,
                    deleted=YES if valeting_terminal.deleted else NO,
                    updated_date=timezone.localtime(timezone.now()),
                    updated_by=user.full_name,
                )
            else:
                if not valeting_terminal.deleted:
                    ValetingTerminals.objects.create(
                        station_id=station,
                        payter_serial_number=valeting_terminal.payter_serial_number,
                        amenities=array_to_string_converter(
                            valeting_terminal.amenities
                        ),
                        status=valeting_terminal.status,
                        created_date=timezone.localtime(timezone.now()),
                        updated_by=user.full_name,
                    )
    else:
        ValetingTerminals.objects.filter(
            station_id=station,
        ).update(
            deleted=YES,
            updated_date=timezone.localtime(timezone.now()),
            updated_by=user.full_name,
        )

def update_evse_and_connectors(evses,ocpi_connectors,connector,chargepoint,station_connector,station):
    
    for evse in evses:
        if evse.uid == connector.evse_uid:
            try:
                OCPIEVSE.objects.filter(
                    uid = connector.evse_uid
                ).update(chargepoint_mapping_id = chargepoint)
            except:
                OCPIEVSE.objects.filter(
                    uid = connector.evse_uid
                ).update(chargepoint_mapping_id = chargepoint.first())   
    
    try:
        for ocpi_connector in ocpi_connectors:
            if ocpi_connector.connector_id == connector.ocpi_connector_id:
                
                OCPIConnector.objects.filter(
                    ~Q(id = ocpi_connector.id),
                    connector_mapping_id = connector.ocpi_connector_id,
                ).update(
                    connector_mapping_id = None
                )
                
                OCPIConnector.objects.filter(
                    id = ocpi_connector.id
                ).update(connector_mapping_id_id = station_connector) 
    except:
        traceback.print_exc()


def update_evse_and_connectors(evses,ocpi_connectors,connector,chargepoint,station_connector,station):
    
    for evse in evses:
        if evse.uid == connector.evse_uid:
            try:
                OCPIEVSE.objects.filter(
                    uid = connector.evse_uid
                ).update(chargepoint_mapping_id = chargepoint)
            except:
                OCPIEVSE.objects.filter(
                    uid = connector.evse_uid
                ).update(chargepoint_mapping_id = chargepoint.first())   
    
    try:
        for ocpi_connector in ocpi_connectors:
            if ocpi_connector.connector_id == connector.ocpi_connector_id:
                
                OCPIConnector.objects.filter(
                    ~Q(id = ocpi_connector.id),
                    connector_mapping_id = connector.ocpi_connector_id,
                ).update(
                    connector_mapping_id = None
                )
                
                OCPIConnector.objects.filter(
                    id = ocpi_connector.id
                ).update(connector_mapping_id_id = station_connector) 
    except:
        traceback.print_exc()

def update_station_valeting_machines(data, user, station):
    if data.valeting and hasattr(data, 'valeting_machines') and data.valeting_machines:
        for valeting_machine in data.valeting_machines:
            if valeting_machine.db_id:
                # Update existing machine
                ValetingMachine.objects.filter(
                    station_id=station, 
                    id=valeting_machine.db_id
                ).update(
                    machine_id=valeting_machine.machine_id,
                    machine_name=valeting_machine.machine_name,
                    machine_number=valeting_machine.machine_number,
                    is_active=valeting_machine.is_active,
                    updated_date=timezone.localtime(timezone.now()),
                    updated_by=user.full_name,
                    deleted=valeting_machine.deleted if hasattr(valeting_machine, 'deleted') else False
                )
            else:
                # Create new machine if not deleted
                if not valeting_machine.deleted:
                    try:
                        ValetingMachine.objects.create(
                            station_id=station,
                            machine_id=valeting_machine.machine_id,
                            machine_name=valeting_machine.machine_name,
                            machine_number=valeting_machine.machine_number,
                            is_active=valeting_machine.is_active,
                            created_date=timezone.localtime(timezone.now()),
                            updated_by=user.full_name,
                        )
                    except IntegrityError:
                        # machine_id already exists
                        print(f"Machine ID {valeting_machine.machine_id} already exists for this station.")
                        ValetingMachine.objects.filter(
                            station_id=station,
                        ).update(
                            deleted=False,
                            machine_name=valeting_machine.machine_name,
                            machine_number=valeting_machine.machine_number,
                            is_active=valeting_machine.is_active,
                            updated_date=timezone.localtime(timezone.now()),
                            updated_by=user.full_name,
                        )
    else:
        # Soft delete all machines if valeting is disabled or no machines provided
        ValetingMachine.objects.filter(
            station_id=station,
        ).update(
            deleted=True,
            updated_date=timezone.localtime(timezone.now()),
            updated_by=user.full_name,
        )

def add_update_valeting_machines(valeting_machines_data):
    """Bulk create/update valeting machines"""
    bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="stations",
    )
    total_machines = len(valeting_machines_data)
    stations = Stations.objects.all()
    machines_to_create = []
    processed_machine_ids = []
    
    with transaction.atomic():
        for machine_data in valeting_machines_data:
            # Get the station
            station = stations.filter(
                station_id=machine_data["station_id"]
            ).first()
            
            if not station:
                continue
                
            # Check if machine exists
            existing_machine = ValetingMachine.objects.filter(
                machine_id=machine_data["machine_id"]
            ).first()
            
            if existing_machine:
                # Update existing machine
                existing_machine.station_id = station
                existing_machine.machine_name = machine_data.get("machine_name")
                existing_machine.machine_number = machine_data.get("machine_number")
                existing_machine.is_active = machine_data.get("is_active", True)
                existing_machine.updated_date = machine_data["updated_date"]
                existing_machine.updated_by = machine_data["updated_by"]
                existing_machine.deleted = False
                existing_machine.save()
            else:
                # Prepare new machine creation
                if machine_data["machine_id"] not in processed_machine_ids:
                    processed_machine_ids.append(machine_data["machine_id"])
                    machines_to_create.append(
                        ValetingMachine(
                            machine_id=machine_data["machine_id"],
                            station_id=station,
                            machine_name=machine_data.get("machine_name"),
                            machine_number=machine_data.get("machine_number"),
                            is_active=machine_data.get("is_active", True),
                            created_date=machine_data.get("created_date", timezone.now()),
                            updated_date=machine_data["updated_date"],
                            updated_by=machine_data["updated_by"],
                        )
                    )
    
    # Bulk create new machines
    ValetingMachine.objects.bulk_create(machines_to_create)
    
    # Update progress counter
    if bulk_upload_progress.exists():
        current_count = (
            int(bulk_upload_progress.first().uploaded_rows_count) + total_machines
        )
        bulk_upload_progress.update(uploaded_rows_count=current_count)