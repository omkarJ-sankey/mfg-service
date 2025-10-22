"""stations apis"""
# Date - 04/11/2024


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on APIs
#                       related to station finder data.
#   Name            - Station Finder APIs
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 19/06/2025


# These are all the imports that we are exporting from
# different module's from project or library.
import json
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Q
from django.utils import timezone
from django.utils.decorators import method_decorator
import traceback
from itertools import repeat

from decouple import config

from rest_framework.permissions import AllowAny
from rest_framework.authentication import BaseAuthentication

from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
)
from sharedServices.model_files.ocpi_sessions_models import OCPISessions
from sharedServices.model_files.station_models import Stations
from sharedServices.model_files.ocpi_credentials_models import OCPICredentials
from django.forms.models import model_to_dict
from concurrent.futures import ProcessPoolExecutor
from passlib.hash import django_pbkdf2_sha256 as handler
from .decorators import token_required

# pylint:disable=import-error
from sharedServices.constants import (
    NO,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    ACTIVE,
    EMPTY_CACHE_CHECK,
    OCPI_LOCATIONS_KEY,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    NO,
    DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    NO,
    SECRET_KEY_IN_VALID,
    SECRET_KEY_NOT_PROVIDED,
    OCPI_CREDENTIALS_CACHE_KEY,
    SYNC_LOCATION_ENDPOINT
)
from sharedServices.model_files.app_user_models import (
    UserSelectedStationFinderFilters
)
from sharedServices.model_files.station_models import (
    StationConnector,
    StationServices,
)

from sharedServices.model_files.config_models import (
    ConnectorConfiguration,
    ServiceConfiguration,
    BaseConfigurations
)

from sharedServices.model_files.charging_session_models import (
    ChargingSession
)

from sharedServices.common import (
    array_to_string_converter,
    redis_connection,
    string_to_array_converter,
    handle_concurrent_user_login,
    get_node_secret,
    remove_all_cache
)

from sharedServices.stations_helper_functions import update_stations_cache
from sharedServices.driivz_api_gateway_functions import driivz_fetch_dynamic_tariff_details
from backendServices.stations.stations_helper_function import emsp_cron_function
from backendServices.backend_app_constants import MULTIPLE_LOGIN, UNAUTHORIZED
# This API will return all the data to make filter operation
# on station list data station finder


class StationFinderViewSetV4(APIView):
    """station finder viewset"""

    # Permission classes are used to restrict the user
    permission_classes = [permissions.AllowAny]

    def get(self, station_finder_request):
        """get method to fetch station finder stations"""
        try:
            data = redis_connection.get("station_finder_cache_data_updated_v4")
            station_finder_data = []
            if data and data.decode("utf-8") != EMPTY_CACHE_CHECK:
                station_finder_data = string_to_array_converter(
                    data.decode("utf-8")
                )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Fetched stations.",
                    "data": station_finder_data[0],
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Station Finder ViewSet API failed for user -> \
                    {station_finder_request.user.id} due to exception -> \
                        {exception}"
            )
            return API_ERROR_OBJECT


