"""common serializers"""
# Date - 21/12/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file contains Serializers to make
#                       operation on database, to restrict fields of database.
#   Name            - Common Serializers
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 12/07/2025


# imports required for serializers
import concurrent.futures
from datetime import datetime
from decouple import config
import ast
from django.db.models import QuerySet

# import json
from rest_framework import serializers
import traceback

# from rest_framework import status
# from rest_framework.response import Response

from django.utils import timezone

# from django.db.models import Q
from passlib.hash import django_pbkdf2_sha256 as handler

from django.db.models import Q
from django.forms.models import model_to_dict

from .constants import (
    REQUEST_API_TIMEOUT,
    ACTIVE
)
from .create_azure import purge_cdn_cache

from .common import (
    array_to_string_converter,
    get_station_address,
    get_station_brand_logo,
    get_station_connector_speed,
    get_ultra_devices,
    redis_connection,
    get_station_services,
    filter_function_for_base_configuration,
)
from .sentry_tracers import traced_request
from .model_files.config_models import (
    BaseConfigurations,
    ConnectorConfiguration,
    MapMarkerConfigurations,
)
from .model_files.promotions_models import Promotions
from .model_files.loyalty_models import Loyalty, LoyaltyAvailableOn

from .model_files.station_models import (
    ChargePoint,
    StationConnector,
    Stations,
    Bookmarks,
    ServiceConfiguration,
)

from .constants import (
    YES,
    NO,
    ACTIVE_STATION_STATUSES,
    COMING_SOON_CONST,
    APP_VERSION_THREE,
    APP_VERSION_FOUR,
    GET_REQUEST,
)

from .shared_station_detail_serializer import StationDetailSerializer
from .model_files.ocpi_locations_models import OCPILocation, OCPIEVSE, OCPIConnector 
from .model_files.ocpi_credentials_models import OCPICredentials,OCPICredentialsRole

from sharedServices.ocpi_common_functions import get_back_office_data

from .model_files.ocpi_tariffs_models import Tariffs
# This serializer returns the detailed info list of connectors
# available for a particular chargepoint. This serializer
# is used for station details page


def get_connector_image(app_version, plug_type_name):
    """this function return connector image for a specific version"""
    queryset = ConnectorConfiguration.objects.filter(
        connector_plug_type=plug_type_name,
        for_app_version=app_version
    )
    if queryset.first():
        return queryset.first().get_image_path()
    return "no_image"


class ConnectorDetailsSerializer(serializers.ModelSerializer):
    """connector details serializer"""

    # Following code defines the meta data for serializer.
    v3_image = serializers.SerializerMethodField("get_v3_image")
    v4_image = serializers.SerializerMethodField("get_v4_image")
    max_charge_rate = serializers.SerializerMethodField("get_max_charge_rate")
    tariff_id = serializers.SerializerMethodField("get_tariff_id")
    evse_uid = serializers.SerializerMethodField("get_evse_uid")

    @classmethod
    def get_v3_image(cls, connector):
        """get connector image"""
        return get_connector_image(
            APP_VERSION_THREE, connector.plug_type_name
        )

    @classmethod
    def get_v4_image(cls, connector):
        """get connector image"""
        return get_connector_image(
            APP_VERSION_FOUR, connector.plug_type_name
        )

    @classmethod
    def get_max_charge_rate(cls, connector):
        """get connector max charge rate"""
        return str(float(connector.max_charge_rate))
    
    @classmethod
    def get_evse_uid(cls, connector):
        """get connector evse uid"""
        try:
            ocpi_connector = OCPIConnector.objects.filter(connector_mapping_id = connector).first()
            return ocpi_connector.evse_id.uid if ocpi_connector is not None else None
        except Exception as e:
            print(e)
            return None
    
    def get_tariff_id(self, connector):
        """get connector max charge rate"""
        try:
            if connector.back_office is None:
                return None
            location = OCPILocation.objects.filter(station_mapping_id = self.context.get("station")).first()
            if not location:
                return None
            connector_data =  OCPIConnector.objects.filter(connector_mapping_id=connector).first()
            if not connector_data:
                return None
            connector_tariff_ids = connector_data.tariff_ids
            return connector_tariff_ids# tariff_ids_arr if tariff_ids_arr else None
        except Exception as e:
            traceback.print_exc()

    class Meta:
        """assign meta data for Station connector"""

        model = StationConnector
        fields = [
            "id",
            "connector_id",
            "connector_type",
            "status",
            "plug_type_name",
            "max_charge_rate",
            "tariff_amount",
            "tariff_currency",
            "connector_sorting_order",
            "v3_image",
            "v4_image",
            "back_office",
            "tariff_id",
            "evse_uid"
        ]


