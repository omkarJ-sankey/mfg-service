"""stations views"""

# Date - 26/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on views(backend logic)
#                      related to stations.
#   Name            - Station Views
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 29/05/2025

# imports required to create views
import json
import traceback
from types import SimpleNamespace
import googlemaps
from decouple import config
from rest_framework import status

from django.db import DataError, DatabaseError
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.views.decorators.http import require_http_methods
from django.db.models import OuterRef, Subquery, F, Q
from django.conf import settings
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
import logging
from django.views.decorators.csrf import csrf_exempt
import requests
import traceback

# pylint:disable=import-error
from sharedServices.model_files.valeting_models import ValetingMachine

from sharedServices.ocpi_common_functions import get_back_office_data

from sharedServices.model_files.bulk_models import (
    BulkUploadErrorMessages,
    BulkUploadProgress,
)
from sharedServices.model_files.station_models import (
    StationConnector,
    StationImages,
    StationServices,
    StationWorkingHours,
    Stations,
    ChargePoint,
    ValetingTerminals,
)
from sharedServices.model_files.ocpi_tariffs_models import (
    Tariffs,
    TariffElements,
    TariffRestrictions,
    TariffComponents
)
from datetime import datetime
from django.utils.timezone import now
from sharedServices.model_files.promotions_models import (
    Promotions,
    PromotionsAvailableOn,
)
from sharedServices.model_files.ocpi_credentials_models import OCPICredentials
from sharedServices.model_files.loyalty_models import LoyaltyAvailableOn
from sharedServices.model_files.audit_models import AuditTrail
from sharedServices.decorators import allowed_users, authenticated_user
from sharedServices.common import (
    api_response,
    export_data_function_multi_tabs,
    filter_url,
    order_by_function,
    paginate_and_serialize,
    pagination_and_filter_func,
    string_to_array_converter,
    search_validator,
    redis_connection
)
from sharedServices.common_audit_trail_functions import (
    add_audit_data,
    services_categorization_function,
    audit_data_formatter,
)
from sharedServices.constants import (
    AZURE_BLOB_STORAGE_URL,
    IS_MFG_KEYS,
    STATION_ID,
    YES,
    NO,
    EXPORT_TRUE,
    GET_METHOD_ALLOWED,
    POST_METHOD_ALLOWED,
    SITES_CONST,
    AUDIT_ADD_CONSTANT,
    AUDIT_DELETE_CONSTANT,
    COMMON_ERRORS,
    ERROR_TEMPLATE_URL,
    PAYTER_PAYMENT_TERMINAL,
    WORLDLINE_PAYMENT_TERMINAL,
    ADVAM_PAYMENT_TERMINAL,
    OCPI_CREDENTIALS_CACHE_KEY,
    AMPECO_LOCATIONS_ENDPOINT,
    AMPECO_CHARGEPOINTS_ENDPOINT,
    IS_EV_KEYS
)
from .db_operators import create_single_station_func
from .stations_helper_functions import (
    export_station_data_function,
    remove_stations_cached_data,
    station_site_locations_list,
    connector_types,
    create_station,
    update_database_stations,
    check_is_ev_status,
)
from .app_level_constants import NO_CHARGEPOINTS_PROVIDED_MESSAGE
from sharedServices.model_files.ocpi_locations_models import OCPIConnector,OCPILocation,OCPIEVSE
from sharedServices.ocpi_common_functions import get_location_backoffice

gmaps = googlemaps.Client(key=config("DJANGO_APP_GOOGLE_API_KEY"))
map_api_key = settings.GOOGLE_MAPS_API_KEY

CACHE_TTL = getattr(settings, "CACHE_TTL", DEFAULT_TIMEOUT)

logger = logging.getLogger(__name__)


# This function returns data such as operation regions, regions, area
def station_list_export(filtered_data_stations):
    """station list export"""
    response_op_station = export_station_data_function(
        filtered_data_stations["filtered_table_for_export"]
    )
    if response_op_station:
        response_op_station.set_cookie(
            "exported_data_cookie_condition", EXPORT_TRUE, max_age=8
        )
    return response_op_station


def station_list_error_export():
    """station list export"""
    stations_error_records = BulkUploadErrorMessages.objects.filter(
        uploaded_for="stations", ready_to_export=YES
    )
    if stations_error_records.first():
        errors = string_to_array_converter(
            stations_error_records.first().errors
        )
        sites_errors = errors[0]["errors"]
        chargepoint_errors = errors[1]["errors"]
        mfg_tab_errors = errors[2]["errors"]
        valeting_tab_errors = errors[3]["errors"]
        error_response_stations = export_data_function_multi_tabs(
            [
                sites_errors,
                chargepoint_errors,
                mfg_tab_errors,
                valeting_tab_errors,
            ],
            [
                [STATION_ID, "Error"],
                [STATION_ID, "Error"],
                [STATION_ID, "Error"],
                [STATION_ID, "Error"],
            ],
            [
                [STATION_ID, "Error"],
                [STATION_ID, "Error"],
                [STATION_ID, "Error"],
                [STATION_ID, "Error"],
            ],
            [SITES_CONST, "Chargepoints", "MFG", "Valeting Terminals"],
        )
        stations_error_records.update(ready_to_export=NO)
        if error_response_stations:
            error_response_stations.set_cookie(
                "exported_data_cookie_condition", EXPORT_TRUE, max_age=8
            )
            return error_response_stations
    return None


def station_list_export_percentage(station_bulk_upload_progress):
    """station list percentage"""
    percentage_station = 0
    bulk_upload_running = False
    if station_bulk_upload_progress.first():
        bulk_upload_running = True
        percentage_station = (
            int(station_bulk_upload_progress.first().total_rows_count)
            * int(station_bulk_upload_progress.first().uploaded_rows_count)
            / 100
        )
        if percentage_station > 100:
            percentage_station = 85
    return [percentage_station, bulk_upload_running]


def cache_check():
    """station cache update"""
    if "cache_stations" in cache:
        # get results from cache
        stations = cache.get("cache_stations").order_by("station_id")
    else:
        stations = Stations.objects.filter(deleted=NO).order_by("station_id")
        cache.set("cache_stations", stations, timeout=CACHE_TTL)
    return stations


def export_errors():
    """station cache update"""
    errors_export_ready = False
    stations_error_records = BulkUploadErrorMessages.objects.filter(
        uploaded_for="stations",
        ready_to_export=YES,
    )
    if stations_error_records.first() is not None:
        errors = string_to_array_converter(
            stations_error_records.first().errors
        )
        if (
            len(errors[0]["errors"]) > 0
            or len(errors[1]["errors"]) > 0
            or len(errors[2]["errors"]) > 0
            or (len(errors) > 3 and len(errors[3]["errors"]) > 0)
        ):
            errors_export_ready = True
    return errors_export_ready


# This view will help to render list of stations.
# Here the function starting with @ is the 'decorator' used to restrict user.
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=SITES_CONST)
def station_list(request):
    """station list view"""
    try:
        # Database call to fetch all stations
        query_params_stations = ""
        for q_param in request.GET:
            if len(query_params_stations) == 0:
                query_params_stations = (
                    f"?{q_param}={request.GET.get(q_param)}"
                )
            else:
                query_params_stations += (
                    f"&{q_param}={request.GET.get(q_param)}"
                )
        stations = cache_check()
        # Declaration of all query params that helps in
        # filtering data and pagination.
        page_num = request.GET.get("page", 1)
        brand = request.GET.get("brand", None)
        station_type = request.GET.get("station_type", None)
        status = request.GET.get("status", None)
        search = request.GET.get("search", "")
        search = search_validator(search)
        do_export = request.GET.get("export", None)
        do_errors_export = request.GET.get("export_errors", None)
        stations_available = True
        # ordering parameters
        order_by_station = request.GET.get("order_by_station", None)
        # ordering of stations
        ordered_stations = order_by_function(
            stations, [{"station_id": ["order_by_station", order_by_station]}]
        )
        stations = ordered_stations["ordered_table"]
        # Here pagination_and_filter_func() is the common function to provide
        # filteration and pagination.
        filtered_data_stations = pagination_and_filter_func(
            page_num,
            stations,
            [
                {
                    "search": search,
                    "search_array": [
                        "station_id__contains",
                        "station_name__icontains",
                    ],
                },
                {"brand__exact": brand},
                {"status__exact": status},
                {"station_type__exact": station_type},
            ],
        )
        # Fetching list of brands from backend.
        brands = []
        station_brands = (
            Stations.objects.filter(deleted=NO).values("brand").distinct()
        )
        for i in station_brands:
            if i["brand"] != "nan":
                brands.append(i["brand"])
        # Here filter_url() function is used to filter
        # navbar elements so that we can  render only those navbar tabs
        # to which logged in user have access.
        url_data = filter_url(
            request.user.role_id.access_content.all(), SITES_CONST
        )
        station_types = []
        for i in station_site_locations_list()[-2]:
            station_types.append(i["station_type"])
        if len(filtered_data_stations["filtered_table_for_export"]) == 0:
            stations_available = False
        if do_export == YES:
            return station_list_export(filtered_data_stations)
        if do_errors_export == YES:
            return station_list_error_export()

        station_bulk_upload_progress = BulkUploadProgress.objects.filter(
            uploaded_for="stations",
            uploading_status="uploading",
        )
        (percentage, bulk_upload_running) = station_list_export_percentage(
            station_bulk_upload_progress
        )
        errors_export_ready = export_errors()

        context = {
            "stations": filtered_data_stations["filtered_table"],
            "bulk_upload_running": bulk_upload_running,
            "errors_export_ready": errors_export_ready,
            "percentage": percentage,
            "data_count": filtered_data_stations["data_count"],
            "first_data_number": filtered_data_stations["first_record_number"],
            "last_data_number": filtered_data_stations["last_record_number"],
            "brands": brands,
            "station_types": station_types,
            "status_list": ["Active", "Inactive", "Coming soon"],
            "prev_search": search,
            "prev_brand": brand,
            "prev_s_type": station_type,
            "prev_station_order": order_by_station,
            "prev_status": status,
            "query_params_str": query_params_stations,
            "update_url_param": filtered_data_stations["url"]
            + ordered_stations["url"],
            "pagination_num_list": filtered_data_stations["number_list"],
            "current_page": int(page_num),
            "prev": filtered_data_stations["prev_page"],
            "next": filtered_data_stations["next_page"],
            "data": url_data,
            "stations_available": stations_available,
        }

        return render(request, "stations/station_list.html", context)
    except COMMON_ERRORS:
        traceback.print_exc()
        return render(request, ERROR_TEMPLATE_URL)