class FilterDataListV4(APIView):
    """This class view returns list of data we can use for
    filtering stations data"""

    @classmethod
    def get(cls, _):
        """get filter list"""
        try:
            data = redis_connection.get("station_finder_filter_list_v4")
            if data and data.decode("utf-8") != "null":
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "Successfully loaded filter data.",
                        "data": string_to_array_converter(
                            data.decode("utf-8")
                        )[0]
                    }
                )
            station_filters_charger_power_range_values = BaseConfigurations.objects.filter(
                base_configuration_key="station_filters_charger_power_range_values"
            )
            station_filters_charger_power_range_values = (
                json.loads(
                    station_filters_charger_power_range_values.first().base_configuration_value
                )
                if station_filters_charger_power_range_values.first() is not None else []
            )
            filer_data = {
                "brands": [
                    {
                        "service": shop.service_name,
                        "image": shop.get_image_path(),
                    }
                    for shop in ServiceConfiguration.objects.filter(
                        ~Q(image_path=None, service_type='Amenity'),
                        id__in=StationServices.objects.filter(deleted=NO)
                        .values_list("service_id_id", flat=True)
                        .distinct(),
                    )
                ],
                "connectors": [
                    {
                        "connector_type": i.connector_plug_type,
                        "image": i.get_image_path(),
                    } for i in ConnectorConfiguration.objects.filter(
                        connector_plug_type__in=StationConnector.objects.filter(
                            deleted=NO, status=ACTIVE
                        )
                        .values_list("plug_type_name", flat=True)
                        .distinct()
                    ).order_by("sorting_order")
                ],
                "station_filters_charger_power_range_values": (
                    station_filters_charger_power_range_values
                ),
            }
            redis_connection.set(
                "station_finder_filter_list_v4",
                array_to_string_converter([filer_data]),
            )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Successfully loaded filter data.",
                    "data": filer_data
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Filter Data List API failed due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


class SaveUserStationFinderSelectedFilterOptions(APIView):
    """This class view saves user selected station finder filter options"""

    @classmethod
    def get(cls, get_user_selected_filter_options):
        """save user selected filter options"""
        try:

            if not get_user_selected_filter_options.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                get_user_selected_filter_options.user.id,
                get_user_selected_filter_options.auth
            ):
                return MULTIPLE_LOGIN
            user_selected_filters = UserSelectedStationFinderFilters.objects.filter(
                user=get_user_selected_filter_options.user
            )
            user_selected_filter_options = None
            if user_selected_filters.first():
                user_selected_filter_options = json.loads(
                    user_selected_filters.first().selected_filter_data
                )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Successfully loaded selected filters.",
                    "data":  user_selected_filter_options,
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Filter Data List API failed due to exception -> {exception}"
            )
            return API_ERROR_OBJECT

    @classmethod
    def post(cls, save_user_selected_filter_options):
        """save user selected filter options"""
        try:
            if not save_user_selected_filter_options.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                save_user_selected_filter_options.user.id,
                save_user_selected_filter_options.auth
            ):
                return MULTIPLE_LOGIN
            user_selected_filters = UserSelectedStationFinderFilters.objects.filter(
                user=save_user_selected_filter_options.user
            )
            if user_selected_filters.first():
                user_selected_filters.update(
                    selected_filter_data=json.dumps(
                        save_user_selected_filter_options.data
                    ),
                    updated_date=timezone.localtime(timezone.now())
                )
            else:
                UserSelectedStationFinderFilters.objects.create(
                    user=save_user_selected_filter_options.user,
                    selected_filter_data=json.dumps(
                        save_user_selected_filter_options.data
                    ),
                    updated_date=timezone.localtime(timezone.now())
                )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Filters saved successfully.",
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Filter Data List API failed due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