def sort_station_connector(station_connector):
    """this function is used to sort station connectors"""
    return (
        int(float(station_connector.connector_sorting_order))
        if station_connector.connector_sorting_order
        else 0
    )


# This serializer returns the detailed info list of chargepoints
# available on a particular stationt.
# This serializer is used for station details page
class ChargePointDetailsSerializer(serializers.ModelSerializer):
    """Chargepoint  details serializer"""

    # serializer call to get the list of connectors available
    # on the chargepoint.
    connectors = serializers.SerializerMethodField("get_connectors_list")
    phone_number = serializers.SerializerMethodField("get_provider_phone_number")

    @classmethod
    def get_provider_phone_number(cls, chargepoint):
        """get chargepoint provider phone number"""
        query_string = chargepoint.back_office.lower() + "_number"
        phone_number = BaseConfigurations.objects.filter(
            base_configuration_key=query_string
        )
        return (
            phone_number.first().base_configuration_value
            if phone_number.first()
            else ""
        )

    # @classmethod
    def get_connectors_list(self, chargepoint):
        """get chargepoint connectors with details"""
        chargepoint_connectors_list = list(
            sorted(
                StationConnector.objects.filter(
                    station_id=chargepoint.station_id,
                    charge_point_id=chargepoint,
                    deleted=NO,
                    status=ACTIVE,
                ),
                key=sort_station_connector,
            )
        )
        connector_data = ConnectorDetailsSerializer(
            chargepoint_connectors_list, many=True, read_only=True, context={
                "location_data":self.context.get("location_data"),
                "station":self.context.get("station")
                }
        )
        return connector_data.data

    # Following code defines the meta data for serializer.
    class Meta:
        """charge point serializer"""

        model = ChargePoint
        fields = [
            "id",
            "charger_point_id",
            "charger_point_name",
            "back_office",
            "phone_number",
            "device_id",
            "connectors",
            "ev_charge_point_status"
        ]


def get_promotion_details_data(station, is_loyalty):
    """returns have promotion data"""
    if is_loyalty:
        data = Loyalty.objects.filter(
            station_available_loyalties__deleted=NO,
            station_available_loyalties__station_id=station,
            status=ACTIVE,
            valid_to_date__gte=timezone.localtime(timezone.now()),
            valid_from_date__lte=timezone.localtime(timezone.now()),
            deleted=NO,
        )
    else:
        data = Promotions.objects.filter(
            station_available_promotions__deleted=NO,
            station_available_promotions__station_id=station,
            status=ACTIVE,
            end_date__gte=timezone.localtime(timezone.now()),
            start_date__lte=timezone.localtime(timezone.now()),
            deleted=NO,
        )
    return data


def get_offer_status(station, car_wash = False):
    if car_wash:
        offers = Loyalty.objects.filter(is_car_wash = True, status = "Active", deleted = NO)
    else:
        offers = Loyalty.objects.filter(is_car_wash = False, status = "Active", deleted = NO)
    flag = False
    loyalty_stations = LoyaltyAvailableOn.objects.filter(loyalty_id__in = offers ).values_list("station_id",flat=True)
    
    if station.id in loyalty_stations:
        flag = True
    return flag

# This serializer returns the list of stations
class StationSerializer(serializers.ModelSerializer):
    """station serializer for station finder"""

    # The variable station_add is used to pass the station address
    # in API, and get_address is used to call the function used
    # to format the station address.
    # station_add = serializers.SerializerMethodField("get_address")
    station_add = serializers.SerializerMethodField("get_location_address")
    station_services = serializers.SerializerMethodField("get_station_services")
    v3_brand_logo = serializers.SerializerMethodField("get_v3_brand_logo")
    v4_brand_logo = serializers.SerializerMethodField("get_v4_brand_logo")
    v4_small_brand_logo = serializers.SerializerMethodField("get_v4_small_brand_logo")
    v4_non_ev_brand_logo = serializers.SerializerMethodField("get_v4_non_ev_brand_logo")
    v4_non_ev_small_brand_logo = serializers.SerializerMethodField("get_v4_non_ev_small_brand_logo")
    bookmark_status = serializers.SerializerMethodField("get_bookmark_status")
    charge_points = serializers.SerializerMethodField("get_charge_points")
    status_images = serializers.SerializerMethodField("get_status_images")
    is_ev = serializers.SerializerMethodField("get_is_ev_status")
    is_mfg = serializers.SerializerMethodField("get_is_mfg_status")
    station_device_speed = serializers.SerializerMethodField("get_station_device_speed")
    station_name = serializers.SerializerMethodField("get_location_name")
    site_title = serializers.SerializerMethodField("get_location_name")
    is_car_wash_available = serializers.SerializerMethodField("get_car_wash_stations")
    is_offer_available = serializers.SerializerMethodField("get_offer_stations")
    parking_details = serializers.SerializerMethodField("get_parking_details")

    @classmethod
    def get_is_ev_status(cls, station):
        """returns is ev status"""
        if station.is_ev == YES:
            station_chargepoint_list = ChargePoint.objects.filter(
                station_id=station, charger_point_status=ACTIVE
            )
            return bool(station_chargepoint_list.first())
        return False
    
    @classmethod
    def get_parking_details(cls, station):
        """returns is ev status"""
        return station.parking_details
    
    @classmethod
    def get_car_wash_stations(cls, station):
        """returns if car wash is present on station"""
        return get_offer_status(station,True)
    
    @classmethod
    def get_offer_stations(cls, station):
        """returns location name"""
        return get_offer_status(station)
    
    @classmethod
    def get_location_name(cls, station):
        """returns location name"""
        location = OCPILocation.objects.filter(station_mapping_id_id = station.id).first()
        if location is not None:
            return location.name
        return station.station_name
    
    @classmethod
    def get_location_address(cls, station):
        """returns location address"""
        location = OCPILocation.objects.filter(station_mapping_id_id = station.id).first()
        # address = get_location_add(location)
        if location is not None:
            print("location_address : ",location.get_full_address())
        return location.get_full_address() if location is not None and len(location.get_full_address()) > 0  else get_station_address(station)

    @classmethod
    def get_is_mfg_status(cls, station):
        """returns is mfg status"""
        return bool(station.is_mfg == "Yes")

    @classmethod
    def get_status_images(cls, station_status):
        """get status images"""
        if station_status.is_ev == YES:
            status_images = {}
            if station_status.status == COMING_SOON_CONST:
                coming_soon_marker = MapMarkerConfigurations.objects.filter(
                    map_marker_key="-".join(COMING_SOON_CONST.split(" "))
                ).first()
                if coming_soon_marker:
                    status_images["coming_soon"] = coming_soon_marker.get_image_path()
            query_string_status = ""
            ultra_rapid_devices = get_ultra_devices(station_status)

            query_string_status = get_station_connector_speed(
                station_status, ultra_rapid_devices
            )
            if len(query_string_status) > 0:
                return {
                    **status_images,
                    **{
                        "available": MapMarkerConfigurations.objects.filter(
                            map_marker_key=f"{query_string_status}-Available"
                        )
                        .first()
                        .get_image_path(),
                        "occupied": MapMarkerConfigurations.objects.filter(
                            map_marker_key=f"{query_string_status}-Occupied"
                        )
                        .first()
                        .get_image_path(),
                        "unavailable": MapMarkerConfigurations.objects.filter(
                            map_marker_key=f"{query_string_status}-Unknown"
                        )
                        .first()
                        .get_image_path(),
                        "loading": MapMarkerConfigurations.objects.filter(
                            map_marker_key=f"{query_string_status}-Loading"
                        )
                        .first()
                        .get_image_path(),
                    },
                }
        return {}

    @classmethod
    def get_station_device_speed(cls, station):
        """this function returns device speed"""
        station_chargepoint_list = ChargePoint.objects.filter(
            station_id=station, charger_point_status=ACTIVE
        )
        if station.is_ev == YES and bool(station_chargepoint_list.first()):
            ultra_rapid_devices = get_ultra_devices(station)
            return get_station_connector_speed(station, ultra_rapid_devices)
        return ""

    def get_charge_points(self, station):
        """get station charge points"""
        if station.is_ev != YES:
            return []
        station_chargepoint_list = ChargePoint.objects.filter(
            station_id=station, charger_point_status=ACTIVE, deleted=NO
        ).order_by("device_id")
        chargepoint_data = ChargePointDetailsSerializer(
            station_chargepoint_list,
            many=True,
            read_only=True,
            context={
                "is_detail_api": self.context["is_detail_api"]
                if "is_detail_api" in self.context
                else False,
                "location_data":station.ocpi_locations,
                "station":station
            },
        )
        return chargepoint_data.data

    @classmethod
    def get_address(cls, station):
        """returns address of station"""
        return get_station_address(station)

    @classmethod
    def get_v3_brand_logo(cls, station):
        """get station brand logo"""
        return get_station_brand_logo(station, APP_VERSION_THREE)

    @classmethod
    def get_v4_non_ev_brand_logo(cls, station):
        """get station brand logo"""
        return get_station_brand_logo(station, APP_VERSION_FOUR, non_ev=True)
    
    @classmethod
    def get_v4_non_ev_small_brand_logo(cls, station):
        """get station brand logo"""
        return get_station_brand_logo(station, APP_VERSION_FOUR, get_small_image=True, non_ev=True)

    @classmethod
    def get_v4_brand_logo(cls, station):
        """get station brand logo"""
        return get_station_brand_logo(station, APP_VERSION_FOUR)
    
    @classmethod
    def get_v4_small_brand_logo(cls, station):
        """get station brand logo"""
        return get_station_brand_logo(station, APP_VERSION_FOUR, get_small_image=True)

    def get_bookmark_status(self, station):
        """bookmark status by default False"""
        bookmarked = False
        if "is_detail_api" in self.context and self.context["user_id"]:
            user_bookmarks = Bookmarks.objects.filter(
                bookmarked_station_id=station.id,
                user_id_id=self.context["user_id"],
            )
            return bool(
                user_bookmarks.first()
                and user_bookmarks.first().bookmark_status == "bookmarked"
            )
        return bookmarked

    # FuCtion returns the list of services available on the station.
    def get_station_services(self, station):
        """station services"""
        return get_station_services(station)

    # Following code defines the meta data for serializer.
    class Meta:
        """assign meta data for Station"""

        model = Stations
        fields = [
            "id",
            "station_id",
            "site_title",
            "station_name",
            "latitude",
            "station_services",
            "station_type",
            "country",
            "station_add",
            "longitude",
            "brand",
            "v3_brand_logo",
            "v4_brand_logo",
            "v4_small_brand_logo",
            "owner",
            "email",
            "phone",
            "status",
            "charge_points",
            "is_mfg",
            "is_ev",
            "bookmark_status",
            "status_images",
            "station_device_speed",
            "post_code",
            "region",
            "site_id",
            "driivz_display_name",
            "ev_station_status",
            "overstay_fee",
            "v4_non_ev_small_brand_logo",
            "v4_non_ev_brand_logo",
            "is_car_wash_available",
            "is_offer_available",
            "parking_details",
        ]


def station_finder_api_call():
    """test api call"""
    traced_request(
        GET_REQUEST,
        config("DJANGO_APP_API_STATION_FINDER"), timeout=REQUEST_API_TIMEOUT
    )
    traced_request(
        GET_REQUEST,
        config("DJANGO_APP_API_STATION_FINDER_VERSION_FOUR"), timeout=REQUEST_API_TIMEOUT
    )
    return


def get_version_wise_connector_images(app_version, charge_points):
    """This function returns version wise connector images for chargepoints"""
    return [
        {
            **charge_point,
            "connectors": [
                {
                    "id": connector["id"],
                    "connector_id": connector["connector_id"],
                    "connector_type": connector["connector_type"],
                    "status": connector["status"],
                    "plug_type_name": connector["plug_type_name"],
                    "max_charge_rate": connector["max_charge_rate"],
                    "tariff_amount": connector["tariff_amount"],
                    "tariff_currency": connector["tariff_currency"],
                    "connector_sorting_order": connector[
                        "connector_sorting_order"
                    ],
                    "image": connector[f"v{app_version}_image"],
                    "back_office":connector["back_office"],
                    "tariff_id":connector["tariff_id"],
                }
                for connector in charge_point["connectors"]
            ]
        }
        for charge_point in charge_points
    ]


def caching_station_finder_data():
    """this function caches data for station finder"""
    station_finder_data_v3 = {}
    station_finder_data_v4 = {}

    available_status_image = MapMarkerConfigurations.objects.filter(
        map_marker_key="EV-Site-Available"
    ).first()
    occupied_status_image = MapMarkerConfigurations.objects.filter(
        map_marker_key="EV-Site-Occupied"
    ).first()
    unavailable_status_image = MapMarkerConfigurations.objects.filter(
        map_marker_key="EV-Site-Unknown"
    ).first()
    loading_status_image = MapMarkerConfigurations.objects.filter(
        map_marker_key="EV-Site-Loading"
    ).first()
    car_wash_image = MapMarkerConfigurations.objects.filter(
        map_marker_key="Car-Wash"
    ).first()
    loyalty_image = MapMarkerConfigurations.objects.filter(
        map_marker_key="Loyalty"
    ).first()

    ev_status_images = {
        "available":available_status_image.get_image_path(),
        "sm_available":available_status_image.get_small_image_path(),
        "occupied": occupied_status_image.get_image_path(),
        "sm_occupied": occupied_status_image.get_small_image_path(),
        "unavailable": unavailable_status_image.get_image_path(),
        "sm_unavailable": unavailable_status_image.get_small_image_path(),
        "loading": loading_status_image.get_image_path(),
        "sm_loading": loading_status_image.get_small_image_path(),
        "car_wash_image":car_wash_image.get_image_path(),
        "sm_car_wash_image":car_wash_image.get_small_image_path(),
        "loyalty_image":loyalty_image.get_image_path(),
        "sm_loyalty_image":loyalty_image.get_small_image_path(),
    }

    def station_extractor(station):
        """data extractor"""
        promotions_details = StationDetailSerializer(station)
        serializer_data = StationSerializer(station).data

        data = {
            **promotions_details.data,
            **serializer_data,
        }
        site_title = serializer_data["site_title"]
        # (
        #     serializer_data["driivz_display_name"]
        #     if serializer_data["driivz_display_name"] else
        #     serializer_data["site_title"]
        # )
        v3_extended_data = {
            "site_title": site_title,
            "charge_points": get_version_wise_connector_images(
                APP_VERSION_THREE,
                serializer_data["charge_points"]
            ),
            "brand_logo": serializer_data["v3_brand_logo"]
        }
        v4_extended_data = {
            "site_title": site_title,
            "status_images": ev_status_images,
            "charge_points": get_version_wise_connector_images(
                APP_VERSION_FOUR,
                serializer_data["charge_points"]
            ),
            "open_now": data["open_now"],
            "working_hours_details": data["working_hours_details"],
            "non_ev_brand_logo":serializer_data['v4_non_ev_brand_logo'],
            "non_ev_brand_logo_small":serializer_data['v4_non_ev_small_brand_logo'],
            "brand_logo": serializer_data["v4_brand_logo"],
            "small_brand_logo": serializer_data["v4_small_brand_logo"],
            "image_url_list": [
                image for image in data["image_url_list"]
                if (
                    "app_version" in image and 
                    image["app_version"] == APP_VERSION_FOUR
                )
            ]
        }
        serializer_data.pop("v3_brand_logo")
        serializer_data.pop("v4_brand_logo")
        serializer_data.pop("v4_small_brand_logo")
        serializer_data.pop("driivz_display_name")
        redis_connection.set(
            f"station-info-{serializer_data['id']}",
            array_to_string_converter(data),
        )
        return [
            station.id,
            {
                **serializer_data,
                **v3_extended_data
            },
            {
                **serializer_data,
                **v4_extended_data
            }
        ]

    # function for purging cdn
    print("*********************Purge Started***************")
    purge_cdn_cache()
    # updating the updated_stations_key in base config for setting as a flag
    updated_stations_key = handler.hash(
        datetime.strftime(timezone.localtime(timezone.now()), "%Y-%m-%d %H:%M:%S.%f")
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        queryset = Stations.objects.filter(
            deleted=NO, status__in=ACTIVE_STATION_STATUSES
        )
        results = executor.map(station_extractor, queryset)
        for result in results:
            station_finder_data_v3[result[0]] = result[1]
            station_finder_data_v4[result[0]] = result[2]
    redis_connection.set(
        "station_finder_cache_data_updated_v3",
        array_to_string_converter(
            [
                {
                    "stations": station_finder_data_v3,
                    "reset_stations": updated_stations_key,
                    "services": {
                        service.id: {
                            "id": service.id,
                            "url": service.get_image_path(),
                            "service_name": service.service_name,
                            "service_type": service.service_type,
                        }
                        for service in (
                            ServiceConfiguration.objects.only(
                                "id", "service_name", "service_type"
                            )
                        )
                    },
                }
            ]
        ),
    )
    redis_connection.set(
        "station_finder_cache_data_updated_v4",
        array_to_string_converter(
            [
                {
                    "stations": station_finder_data_v4,
                    "reset_stations": updated_stations_key,
                    "services": {
                        service.id: {
                            "id": service.id,
                            "url": service.get_image_path(),
                            "service_name": service.service_name,
                            "service_type": service.service_type,
                            "service_unique_identifier": service.service_unique_identifier
                        }
                        for service in (
                            ServiceConfiguration.objects.only(
                                "id",
                                "service_name",
                                "service_type",
                                "service_unique_identifier"
                            )
                        )
                    },
                    "connectors": [
                        {
                            "connector_type": i.connector_plug_type,
                            "image": i.get_image_path(),
                            "alt_image": i.get_alt_image_path(),
                        } for i in ConnectorConfiguration.objects.filter(
                            connector_plug_type__in=StationConnector.objects.filter(
                                deleted=NO,
                                status=ACTIVE,
                            )
                            .values_list("plug_type_name", flat=True)
                            .distinct(),
                            for_app_version=APP_VERSION_FOUR
                        ).order_by("sorting_order")
                    ],
                    "preauthorize_money_ev": float(
                        filter_function_for_base_configuration(
                            "preauthorize_money_ev", 0
                        )
                    ),
                    "wallet_preauthorize_money_ev": float(
                        filter_function_for_base_configuration(
                            "wallet_preauthorize_money_ev", 0
                        )
                    )
                }
            ]
        ),
    )
    redis_connection.set(
        "active_cp_ids",
        array_to_string_converter(
            list(
                ChargePoint.objects.filter(charger_point_status=ACTIVE, deleted=NO)
                .values_list("station_id", flat=True)
                .distinct()
            )
        ),
    )

    station_finder_api_call()

    reset_station_from_baseconfig = BaseConfigurations.objects.filter(
        base_configuration_key="reset_stations"
    )
    if reset_station_from_baseconfig:
        reset_station_from_baseconfig.update(
            base_configuration_value=updated_stations_key,
            updated_date=timezone.localtime(timezone.now()),
        )
        redis_connection.set("reset_stations",updated_stations_key)
    else:
        BaseConfigurations.objects.create(
            base_configuration_key="reset_stations",
            base_configuration_value=updated_stations_key,
            created_date=timezone.localtime(timezone.now()),
        )
        redis_connection.set("reset_stations",updated_stations_key)
    print("**********Caching Done*********")




# This serializer returns the list of stations
class StationDetailsLogoSerializer(serializers.ModelSerializer):
    """station serializer for stations"""

    # Here the variables before equal to (=) are the names to be
    # passed in the API and the names passed in 'SerializerMethodField()'
    # are the name of functions which return the
    # value for the respected variable.
    station_add = serializers.SerializerMethodField("get_address")
    brand_logo = serializers.SerializerMethodField("get_brand_logo")

    # Function to get the address of station in combined format.
    @classmethod
    def get_address(cls, station):
        """returns address of station"""
        return get_station_address(station)

    @classmethod
    def get_brand_logo(cls, station):
        """get station brand logo"""
        return get_station_brand_logo(station)

    # Following code defines the meta data for serializer.

    class Meta:
        """meta data"""

        model = Stations
        fields = [
            "id",
            "station_name",
            "station_id",
            "station_add",
            "brand_logo",
            "latitude",
            "longitude",
            "site_title",
        ]