@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=SITES_CONST)
def add_station(request):
    """add station view"""
    try:
        # Fetching services from a function which is
        # common for this sites module.
        query_params_add_station = ""
        for q_param in request.GET:
            if len(query_params_add_station) == 0:
                query_params_add_station = (
                    f"?{q_param}={request.GET.get(q_param)}"
                )
            else:
                query_params_add_station = (
                    f"&{q_param}={request.GET.get(q_param)}"
                )
        services = services_categorization_function()
        # Post request to add station details securely.
        if request.method == "POST":
            # Decoding JSON data from frontend.
            post_data_from_front_end = json.loads(
                request.POST["getdata"],
                object_hook=lambda d: SimpleNamespace(**d),
            )
            # Ensure ampeco_charge_point_id and ampeco_charge_point_name are present for each chargepoint
            for cp in getattr(post_data_from_front_end, 'chargepoints', []):
                if not hasattr(cp, 'ampeco_charge_point_id'):
                    cp.ampeco_charge_point_id = ''
                if not hasattr(cp, 'ampeco_charge_point_name'):
                    cp.ampeco_charge_point_name = ''
            # Ensure ampeco_site_id and ampeco_site_title are present
            if not hasattr(post_data_from_front_end, 'ampeco_site_id'):
                post_data_from_front_end.ampeco_site_id = ''
            if not hasattr(post_data_from_front_end, 'ampeco_site_title'):
                post_data_from_front_end.ampeco_site_title = ''
            # The following condition is used to
            # differentiate station according to station owner.
            station_create = None
            is_mfg = NO
            if post_data_from_front_end.station_type in IS_MFG_KEYS:
                is_mfg = YES
            # Station insert operation
            is_ev = NO
            if check_is_ev_status(post_data_from_front_end):
                is_ev = YES
            station_can_be_added = True

            if is_ev == YES and post_data_from_front_end.brand == "EV Power":
                if len(post_data_from_front_end.chargepoints) == 0:
                    station_can_be_added = False
            if not station_can_be_added:
                response_op = {
                    "status": False,
                    "message": NO_CHARGEPOINTS_PROVIDED_MESSAGE,
                    "url": reverse("station_list"),
                }
            back_office_data = {item.back_office: item.location_id for item in post_data_from_front_end.backoffice}
            try:
                # back_office_data = {item.back_office: item.location_id for item in post_data_from_front_end.backoffice}
                station_create,locations = create_single_station_func(
                    post_data_from_front_end, is_mfg, is_ev, request.user,back_office_data
                )
                
            except (DatabaseError, DataError) as error:
                station_exists = Stations.objects.filter(
                    station_id=post_data_from_front_end.station_id
                )
                if station_exists.first():
                    response_op = {
                        "status": False,
                        "message": "Station with this id already exists",
                        "url": reverse("station_list"),
                    }
                else:
                    response_op = {
                        "status": False,
                        "message": "Unable to create station",
                        "url": reverse("station_list"),
                    }
                return JsonResponse(response_op)
            # Insertion of Working hours details of station.
            back_office = list(back_office_data.keys())[0]
            if station_create:
                response_op = create_station(
                    request, station_create, post_data_from_front_end,locations,back_office
                )
                if response_op:
                    return JsonResponse(response_op)
                new_data = audit_data_formatter(SITES_CONST, station_create.id)
                add_audit_data(
                    request.user,
                    (
                        station_create.station_id
                        + ", "
                        + station_create.station_name
                    ),
                    f"{SITES_CONST}-{station_create.id}",
                    AUDIT_ADD_CONSTANT,
                    SITES_CONST,
                    new_data,
                    None,
                )
            # response to request
            response_op = {
                "status": True,
                "message": "ok",
                "url": reverse("station_list"),
            }
            remove_stations_cached_data()
            return JsonResponse(response_op)

        context = {
            "food": services[1],
            "retail": services[0],
            "amenities": services[2],
        }

        # Dumping data so that we can handle that on frontend.
        json_string = json.dumps(context)
        site_data = station_site_locations_list()
        # Here filter_url() function is used to filter navbar
        # elements so that we can render only those navbar tabs
        # to which logged in user have access.
        url_data = filter_url(
            request.user.role_id.access_content.all(), SITES_CONST
        )
        # backoffices = list(OCPICredentials.objects.filter(status = "Active").values_list('name', flat=True).distinct())
        available_back_offices = redis_connection.get(OCPI_CREDENTIALS_CACHE_KEY)
        back_office_names = list(json.loads(available_back_offices.decode('utf-8')).keys())
        if available_back_offices is None:
            back_office_names = OCPICredentials.objects.filter(status='Active').values_list('name', flat=True).distinct()
        return render(
            request,
            "stations/add_station.html",
            {
                "map_api_key": map_api_key,
                "data": url_data,
                "connector_speed_types": [
                    ["AC", "AC (0 - 22kWh)"],
                    ["Rapid", "Rapid (25 - 62.5 kWh)"],
                    ["Ultra-Rapid", "Ultra-Rapid (62.5 - 150 kWh)"],
                ],
                "plug_types": connector_types(),
                "operation_regions": site_data[0],
                "regions": site_data[1],
                "areas": site_data[2],
                "towns": site_data[3],
                "postal_codes": site_data[4],
                "brands": site_data[5],
                "owners": site_data[6],
                "tsjson": json_string,
                "query_params_str": query_params_add_station,
                "station_payment_terminals": [
                ["None", "None"],
                [PAYTER_PAYMENT_TERMINAL, PAYTER_PAYMENT_TERMINAL],
                ["Reciept Hero", WORLDLINE_PAYMENT_TERMINAL],
                [ADVAM_PAYMENT_TERMINAL, ADVAM_PAYMENT_TERMINAL],
                ],
                "backoffices_data":json.dumps(back_office_names),
            },
        )
    except COMMON_ERRORS:
        traceback.print_exc()
        return render(request, ERROR_TEMPLATE_URL)


def get_tariff_energy_amounts(tariff_ids):
    current_time = now().strftime('%H:%M')
    current_day = now().strftime('%A').upper() 
    
    result = {}
    tariff_data = tariff_ids

    for tariff in Tariffs.objects.filter(tariff_id__in=tariff_data):
        # Get element_ids linked to this tariff
        elements = TariffElements.objects.filter(id=tariff.id).values_list('id', flat=True)
        # Filter restrictions valid for current time and day
        valid_element_ids = TariffRestrictions.objects.filter(
            element_id__in=elements,
            day_of_week=current_day,
            start_time__lte=current_time,
            end_time__gte=current_time
        ).values_list('element_id', flat=True)
        # Get components of type 'energy' for valid elements
        energy_components = TariffComponents.objects.filter(
            element_id__in=valid_element_ids,
            type='ENERGY'
        )
        en = list(energy_components.values())

        total_amount = sum(comp['price'] for comp in en)
        result[tariff.tariff_id] = total_amount
        

    return result


# This view will be used to fetched details of station.
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=SITES_CONST)
def view_station(request, station_pk):
    """view station view"""
    try:
        query_params_view_str = ""
        for q_param in request.GET:
            if len(query_params_view_str) == 0:
                query_params_view_str = (
                    f"?{q_param}={request.GET.get(q_param)}"
                )
            else:
                query_params_view_str += (
                    f"&{q_param}={request.GET.get(q_param)}"
                )
        # Fetching services from a function which is common
        # for this sites module
        (
            retails_services,
            food_to_go_services,
            amenities_services,
        ) = services_categorization_function()
        # Fetching required station with the help of 'station_pk' parameter.
        station = Stations.objects.get(id=station_pk)

        # If station is deleted to disable access using station url.
        if station.deleted == YES:
            return redirect("station_list")
        # Fetching working hours details
        working_hours = StationWorkingHours.objects.filter(station_id=station_pk).first()

        # Fetching Chargepoints
        chargepoints = ChargePoint.objects.filter(
            station_id=station_pk, deleted=NO
        ).order_by("device_id")

        # location_ids = list(station.ocpi_locations.values())
        locations = OCPILocation.objects.filter(station_mapping_id = station, station_mapping_id__deleted = "No")
        back_offices_data = {
            get_location_backoffice(location):location.location_id
            for location in locations
        }
        
        evses = OCPIEVSE.objects.filter(
            chargepoint_mapping_id__in = chargepoints
        )
        tariff_ids = []
        
        connectors_data = OCPIConnector.objects.filter(evse_id__in=evses)

        country_code_query = OCPICredentials.objects.filter(
            name=OuterRef('back_office'),
            status = 'Active'
        ).select_related('to_role').values('to_role__country_code')[:1]

        party_id_query = OCPICredentials.objects.filter(
            name=OuterRef('back_office'),
            status = 'Active'
        ).select_related('to_role').values('to_role__party_id')[:1]

        # connectors = StationConnector.objects.filter(
        #     ~Q(charge_point_id=None), station_id=station_pk, deleted=NO
        # ).prefetch_related('station_connectors').order_by("connector_id").annotate(
        #     country_code=Subquery(country_code_query),
        #     party_id=Subquery(party_id_query),
        # )
        
        ocpi_connector_query = OCPIConnector.objects.filter(
            connector_mapping_id=OuterRef('id'),
        ).values('connector_id')

        evse_query = OCPIConnector.objects.filter(
            connector_mapping_id=OuterRef('id'),
        ).values('evse_id__uid')
        
        connectors = StationConnector.objects.filter(
            ~Q(charge_point_id=None), station_id=station_pk, deleted=NO
        ).prefetch_related('station_connectors').order_by("connector_id").annotate(
            country_code=Subquery(country_code_query),
            party_id=Subquery(party_id_query),
        )
        
        chargepoint_list = [
            [
                chargepoint,
                [
                    connector
                    for connector in connectors
                    if connector.charge_point_id.id == chargepoint.id 
                ],
            ]
            for chargepoint in chargepoints 
        ]

        connector_tariff_mapping = {}
        connector_tariff_ids = []

        seen = set()
        for connector in connectors_data:
            for tariff in connector.tariff_ids:
                if tariff not in seen:
                    seen.add(tariff)
                    connector_tariff_ids.append(tariff)


        tariff_data = TariffComponents.objects.filter(element_id_id__tariff_id_id__tariff_id__in = connector_tariff_ids, type = 'ENERGY').values_list('element_id_id__tariff_id_id__tariff_id', 'price')

        # Convert to dict
        tariff_price_map = {tariff_id: float(price) for tariff_id, price in tariff_data if tariff_id is not None and price is not None}

        # fetching station images
        images = StationImages.objects.filter(station_id=station_pk)

        # Fetching amenities available on station.
        amenities_ids = [
            service.service_id.id
            for service in StationServices.objects.filter(
                station_id=station_pk, service_name="Amenity", deleted=NO
            )
            if service.service_id
        ]
        # Fetching retail shops available on station.
        retail_ids = [
            service.service_id.id
            for service in StationServices.objects.filter(
                station_id=station_pk, service_name="Retail", deleted=NO
            )
            if service.service_id
        ]

        # Fetching food services available on station.
        foods_ids = [
            service.service_id.id
            for service in StationServices.objects.filter(
                station_id=station_pk, service_name="Food To Go", deleted=NO
            )
            if service.service_id
        ]

        # Matching station services with configuration services
        # to filter station services.
        station_amenities = [
            service
            for service in amenities_services
            if service["id"] in amenities_ids
        ]
        station_retails = [
            service
            for service in retails_services
            if service["id"] in retail_ids
        ]
        station_food_services = [
            service
            for service in food_to_go_services
            if service["id"] in foods_ids
        ]
        tariff_ids = []
        
        try:
            for connector in connectors:
                if connector.tariff_ids is not None:
                    ids = string_to_array_converter(connector.tariff_ids)
                    tariff_ids.extend(ids)
            if len(tariff_ids) > 0:
                tariff_data = get_tariff_energy_amounts(tariff_ids)
        
        except Exception as e:
            tariff_data = {}
            print(e)
        promotion = Promotions.objects.filter(
            ~Q(image=None),
            station_available_promotions__station_id=station,
            deleted=NO,
            station_available_promotions__deleted=NO,
            status="Active",
            end_date__gte=timezone.localtime(timezone.now()),
            start_date__lte=timezone.localtime(timezone.now()),
        ).distinct()
        promotions = [
            {
                "title": prom.promotion_title,
                "image": prom.get_promotion_image(),
            }
            for prom in promotion
        ]

        valeting_terminals = ValetingTerminals.objects.filter(
            station_id=station_pk, deleted=NO
        )
        
        #Fetching Valeting Machines
        valeting_machines = ValetingMachine.objects.filter(
            station_id=station_pk, deleted=False
        )

        valeting_terminals = [
            {
                "payter_serial_number": valating_terminal.payter_serial_number,
                "amenities": string_to_array_converter(
                    valating_terminal.amenities
                ),
                "status": valating_terminal.status,
            }
            for valating_terminal in valeting_terminals
        ]

        valeting_machines = [
            {
                "db_id": machine.id,
                "machine_id": machine.machine_id,
                "machine_name": machine.machine_name,
                "machine_number": machine.machine_number,
                "is_active": machine.is_active,
            }
            for machine in valeting_machines
        ]

        # Here filter_url() function is used to filter navbar
        # elements so that we can render only those navbar tabs
        # to which logged in user have access.
        url_data = filter_url(
            request.user.role_id.access_content.all(), SITES_CONST
        )
        station_terminals = ", ".join(string_to_array_converter(station.payment_terminal))
        
        if "Worldline" in station_terminals:
            station_terminals = station_terminals.replace("Worldline", "Receipt Hero")
        context = {
            "connector_tariff_mapping":connector_tariff_mapping,
            "tariff_data":tariff_data,
            "blob_root": AZURE_BLOB_STORAGE_URL,
            "station_promotions": promotions,
            "station": station,
            "working_hours": working_hours,
            "chargepoints": chargepoint_list,#connectors_list if connectors_list else 
            "images": images,
            "foods": station_food_services,
            "retail": station_retails,
            "amenities": station_amenities,
            "data": url_data,
            "query_params_str": query_params_view_str,
            "valeting_terminals": valeting_terminals,
            "valeting_machines": valeting_machines,
            "station_terminal": string_to_array_converter(station.payment_terminal),
            "station_terminals": station_terminals,
            "tariffs":tariff_price_map,
            "back_offices_data":back_offices_data

        }
        return render(request, "stations/view_station.html", context)
    except COMMON_ERRORS:
        traceback.print_exc()
        return render(request, ERROR_TEMPLATE_URL)


def station_fetch_details(station_pk):
    """update station object"""
    # Fetching services from a function which is
    # common for this sites module
    (
        retails_services,
        food_to_go_services,
        amenities_services,
    ) = services_categorization_function()
    # Fetching required station with the help of 'station_pk' parameter.
    station = Stations.objects.get(id=station_pk)
    # redirecting user if station is already deleted.
    if station.deleted == YES:
        return redirect("station_list")

    station_object = Stations.objects.filter(id__exact=station_pk).values(
        "station_id",
        "station_name",
        "station_address1",
        "station_address2",
        "station_address3",
        "town",
        "post_code",
        "country",
        "brand",
        "owner",
        "latitude",
        "longitude",
        "email",
        "phone",
        "status",
        "station_type",
        "site_title",
        "operation_region",
        "region",
        "regional_manager",
        "area",
        "area_regional_manager",
        "site_id",
        "valeting",
        "payment_terminal",
        "receipt_hero_site_name",
        "overstay_fee",
        "valeting_site_id",
        "ocpi_locations",
        "ampeco_site_id",
        "ampeco_site_title"
    )
    station_data = [station_object.first()]
    working_hours = StationWorkingHours.objects.get(station_id=station_pk)
    # Fetching working hours of station.
    working_hours_object = StationWorkingHours.objects.filter(
        station_id=station
    ).values("monday_friday", "saturday", "sunday")
    working_hours_data = [working_hours_object.first()]
    # Fetching chargepoints available on station.
    chargepoints = (
        ChargePoint.objects.filter(station_id=station_pk, deleted=NO)
        .order_by("device_id")
        .values(
            "id",
            "charger_point_id",
            "charger_point_name",
            "charger_point_status",
            "back_office",
            "device_id",
            "payter_terminal_id",
            "ampeco_charge_point_id",
            "ampeco_charge_point_name",
            "worldline_terminal_id",
        )
    )
    # Fetching conectors available on station for devices.

    
    chargepoint_ids = list(chargepoints.values_list('id', flat=True))
    connectors = StationConnector.objects.prefetch_related(
        'station_connectors',
    ).filter(
        deleted=NO,
        station_id=station_pk,
        charge_point_id_id__in = chargepoint_ids
    ).order_by('connector_id').values(
        "id",
        "charge_point_id",
        "connector_id",
        "connector_name",
        "plug_type_name",
        "connector_type",
        "status",
        "max_charge_rate",
        "connector_sorting_order",
        "tariff_amount",
        "tariff_currency",
        "current_status",
        "back_office",
        "station_connectors__connector_id",      
        "station_connectors__evse_id__uid",         
    )        

    # Making an object (dictionary so that we can render
    # chargepoints and connectors on frontend in forloop)
    chargepoint_list = [
        [
            chargepoint,
            [
                connector
                for connector in connectors
                if connector["charge_point_id"] == chargepoint["id"]
            ],
        ]
        for chargepoint in chargepoints
    ]
    # Fetching station images
    img_list = [
        {"image": image.get_image()}
        for image in StationImages.objects.filter(station_id=station_pk)
    ]
    # Fetching amenities available on station.
    amenities_ids = [
        service.service_id.id
        for service in StationServices.objects.filter(
            station_id=station_pk, service_name="Amenity", deleted=NO
        )
        if service.service_id
    ]
    # Fetching retail shops available on station.
    retail_ids = [
        service.service_id.id
        for service in StationServices.objects.filter(
            station_id=station_pk, service_name="Retail", deleted=NO
        )
        if service.service_id
    ]
    # Fetching food services available on station.
    foods_ids = [
        service.service_id.id
        for service in StationServices.objects.filter(
            station_id=station_pk, service_name="Food To Go", deleted=NO
        )
        if service.service_id
    ]
    # Matching station services with configuration services
    # to filter station services.
    station_amenities = [
        service
        for service in amenities_services
        if service["id"] in amenities_ids
    ]
    station_retails = [
        service for service in retails_services if service["id"] in retail_ids
    ]
    station_food_services = [
        service
        for service in food_to_go_services
        if service["id"] in foods_ids
    ]
    valeting_terminals = ValetingTerminals.objects.filter(
        station_id=station_pk, deleted=NO
    )
    
    #Fetching Valeting Machines
    valeting_machines = ValetingMachine.objects.filter(
        station_id=station_pk, deleted=False
    )

    valeting_terminals = [
        {
            "db_id": valating_terminal.id,
            "payter_serial_number": valating_terminal.payter_serial_number,
            "amenities": string_to_array_converter(
                valating_terminal.amenities
            ),
            "status": valating_terminal.status,
            "deleted": valating_terminal.deleted == YES,
        }
        for valating_terminal in valeting_terminals
    ]
    valeting_machines = [
        {
            "db_id": machine.id,
            "machine_id": machine.machine_id,
            "machine_name": machine.machine_name,
            "machine_number": machine.machine_number,
            "status": "Active" if machine.is_active else "Inactive",
        }
        for machine in valeting_machines
    ]
    return [
        station,
        station_data,
        working_hours,
        working_hours_data,
        chargepoint_list,
        img_list,
        station_amenities,
        station_retails,
        station_food_services,
        amenities_services,
        retails_services,
        food_to_go_services,
        valeting_terminals,
        valeting_machines,
    ]


# This view will help to edit the station details.
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=SITES_CONST)
def update_station(request, station_pk):
    """update station view"""
    try:
        query_params_update_str = ""
        for q_param in request.GET:
            if len(query_params_update_str) == 0:
                query_params_update_str = (
                    f"?{q_param}={request.GET.get(q_param)}"
                )
            else:
                query_params_update_str += (
                    f"&{q_param}={request.GET.get(q_param)}"
                )
        # Fetching station data in values to prerender station_data.
        (
            station,
            station_data,
            working_hours,
            working_hours_data,
            chargepoint_list,
            img_list,
            station_amenities,
            station_retails,
            station_food_services,
            amenities_services,
            retails_services,
            food_to_go_services,
            valeting_terminals,
            valeting_machines,
        ) = station_fetch_details(station_pk)
        # Post request to update data securely.
        if request.method == "POST":
            response_op = update_database_stations(
                request,
                station_pk,
                station,
                amenities_services,
                retails_services,
                food_to_go_services,
                query_params_update_str,
            )
            return response_op
        json_data_stations = {
            "station_json": station_data,
            "working_hours_json": working_hours_data,
            "chargepoints": chargepoint_list,
            "station_images": img_list,
            "foods": station_food_services,
            "retail_station": station_retails,
            "amenities_station": station_amenities,
            "food": food_to_go_services,
            "retail": retails_services,
            "amenities": amenities_services,
            "valeting_terminals": valeting_terminals,
            "valeting_machines": valeting_machines,
        }
        # Dumping data in JSON so that we can handle that in frontend.
        json_string = json.dumps(json_data_stations)
        site_data = station_site_locations_list()
        # Here filter_url() function is used to filter navbar
        # elements so that we can render only those navbar tabs
        # to which logged in user have access.
        available_back_offices = redis_connection.get(OCPI_CREDENTIALS_CACHE_KEY)
        back_office_names = list(json.loads(available_back_offices.decode('utf-8')).keys())
        if available_back_offices is None:
            back_office_names = OCPICredentials.objects.filter(status='Active').values_list('name', flat=True)
        url_data = filter_url(
            request.user.role_id.access_content.all(), SITES_CONST
        )
        
        locations = OCPILocation.objects.filter(
            station_mapping_id = station
        )
        print("[DEBUG] locations: ", locations)
        location_object = {}
        for location in locations:
            back_office = get_location_backoffice(location)

            if back_office is not None:
                location_object[back_office]=location.location_id
        context = {
            "map_api_key": map_api_key,
            "connector_speed_types": [
                ["AC", "AC (0 - 22kWh)"],
                ["Rapid", "Rapid (25 - 62.5 kWh)"],
                ["Ultra-Rapid", "Ultra-Rapid (62.5 - 150 kWh)"],
            ],
            "plug_types": connector_types(),
            "station": station,
            "working_hours": working_hours,
            "tsjson": json_string,
            "station_type": [
                "MFG EV",
                "MFG Forecourt",
                "Non MFG",
                "MFG EV plus Forecourt",
            ],
            "valeting_status": [YES, NO],
            "data": url_data,
            "operation_regions": site_data[0],
            "regions": site_data[1],
            "areas": site_data[2],
            "towns": site_data[3],
            "postal_codes": site_data[4],
            "brands": site_data[5],
            "owners": site_data[6],
            "countries": ["England", "Scotland", "Wales", "Jersey"],
            "status_list": ["Active", "Inactive", "Coming soon"],
            "query_params_str": query_params_update_str,
            "station_payment_terminals": [
                ["None", "None"],
                [PAYTER_PAYMENT_TERMINAL, PAYTER_PAYMENT_TERMINAL],
                ["Reciept Hero", WORLDLINE_PAYMENT_TERMINAL],
                [ADVAM_PAYMENT_TERMINAL, ADVAM_PAYMENT_TERMINAL],
            ],
            "station_terminals": string_to_array_converter(station.payment_terminal),
            "back_offices_data":json.dumps(location_object),
            "back_offices_count":len(location_object),
            "available_back_offices":json.dumps(back_office_names),
            "total_back_offices":json.dumps(back_office_names),
        }
        return render(request, "stations/update_station.html", context)
    except COMMON_ERRORS:
        traceback.print_exc()
        return render(request, ERROR_TEMPLATE_URL)


# This view will help to delete the particular station
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=SITES_CONST)
def delete_station(request, station_pk):
    """delete station view"""
    try:
        # For deletion we have used "Soft delete".
        # Fetching required station with the help of 'station_pk'
        # parameter for deletion.
        stations = Stations.objects.filter(id=station_pk)
        station = stations.first()
        Stations.objects.filter(id=station_pk).update(deleted=YES)

        #clear ocpi mappings
        locations = OCPILocation.objects.filter(station_mapping_id = station)
        evses = OCPIEVSE.objects.filter(location_id__in = locations)
        OCPIConnector.objects.filter(evse_id__in = evses).update(connector_mapping_id = None)
        evses.update(chargepoint_mapping_id = None)
        locations.update(station_mapping_id = None)

        StationWorkingHours.objects.filter(station_id_id=station_pk).update(
            deleted=YES,
            updated_date=timezone.localtime(timezone.now()),
            updated_by=request.user.full_name,
        )
        ChargePoint.objects.filter(station_id_id=station_pk).update(
            deleted=YES,
            updated_date=timezone.localtime(timezone.now()),
            updated_by=request.user.full_name,
        )
        StationConnector.objects.filter(station_id_id=station_pk).update(
            deleted=YES,
            updated_date=timezone.localtime(timezone.now()),
            updated_by=request.user.full_name,
        )
        StationImages.objects.filter(station_id_id=station_pk).update(
            deleted=YES,
            updated_date=timezone.localtime(timezone.now()),
            updated_by=request.user.full_name,
        )
        StationServices.objects.filter(station_id_id=station_pk).update(
            deleted=YES,
            updated_date=timezone.localtime(timezone.now()),
            updated_by=request.user.full_name,
        )
        ValetingTerminals.objects.filter(station_id=station_pk).update(
            deleted=YES,
            updated_date=timezone.localtime(timezone.now()),
            updated_by=request.user.full_name,
        )
        PromotionsAvailableOn.objects.filter(station_id_id=station_pk).update(
            deleted=YES,
            updated_date=timezone.localtime(timezone.now()),
            updated_by=request.user.full_name,
        )
        LoyaltyAvailableOn.objects.filter(station_id_id=station_pk).update(
            deleted=YES,
            updated_date=timezone.localtime(timezone.now()),
            updated_by=request.user.full_name,
        )
        prev_audit_data = AuditTrail.objects.filter(
            data_db_id=f"{SITES_CONST}-{station_pk}"
        ).last()
        prev_locations = Stations.objects.filter(station_id__startswith = station.station_id)
        updated_station_id = station.station_id+"_OLD_"+str(prev_locations.count())
        stations.update(station_id = updated_station_id)
        if prev_audit_data and prev_audit_data.new_data:
            prev_audit_data = prev_audit_data.new_data
            add_audit_data(
                request.user,
                f"{station.station_id}, {station.station_name}",
                f"{SITES_CONST}-{station_pk}",
                AUDIT_DELETE_CONSTANT,
                SITES_CONST,
                None,
                prev_audit_data,
            )
        # redirecting user on successful deletion
        remove_stations_cached_data()
        return redirect("station_list")
    except COMMON_ERRORS:
        traceback.print_exc()
        return render(request, ERROR_TEMPLATE_URL)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
def delete_station_image(request, station_image_pk):
    """delete station image view"""
    if request.method == "POST":
        post_data_from_front_end = json.loads(
            request.POST["getdata"], object_hook=lambda d: SimpleNamespace(**d)
        )
        for url in post_data_from_front_end.url:
            split = url.split(AZURE_BLOB_STORAGE_URL)
            station_image = StationImages.objects.filter(
                station_id=station_image_pk, image=split[1]
            )
            dl_id = station_image.first().id
            station_image.first().image.delete()
            StationImages.objects.filter(id=dl_id).delete()
        response_op = {"status": 1, "message": "ok"}
        remove_stations_cached_data()
        return JsonResponse(response_op)
    return JsonResponse("Method")


def fetch_ampeco_api(url, headers):
    """Fetch data from Ampeco API and return the 'data' array or None on error."""
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code == 200:
            return resp.json().get('data', [])
        else:
            return None
    except Exception as e:
        return None


def update_station_titles_from_ampeco(ampeco_data):
    """Update ampeco_site_title for all stations with a matching ampeco_site_id."""
    updated_stations = []
    for loc in ampeco_data:
        ampeco_id = str(loc.get('id'))
        translation = loc.get('name', [{}])[0].get('translation')
        if ampeco_id and translation:
            qs = Stations.objects.filter(ampeco_site_id=ampeco_id)
            count = qs.update(ampeco_site_title=translation)
            if count > 0:
                updated_stations.append({
                    'ampeco_site_id': ampeco_id,
                    'new_title': translation,
                    'stations_updated': count
                })
    return updated_stations


def update_charge_point_names_from_ampeco(cp_data):
    """Update ampeco_charge_point_name for all charge points with a matching ampeco_charge_point_id."""
    updated_charge_points = []
    for cp in cp_data:
        ampeco_cp_id = str(cp.get('id'))
        name = cp.get('name')
        if ampeco_cp_id and name:
            qs = ChargePoint.objects.filter(ampeco_charge_point_id=ampeco_cp_id)
            count = qs.update(ampeco_charge_point_name=name)
            if count > 0:
                updated_charge_points.append({
                    'ampeco_charge_point_id': ampeco_cp_id,
                    'new_name': name,
                    'charge_points_updated': count
                })
    return updated_charge_points


@require_http_methods([POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=SITES_CONST)
@csrf_exempt
def map_ampeco_site_titles(request):
    """
    Endpoint: /admin/stations/map_ampeco_site_titles/
    Updates ampeco_site_title for all stations with a non-null ampeco_site_id by fetching from Ampeco API.
    Also updates ampeco_charge_point_name for all charge points with a non-null ampeco_charge_point_id.
    Returns a structured JSON response with details for both updates.
    """
    AMPECO_BASE_URL = config("DJANGO_APP_AMPECO_BASE_URL")
    AMPECO_TOKEN = config("DJANGO_APP_AMPECO_TOKEN")
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {AMPECO_TOKEN}"
    }
    # Fetch and update stations
    ampeco_locations_url = AMPECO_BASE_URL + AMPECO_LOCATIONS_ENDPOINT
    ampeco_data = fetch_ampeco_api(ampeco_locations_url, headers)
    if ampeco_data is None:
        return JsonResponse({'error': 'Failed to fetch Ampeco locations data'}, status=500)
    updated_stations = update_station_titles_from_ampeco(ampeco_data)

    # Fetch and update charge points
    ampeco_cp_url = AMPECO_BASE_URL + AMPECO_CHARGEPOINTS_ENDPOINT
    cp_data = fetch_ampeco_api(ampeco_cp_url, headers)
    if cp_data is None:
        return JsonResponse({'error': 'Failed to fetch Ampeco charge points data'}, status=500)
    updated_charge_points = update_charge_point_names_from_ampeco(cp_data)

    return JsonResponse({
        'stations': {'updated': updated_stations, 'count': len(updated_stations)},
        'charge_points': {'updated': updated_charge_points, 'count': len(updated_charge_points)}
    })

@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=SITES_CONST)
def validate_location(request):
    """validate locations view"""
    try:
        if request.method == "POST":
            
            charge_points = request.POST.get("charge_points", [])# json.loads(request.POST["charge_points"])
            charge_points = string_to_array_converter(charge_points)
            back_office = request.POST.get("back_office", [])
            back_office = back_office.upper()
            # charge_points = filter(
            # lambda charge_point: charge_point.deleted is False,
            # request.chargepoints,
            # )
            is_ev_site = bool(
                (
                    request.POST["station_type"] == "Non MFG"
                    or request.POST["station_type"] in IS_EV_KEYS
                )
                and len(charge_points) > 0
            )
            
            valid_mapping = True
            if is_ev_site:
                locations_data = json.loads(request.POST["location_data"])["location_mapping_arr"]
                country_code,party_id = get_back_office_data(back_office)
                if len(locations_data) == 0:
                    return JsonResponse({"valid": False},status=status.HTTP_400_BAD_REQUEST)
                for location in locations_data:
                    location_obj = OCPILocation.objects.filter(
                            location_id = location["location_id"],
                            country_code = country_code,
                            party_id = party_id
                        )
                    if location_obj.first() is None:
                        return JsonResponse({"valid": False},status=status.HTTP_400_BAD_REQUEST)
                    if location["evse_uid"] != '' and location["evse_uid"] is not None:
                        # location_obj = OCPILocation.objects.filter(
                        #     location_id = location["location_id"],
                        #     country_code = country_code,
                        #     party_id = party_id
                        # )
                        valid_mapping = OCPIConnector.objects.filter(
                            connector_id = location["connector_id"],
                            evse_id__uid = location["evse_uid"],
                            evse_id__location_id = location_obj.first()
                            ).exists()
                        if not valid_mapping:
                            break
            if valid_mapping:
                return JsonResponse({"valid": valid_mapping},status=status.HTTP_200_OK)
            return JsonResponse({"valid": valid_mapping},status=status.HTTP_400_BAD_REQUEST)
            
    except COMMON_ERRORS:
        return JsonResponse({"valid": False},status=status.HTTP_400_BAD_REQUEST)
    
#Rest API

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import AddStationRequestSerializer, DeleteStationRequestSerializer, StationListRequestSerializer, StationListResponseSerializer, UpdateStationRequestSerializer, ViewStationRequestSerializer, ViewStationResponseSerializer
from .services import add_station_service, delete_station_service, get_station_details_service, get_station_list, update_station_data
from sharedServices.constants import ConstantMessage
import traceback
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import UploadSheetRequestSerializer
from .services import upload_sheet_service


class AddStationAPIView(APIView):
    """
    API view for adding a station.
    All business logic handled in service layer.
    """

    def post(self, request):
        try:
            serializer = AddStationRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return api_response(
                    message=serializer.errors,
                    status=False,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error=serializer.errors
                )

            result = add_station_service(serializer.validated_data, request.user)

            return api_response(
                message=result.get("message"),
                status=result.get("status"),
                status_code=status.HTTP_200_OK if result.get("status") else status.HTTP_400_BAD_REQUEST,
                data=result.get("data", None)
            )
        except Exception:
            return api_response(
                message=ConstantMessage.SOMETHING_WENT_WRONG,
                status=False,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error=traceback.format_exc()
            )
        

class UploadSheetAPIView(APIView):
    """
    API view for bulk station upload from Excel sheet.
    Handles multiple tabs and starts asynchronous processing.
    """
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            serializer = UploadSheetRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return api_response(
                    message=serializer.errors,
                    status=False,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error=serializer.errors
                )

            file_obj = serializer.validated_data.get("file")
            result = upload_sheet_service(file_obj, request.user)

            return api_response(
                message=result.get("message"),
                status=result.get("status"),
                status_code=status.HTTP_200_OK if result.get("status") else status.HTTP_400_BAD_REQUEST,
                data=result.get("data", None)
            )

        except Exception:
            return api_response(
                message=ConstantMessage.SOMETHING_WENT_WRONG,
                status=False,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error=traceback.format_exc()
            )
        


class StationList(APIView):
    """API view to retrieve the list of stations with filters and pagination."""

    def get(self, request):
        """Handle GET request to retrieve station list."""
        try:
            # Step 1: Validate query parameters
            serializer = StationListRequestSerializer(data=request.query_params)
            if not serializer.is_valid():
                return api_response(
                    message=serializer.errors,
                    status=False,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error=serializer.errors
                )

            # Step 2: Fetch filtered data from service
            data_list = get_station_list(serializer.validated_data)

            # # Step 3: Paginate and serialize
            result = paginate_and_serialize(
                request, data_list, StationListResponseSerializer
            )

            # Step 4: Return standardized API response
            return api_response(
                status_code=status.HTTP_200_OK,
                message=ConstantMessage.STATION_LIST_FETCH_SUCCESS,
                data=result,
            )

        except Exception as e:
            return api_response(
                message=ConstantMessage.SOMETHING_WENT_WRONG,
                status=False,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error=traceback.format_exc()
            )


class ViewStation(APIView):
    """API view to fetch full details of a specific station."""

    def get(self, request, station_pk):
        """Retrieve station details by ID."""
        try:
            # Validate path + query params
            serializer = ViewStationRequestSerializer(
                data={"station_pk": station_pk, **request.query_params}
            )
            if not serializer.is_valid():
                return api_response(
                    message=serializer.errors,
                    status=False,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error=serializer.errors
                )

            station_data = get_station_details_service(serializer.validated_data)

            if not station_data:
                return api_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=ConstantMessage.STATION_NOT_FOUND,
                )

            response_serializer = ViewStationResponseSerializer(station_data)
            return api_response(
                status_code=status.HTTP_200_OK,
                message=ConstantMessage.STATION_DATA_RETRIVED_SUCCESS,
                data=response_serializer.data,
            )

        except Exception as e:
            return api_response(
                message=ConstantMessage.SOMETHING_WENT_WRONG,
                status=False,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error=traceback.format_exc()
            )
    
    def put(self, request, station_pk):
        """Update station details by ID."""
        try:
            # Validate input
            serializer = UpdateStationRequestSerializer(
                data={"station_pk": station_pk, **request.data}
            )
            if not serializer.is_valid():
                return api_response(
                    message=serializer.errors,
                    status=False,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error=serializer.errors
                )

            # Fetch existing station details
            result = get_station_details_service(serializer.validated_data)
            if not result or "station_obj" not in result:
                return api_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=ConstantMessage.STATION_NOT_FOUND
                )

            station_obj = result["station_obj"]

            update_station_data(
                request,
                station_pk,
                station_obj,
                result["data"]["amenities"],
                result["data"]["retail"],
                result["data"]["food"],
                request.META.get('QUERY_STRING', '')
            )


            return api_response(
                status_code=status.HTTP_200_OK,
                message=ConstantMessage.STATION_UPDATED_SUCCESS,
            )

        except Exception as e:
            return api_response(
                message=ConstantMessage.SOMETHING_WENT_WRONG,
                status=False,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error=traceback.format_exc()
            )
        
    def delete(self, request, station_pk):
        """Internal method to perform deletion."""
        try:
            serializer = DeleteStationRequestSerializer(
                data={"station_pk": station_pk, **request.query_params}
            )
            if not serializer.is_valid():
                return api_response(
                    message=serializer.errors,
                    status=False,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error=serializer.errors
                )

            validated_data = serializer.validated_data

            delete_station_service(station_pk=validated_data["station_pk"], user=request.user)

            return api_response(
                status_code=status.HTTP_200_OK,
                message=ConstantMessage.STATION_DELETED_SUCCESS
            )

        except Exception:
            return api_response(
                message=ConstantMessage.SOMETHING_WENT_WRONG,
                status=False,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error=traceback.format_exc()
            )