class GetRecentlyUsedChargingStations(APIView):
    """get recently used charging stations for the user"""

    @classmethod
    def get(cls, get_recently_used_charging_stations):
        """get method to fetch list of recently used stations"""
        try:
            if not get_recently_used_charging_stations.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                get_recently_used_charging_stations.user.id,
                get_recently_used_charging_stations.auth
            ):
                return MULTIPLE_LOGIN
            # recent_charging_sessions_stations = OCPISessions.objects.filter(
            #     user_id_id=get_recently_used_charging_stations.user.id
            # ).distinct('station_id_id')
            recent_charging_sessions_stations = OCPISessions.objects.filter(
                user_id_id=get_recently_used_charging_stations.user.id
            ).values_list('station_id_id', flat=True).distinct()

            charging_session_ordering = []
            
            for recent_charging_session_station in recent_charging_sessions_stations[:5]:
                if recent_charging_session_station is None:
                    continue
                
                # back_office = OCPICredentials.objects.select_related('to_role').filter(
                #     to_role__country_code = recent_charging_session_station.location_id.country_code,
                #     to_role__party_id = recent_charging_session_station.location_id.party_id,
                #     status = "Active"
                #     ).values('name')
                
                # key_filter = OCPI_LOCATIONS_KEY+"__"+back_office.first()['name'].replace(" ","_").upper()
                # station_data = Stations.objects.filter(**{key_filter: recent_charging_session_station.location_id.id})
                station_data = Stations.objects.filter(id = recent_charging_session_station)
                charging_session_ordering.append(
                    {
                        "station_id": station_data.first().id if station_data else None,
                        "latest_session_id": OCPISessions.objects.filter(
                            user_id_id=get_recently_used_charging_stations.user.id,
                            station_id_id=recent_charging_session_station
                        ).only('id').first().id
                    }
                )

            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Successfully fetched recently charged stations.",
                    "data": [
                        station["station_id"]
                        for station in
                        sorted(
                            charging_session_ordering,
                            key=lambda session: session["latest_session_id"]
                        )
                    ]
                }
            )
        except COMMON_ERRORS as error:
            print(
                "Get recent charging session API failed for the user =>"
                + f"{get_recently_used_charging_stations.user}"
                + "\n"
                + f"due to error =>{error}"
                + "\n"
            )
            traceback.print_exc()
            return API_ERROR_OBJECT



@authentication_classes([])
@permission_classes([])
class GetDynamicTariff(APIView):
    """get dyanmic tariff details"""

    @classmethod
    def post(cls, get_dynamic_tariff):
        """get dyanmic tariff details"""
        try:
            connector_id = get_dynamic_tariff.data.get("connector_id", None)
            if connector_id is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Connector not provided.",
                    }
                )
            dynamic_tariff_response = driivz_fetch_dynamic_tariff_details(
                connector_id,
                config("DJANGO_APP_DRIIVZ_DRIVER_ACCOUNT"),
                config("DJANGO_APP_DRIIVZ_DRIVER_VIRTUAL_CARD_NUMBER"),
            )
            if dynamic_tariff_response.status_code != 200:
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "status": False,
                        "message": "Failed to get tariff details from DRIIVZ.",
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Successfully fetched tariff details.",
                    "data": Decimal(
                        json.loads(
                            dynamic_tariff_response.content
                        )["data"][
                            0
                        ]["kwhRateTariffPeriods"]["periods"][0]["price"]
                    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                }
            )
        except COMMON_ERRORS as error:
            print(
                "Get dynamic tariff API failed for the user =>"
                + f"{get_dynamic_tariff.user}"
                + "\n"
                + f"due to error =>{error}"
                + "\n"
            )
            return API_ERROR_OBJECT


class SyncLocationCron(APIView):
    """Cronjonb API"""

    @classmethod
    def post(cls, cron_job_request):
        """Post method to initialize cron job api"""
        try:
            secret_key_azure = cron_job_request.data.get("secret_key", None)
            if secret_key_azure is None:
                return SECRET_KEY_NOT_PROVIDED
            if not handler.verify(
                secret_key_azure, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
            ):
                return SECRET_KEY_IN_VALID
            back_office_data = redis_connection.get(
                OCPI_CREDENTIALS_CACHE_KEY
            )
            back_office_data = json.loads(back_office_data.decode('utf-8'))
            cpo_names = list(back_office_data.keys())

            if len(cpo_names) == 0:
                cpo_names = OCPICredentials.objects.filter(status = "Active").only("name").values_list("name", flat=True)
            
            token = get_node_secret()
            
            results = emsp_cron_function( cpo_names,token,SYNC_LOCATION_ENDPOINT)
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Cron job to sync location status initiated.",
                    "results": results,
                }
            )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT


@method_decorator(token_required, name='dispatch')
class UpdateStationsCache(APIView):
    """Cronjonb API"""
    # permission_classes = []
    # authentication_classes = []
    # @method_decorator(token_required)
    @classmethod
    def post(cls, request):
        """Post method to initialize cron job api"""
        try:
            print("Updating stations cache ...")
            update_stations_cache()
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Updating station data in cache",
                }
            )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT
