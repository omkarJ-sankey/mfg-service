
from datetime import timezone
from adminServices.stations.bulk_upload_functions import sites_bulk_upload
from adminServices.stations.db_operators import create_single_station_func
from adminServices.stations.stations_helper_functions import check_is_ev_status, create_station, remove_stations_cached_data, update_database_stations
from sharedServices.common_audit_trail_functions import add_audit_data, audit_data_formatter
from sharedServices.constants import AUDIT_ADD_CONSTANT, AUDIT_DELETE_CONSTANT, IS_MFG_KEYS, SITES_CONST, ConstantMessage
from django.db import DatabaseError, DataError

from sharedServices.model_files.audit_models import AuditTrail
from sharedServices.model_files.loyalty_models import LoyaltyAvailableOn
from sharedServices.model_files.ocpi_locations_models import OCPIEVSE, OCPIConnector, OCPILocation
from sharedServices.model_files.promotions_models import Promotions, PromotionsAvailableOn
from sharedServices.model_files.station_models import ChargePoint, StationConnector, StationImages, StationServices, StationWorkingHours, Stations, ValetingTerminals
from django.db import DatabaseError, DataError
import pandas as pd
import zipfile
import threading
import traceback
from django.db.models import Q

from sharedServices.model_files.valeting_models import ValetingMachine

def add_station_service(validated_data, user):
    """add station view"""
    station_id = validated_data.get("station_id")
    station_name = validated_data.get("station_name")
    station_type = validated_data.get("station_type")
    brand = validated_data.get("brand")
    chargepoints = validated_data.get("chargepoints", [])
    backoffice_list = validated_data.get("backoffice", [])

    # Determine station type flags
    is_mfg = "YES" if station_type in IS_MFG_KEYS else "NO"
    is_ev = "YES" if check_is_ev_status(validated_data) else "NO"

    # Prepare backoffice mapping
    back_office_data = {item['back_office']: item['location_id'] for item in backoffice_list}

    try:
        # Call existing station creation function
        station_create, locations = create_single_station_func(validated_data, is_mfg, is_ev, user, back_office_data)

        # Insert working hours / additional station data
        back_office = list(back_office_data.keys())[0] if back_office_data else None
        if station_create:
            response_op = create_station(user, station_create, validated_data, locations, back_office)
            if response_op:  # If create_station returns custom response
                return response_op

            # Audit logging
            new_data = audit_data_formatter(SITES_CONST, station_create.station_id)
            add_audit_data(
                user,
                f"{station_create.station_id}, {station_create.station_name}",
                f"{SITES_CONST}-{station_create.id}",
                AUDIT_ADD_CONSTANT,
                SITES_CONST,
                new_data,
                None,
            )

        # Clear cached stations
        remove_stations_cached_data()

        return {"status": True, "message": ConstantMessage.STATION_CREATED_SUCCESSFULLY, "data": {"station_id": station_create.station_id}}

    except (DatabaseError, DataError):
        return {"status": False, "message": ConstantMessage.STATION_CREATION_FAILED}
    


def upload_sheet_service(file_obj, user):
    """
    Service layer for bulk upload of station Excel sheets.
    Validates tabs, fields, and initiates asynchronous DB insertions.
    """
    tab_errors_stations = []

    try:
        xls = pd.ExcelFile(file_obj, engine="openpyxl")

        # Attempt to read each required tab
        try:
            sites = pd.read_excel(xls, "Sites", dtype=str)
        except ValueError:
            tab_errors_stations.append(ConstantMessage.TAB_SITES)

        try:
            devices = pd.read_excel(xls, "Chargepoint", dtype=str)
        except ValueError:
            tab_errors_stations.append(ConstantMessage.TAB_CHARGEPOINT)

        try:
            site_details = pd.read_excel(xls, "MFG", dtype=str)
        except ValueError:
            tab_errors_stations.append(ConstantMessage.TAB_MFG)

        try:
            valeting_details = pd.read_excel(xls, "Valeting Terminals", dtype=str)
        except ValueError:
            tab_errors_stations.append(ConstantMessage.TAB_VALETING_TERMINALS)

        try:
            valeting_machines = pd.read_excel(xls, "Valeting Machines", dtype=str)
        except ValueError:
            tab_errors_stations.append(ConstantMessage.TAB_VALETING_MACHINES)

        # If any tab is missing
        if tab_errors_stations:
            error_message = ConstantMessage.MISSING_SHEETS.format(
                missing_tabs=" & ".join(tab_errors_stations)
            )
            return {"status": False, "message": error_message}

        # Process the Excel data
        data_stations = sites_bulk_upload(
            sites, user, devices, site_details, valeting_details, valeting_machines
        )

        return {
            "status": True,
            "message": ConstantMessage.SUCCESS,
            "data": data_stations
        }

    except zipfile.BadZipFile:
        traceback.print_exc()
        return {"status": False, "message": ConstantMessage.INVALID_EXCEL_FILE}

    except Exception as e:
        traceback.print_exc()
        return {"status": False, "message": f"{ConstantMessage.UNKNOWN_ERROR}: {str(e)}"}



def get_station_list(filters):
    """Service to fetch and filter station list based on given filters."""
    queryset = Stations.objects.filter(deleted="No")

    # Extract filters
    search = filters.get("search", "")
    brand = filters.get("brand")
    station_type = filters.get("station_type")
    status = filters.get("status")
    order_by_station = filters.get("order_by_station")

    # Apply filters
    if search:
        queryset = queryset.filter(
            Q(station_id__icontains=search) | Q(station_name__icontains=search)
        )
    if brand:
        queryset = queryset.filter(brand=brand)
    if station_type:
        queryset = queryset.filter(station_type=station_type)
    if status:
        queryset = queryset.filter(status=status)
    if order_by_station:
        queryset = queryset.order_by(order_by_station)

    return queryset


def get_station_details_service(validated_data):
    """Fetch all related details for a given station."""
    station_pk = validated_data["station_pk"]
    station = Stations.objects.get(id=station_pk, deleted="No")

    # Amenities
    amenities_ids = list(
        StationServices.objects.filter(
            station_id=station_pk, service_name="Amenity", deleted="No"
        ).values_list("service_id", flat=True)
    )

    # Food services
    food_ids = list(
        StationServices.objects.filter(
            station_id=station_pk, service_name="Food To Go", deleted="No"
        ).values_list("service_id", flat=True)
    )

    # Retails
    retail_ids = list(
        StationServices.objects.filter(
            station_id=station_pk, service_name="Retail", deleted="No"
        ).values_list("service_id", flat=True)
    )

    # Promotions
    promotions = Promotions.objects.filter(
        ~Q(image=None),
        station_available_promotions__station_id=station,
        deleted="No",
        station_available_promotions__deleted="No",
        status="Active",
        end_date__gte=timezone.localtime(timezone.now()),
        start_date__lte=timezone.localtime(timezone.now()),
    ).distinct()

    promotion_data = [
        {"title": prom.promotion_title, "image": prom.get_promotion_image()}
        for prom in promotions
    ]

    # Valeting machines
    valeting_machines = ValetingMachine.objects.filter(
        station_id=station_pk, deleted=False
    ).values("machine_id", "machine_name", "is_active")

    # Station images
    images = [img.image.url for img in StationImages.objects.filter(station_id=station_pk)]

    return {
        "station_id": station.station_id,
        "station_name": station.station_name,
        "brand": station.brand,
        "station_type": station.station_type,
        "status": station.status,
        "amenities": amenities_ids,
        "food_services": food_ids,
        "retails": retail_ids,
        "images": images,
        "payment_terminals": station.payment_terminal.split(",") if station.payment_terminal else [],
        "promotions": promotion_data,
        "valeting_machines": list(valeting_machines),
        "tariffs": {},
        "back_offices": station.ocpi_locations or {},
        "get_full_address": station.get_full_address,
    }



def update_station_data(request, station_pk, station_obj, amenities_services, retails_services, food_services, query_params_str):
    """
    Update station details using provided request data.
    """
    return update_database_stations(request, station_pk, station_obj, amenities_services, retails_services, food_services, query_params_str)



def delete_station_service(station_pk, user):
    """Service to perform soft deletion of a station and related objects."""
    # Soft-delete the station
    stations = Stations.objects.filter(id=station_pk)
    station = stations.first()
    stations.update(deleted="YES")

    # Clear OCPI mappings
    locations = OCPILocation.objects.filter(station_mapping_id=station)
    evses = OCPIEVSE.objects.filter(location_id__in=locations)
    OCPIConnector.objects.filter(evse_id__in=evses).update(connector_mapping_id=None)
    evses.update(chargepoint_mapping_id=None)
    locations.update(station_mapping_id=None)

    # Soft-delete related objects
    related_models = [
        StationWorkingHours,
        ChargePoint,
        StationConnector,
        StationImages,
        StationServices,
        ValetingTerminals,
        PromotionsAvailableOn,
        LoyaltyAvailableOn
    ]

    for model in related_models:
        model.objects.filter(station_id_id=station_pk).update(
            deleted="YES",
            updated_date=timezone.localtime(timezone.now()),
            updated_by=user.full_name
        )

    # Update station_id to mark old
    prev_audit_data = AuditTrail.objects.filter(
        data_db_id=f"{SITES_CONST}-{station_pk}"
    ).last()

    prev_locations = Stations.objects.filter(station_id__startswith=station.station_id)
    updated_station_id = f"{station.station_id}_OLD_{prev_locations.count()}"
    stations.update(station_id=updated_station_id)

    # Add audit log
    if prev_audit_data and prev_audit_data.new_data:
        prev_audit_data_content = prev_audit_data.new_data
        add_audit_data(
            user,
            f"{station.station_id}, {station.station_name}",
            f"{SITES_CONST}-{station_pk}",
            AUDIT_DELETE_CONSTANT,
            SITES_CONST,
            None,
            prev_audit_data_content
        )

    # Clear cached station data
    remove_stations_cached_data()

    return {
        "station_id": station.station_id,
        "station_name": station.station_name,
        "deleted_by": user.full_name,
        "deleted_at": timezone.localtime(timezone.now()),
    }
