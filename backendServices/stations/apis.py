"""stations apis"""
# Date - 21/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on APIs
#                       related to station finder data.
#   Name            - Station Finder APIs
#   Modified by     - Vismay Raul
#   Modified date   - 23/02/2023


# These are all the imports that we are exporting from
# different module's from project or library.
import ast
import json
import googlemaps
import traceback
from decouple import config
from better_profanity import profanity

from django.db.models import Q, Case, When, F

from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
)

# pylint:disable=import-error
from sharedServices.constants import (
    DEFAULT_LATITUDE_FOR_PROMOTIONS_AND_STATION_FINDER,
    DEFAULT_LONGITUDE_FOR_PROMOTIONS_AND_STATION_FINDER,
    MFG_NORMAL,
    MFG_RAPID,
    OTHER_NORMAL,
    OTHER_RAPID,
    NO,
    YES,
    EMPTY_CACHE_CHECK,
    ACTIVE_STATION_STATUSES,
    COMING_SOON_CONST,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    ACTIVE,
    IS_EV_ID_KEY,
    STATION_ID_KEY,
    NO_NEARBY_STATIONS_AVAILABLE,
    IS_EV_FLAG_TRUE,
    IS_EV_FLAG_FALSE,
)
from sharedServices.model_files.station_models import (
    Bookmarks,
    Stations,
    StationConnector,
    StationServices,
    ChargePoint,
)

from sharedServices.model_files.config_models import (
    ConnectorConfiguration,
    MapMarkerConfigurations,
    ServiceConfiguration,
)

from sharedServices.common import (
    array_to_string_converter,
    get_distance,
    RADIUS,
    get_station_distance,
    handle_concurrent_user_login,
    redis_connection,
    string_to_array_converter,
    filter_function_for_base_configuration,
)
from sharedServices.shared_station_serializer import StationSerializer
from sharedServices.shared_station_detail_serializer import (
    StationDetailSerializer,
)
from sharedServices.model_files.loyalty_models import Loyalty
from backendServices.loyalty.apis import return_station_loyalties
from backendServices.backend_app_constants import MULTIPLE_LOGIN, UNAUTHORIZED
from backendServices.trip_planner.trips_helper_functions import (
    get_devices_speed,
)
from .serializers import (
    BookmarksSerializer,
    ReviewsSerializer,
)

from .stations_helper_function import (
    location_data_api,
    updating_tariff,
)

# list of station API (this API returns list of stations
# in sorted manner according to user's
# current location in simple words nearest station).


class StationFinderViewSet(APIView):
    """station finder viewset"""

    # Permission classes are used to restrict the user
    permission_classes = [permissions.AllowAny]

    def get(self, station_finder_request):
        """get method to fetch station finder stations"""
        try:
            data = redis_connection.get("station_finder_cache_data_updated_v3")
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

def get_trigger_sites():
    """
    Returns the car wash trigger sites
    """
    car_wash_data = Loyalty.objects.filter(is_car_wash = True,status = 'Active').first()
    trigger_sites = string_to_array_converter(car_wash_data.trigger_sites)
    if not trigger_sites or len(trigger_sites) == 0:
        trigger_sites = list(Stations.objects.all().only("station_id"))
    return trigger_sites


@authentication_classes([])
@permission_classes([])
class NearestStation(APIView):
    """To fetch nearest station"""

    # Permission classes are used to restrict the user
    permission_classes = [permissions.AllowAny]

    @staticmethod
    def get_nearest_station(user_latitude, user_longitude, is_ev=None, both=False, is_car_wash=False):
        """
        Returns the nearest station dict (with keys: STATION_ID_KEY, IS_EV_ID_KEY, etc.)
        """

        # Extracting user address from gmaps api
        gmaps = googlemaps.Client(key=config("DJANGO_APP_GOOGLE_API_KEY"))
        reverse_geocode = gmaps.reverse_geocode((user_latitude, user_longitude))

        user_town = ""
        user_address_line3 = ""
        user_administrative_area_level_1 = ""
        user_country = ""
        for google_location in reverse_geocode:
            for rev in range(len(google_location["address_components"])):
                if (
                    "postal_town"
                    in google_location["address_components"][rev]["types"]
                ):
                    user_town = google_location["address_components"][rev][
                        "long_name"
                    ]
                if (
                    "administrative_area_level_2"
                    in google_location["address_components"][rev]["types"]
                ):
                    user_address_line3 = google_location["address_components"][rev][
                        "long_name"
                    ]
                if (
                    "administrative_area_level_1"
                    in google_location["address_components"][rev]["types"]
                ):
                    user_administrative_area_level_1 = google_location[
                        "address_components"
                    ][rev]["long_name"]
                if (
                    "country"
                    in google_location["address_components"][rev]["types"]
                ):
                    user_country = google_location["address_components"][
                        rev
                    ]["long_name"]
            if user_town and user_address_line3:
                break

        station = {STATION_ID_KEY: [], IS_EV_ID_KEY: []}
        if both:
            if is_car_wash:
                trigger_sites = get_trigger_sites()
                
                station[STATION_ID_KEY] = (
                    Stations.objects.annotate(
                        selected_field=Case(
                            When(
                                Q(town=user_town) & ~Q(town=""), then=F("town")
                            ),
                            When(
                                Q(station_address3=user_address_line3)
                                & ~Q(station_address3=""),
                                then=F("station_address3"),
                            ),
                            When(
                                (
                                    Q(country=user_administrative_area_level_1)
                                    | Q(country=user_country)
                                )
                                & ~Q(country=""),
                                then=F("country"),
                            ),
                            default=None,
                        )
                    )
                    .filter(
                        selected_field__isnull=False,
                        deleted=NO,
                        status=ACTIVE,
                        station_id__in = trigger_sites
                    )
                    .values("id", "latitude", "longitude")
                )
            else:
                station[STATION_ID_KEY] = (
                    Stations.objects.annotate(
                        selected_field=Case(
                            When(
                                Q(town=user_town) & ~Q(town=""), then=F("town")
                            ),
                            When(
                                Q(station_address3=user_address_line3)
                                & ~Q(station_address3=""),
                                then=F("station_address3"),
                            ),
                            When(
                                (
                                    Q(country=user_administrative_area_level_1)
                                    | Q(country=user_country)
                                )
                                & ~Q(country=""),
                                then=F("country"),
                            ),
                            default=None,
                        )
                    )
                    .filter(
                        selected_field__isnull=False,
                        deleted=NO,
                        status=ACTIVE,
                    )
                    .values("id", "latitude", "longitude")
                )

            if not station[STATION_ID_KEY]:
                return None

            if (
                station[STATION_ID_KEY]
                and len(station[STATION_ID_KEY]) > 1
            ):
                def get_station_distance_station(station_distance_value):
                    return get_station_distance(
                        station_distance_value,
                        user_latitude,
                        user_longitude,
                    )
                station[STATION_ID_KEY] = sorted(
                    station[STATION_ID_KEY],
                    key=get_station_distance_station,
                )

        elif is_ev == IS_EV_FLAG_TRUE:
            active_cp_ids = redis_connection.get("active_cp_ids")
            if (
                active_cp_ids
                and active_cp_ids.decode("utf-8") != EMPTY_CACHE_CHECK
            ):
                active_cp_ids = string_to_array_converter(
                    active_cp_ids.decode("utf-8")
                )

            if not active_cp_ids:
                active_cp_ids = list(
                    ChargePoint.objects.filter(
                        charger_point_status="Active", deleted=NO
                    )
                    .only("station_id")
                    .values_list("station_id", flat=True)
                    .distinct()
                )
                redis_connection.set(
                    "active_cp_ids",
                    array_to_string_converter(active_cp_ids),
                )
            if is_car_wash:
                trigger_sites = get_trigger_sites()
                station[IS_EV_ID_KEY] = (
                    Stations.objects.annotate(
                        selected_field=Case(
                            When(
                                Q(town=user_town)
                                & ~Q(town="")
                                & Q(town__isnull=False),
                                then=F("town"),
                            ),
                            When(
                                Q(station_address3=user_address_line3)
                                & ~Q(station_address3=""),
                                then=F("station_address3"),
                            ),
                            When(
                                Q(country=user_administrative_area_level_1)
                                & ~Q(country=""),
                                then=F("country"),
                            ),
                            default=None,
                        )
                    )
                    .filter(
                        selected_field__isnull=False,
                        is_ev=YES,
                        deleted=NO,
                        status=ACTIVE,
                        id__in=active_cp_ids,
                        station_id__in = trigger_sites
                    )
                    .values("id", "latitude", "longitude")
                )
            else:
                station[IS_EV_ID_KEY] = (
                    Stations.objects.annotate(
                        selected_field=Case(
                            When(
                                Q(town=user_town)
                                & ~Q(town="")
                                & Q(town__isnull=False),
                                then=F("town"),
                            ),
                            When(
                                Q(station_address3=user_address_line3)
                                & ~Q(station_address3=""),
                                then=F("station_address3"),
                            ),
                            When(
                                Q(country=user_administrative_area_level_1)
                                & ~Q(country=""),
                                then=F("country"),
                            ),
                            default=None,
                        )
                    )
                    .filter(
                        selected_field__isnull=False,
                        is_ev=YES,
                        deleted=NO,
                        status=ACTIVE,
                        id__in=active_cp_ids,
                    )
                    .values("id", "latitude", "longitude")
                )

            if not station[IS_EV_ID_KEY]:
                return None

            if station[IS_EV_ID_KEY] and len(station[IS_EV_ID_KEY]) > 1:
                def get_station_distance_station_ev(station_distance_value):
                    return get_station_distance(
                        station_distance_value,
                        user_latitude,
                        user_longitude,
                    )
                station[IS_EV_ID_KEY] = sorted(
                    station[IS_EV_ID_KEY],
                    key=get_station_distance_station_ev,
                )
        

        elif is_ev == IS_EV_FLAG_FALSE:
            if is_car_wash:
                trigger_sites = get_trigger_sites()
                
                station[STATION_ID_KEY] = (
                    Stations.objects.annotate(
                        selected_field=Case(
                            When(
                                Q(town=user_town) & ~Q(town=""), then=F("town")
                            ),
                            When(
                                Q(station_address3=user_address_line3)
                                & ~Q(station_address3=""),
                                then=F("station_address3"),
                            ),
                            When(
                                (
                                    Q(country=user_administrative_area_level_1)
                                    | Q(country=user_country)
                                )
                                & ~Q(country=""),
                                then=F("country"),
                            ),
                            default=None,
                        )
                    )
                    .filter(
                        selected_field__isnull=False,
                        is_ev=NO,
                        deleted=NO,
                        status=ACTIVE,
                        station_id__in = trigger_sites
                    )
                    .values("id", "latitude", "longitude")
                )
            else:
                station[STATION_ID_KEY] = (
                    Stations.objects.annotate(
                        selected_field=Case(
                            When(
                                Q(town=user_town) & ~Q(town=""), then=F("town")
                            ),
                            When(
                                Q(station_address3=user_address_line3)
                                & ~Q(station_address3=""),
                                then=F("station_address3"),
                            ),
                            When(
                                (
                                    Q(country=user_administrative_area_level_1)
                                    | Q(country=user_country)
                                )
                                & ~Q(country=""),
                                then=F("country"),
                            ),
                            default=None,
                        )
                    )
                    .filter(
                        selected_field__isnull=False,
                        is_ev=NO,
                        deleted=NO,
                        status=ACTIVE,
                    )
                    .values("id", "latitude", "longitude")
                )

            if not station[STATION_ID_KEY]:
                return None

            if (
                station[STATION_ID_KEY]
                and len(station[STATION_ID_KEY]) > 1
            ):
                def get_station_distance_station(station_distance_value):
                    return get_station_distance(
                        station_distance_value,
                        user_latitude,
                        user_longitude,
                    )
                station[STATION_ID_KEY] = sorted(
                    station[STATION_ID_KEY],
                    key=get_station_distance_station,
                )

        reset_stations = redis_connection.get("reset_stations")

        station = {
            STATION_ID_KEY: [station[STATION_ID_KEY][0]["id"]]
            if station[STATION_ID_KEY]
            else [],
            IS_EV_ID_KEY: [station[IS_EV_ID_KEY][0]["id"]]
            if station[IS_EV_ID_KEY]
            else [],
            "reset_stations": reset_stations if reset_stations else None,
        }
        return station

    def get(self, nearest_station):
        """get method to fetch station finder stations"""
        try:
            user_latitude = self.request.query_params.get("latitude", False)
            user_longitude = self.request.query_params.get("longitude", False)
            is_ev = self.request.query_params.get("is_ev", None)
            both = None
            if not is_ev:
                both = True
            is_car_wash_param = self.request.query_params.get("is_car_wash", IS_EV_FLAG_FALSE)
            is_car_wash = True
            if is_car_wash_param.lower() =='false':
                is_car_wash = False
            if user_latitude and user_longitude:
                user_latitude = float(user_latitude)
                user_longitude = float(user_longitude)
            else:
                user_latitude = (
                    DEFAULT_LATITUDE_FOR_PROMOTIONS_AND_STATION_FINDER
                )
                user_longitude = (
                    DEFAULT_LONGITUDE_FOR_PROMOTIONS_AND_STATION_FINDER
                )

            station = self.get_nearest_station(user_latitude, user_longitude, is_ev,both,is_car_wash=is_car_wash)

            if not station or (
                not station.get(STATION_ID_KEY) and not station.get(IS_EV_ID_KEY)
            ):
                return Response(
                    {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "status": False,
                        "message": NO_NEARBY_STATIONS_AVAILABLE,
                    }
                )

            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Fetched stations.",
                    "data": station,
                }
            )

        except COMMON_ERRORS as exception:
            traceback.print_exc()
            print(
                f"Nearest Station ViewSet API failed for user -> \
                    {nearest_station.user.id} due to exception -> \
                        {exception}"
            )
            return API_ERROR_OBJECT


class Bookmark(APIView):
    """bookmark api"""

    # Permission classes are used to restrict the user
    permission_classes = [permissions.IsAuthenticated]

    def get(self, station_finder_request):
        """get method to fetch station finder stations"""
        try:
            # The following two lines are used for user's bookmarked stations
            if self.request.auth:
                if not handle_concurrent_user_login(
                    station_finder_request.user.id, station_finder_request.auth
                ):
                    return Response(
                        {
                            "status_code": status.HTTP_409_CONFLICT,
                            "status": False,
                            "message": (
                                "You have logged in from another device!"
                            ),
                        }
                    )

                # getting bookmarked stations from db with respect to user
                bookmarked_stations = list(
                    Stations.objects.select_related(
                        "user_bookmarks__user_id",
                        "user_bookmarks__bookmark_status",
                    )
                    .filter(
                        user_bookmarks__user_id=self.request.user,
                        user_bookmarks__bookmark_status="bookmarked",
                    )
                    .values_list("id", flat=True)
                    .iterator()
                )

                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "Fetched stations.",
                        "data": bookmarked_stations,
                    }
                )
        except COMMON_ERRORS as exception:
            print(
                f"Bookmark ViewSet API failed for user -> \
                    {station_finder_request.user.id} due to exception -> \
                        {exception}"
            )
            return API_ERROR_OBJECT


# list of station API (this API returns list of stations
# in sorted manner according to user's
# current location in simple words nearest station).
class StationFinderRadiusViewSet(ModelViewSet):
    """station finder api with respect to radius"""

    try:
        queryset = Stations.objects.all()

        # Permission classes are used to restrict the user
        permission_classes = [permissions.IsAuthenticated]

        # serializer_class is nothing but the the serializer
        # which helps us to make queries.
        serializer_class = StationSerializer

        # this function is the actual core logic of finding nearest station
        #   It has two sublogics-
        #   1) Nearest station according to user's current location
        #   2) User's bookmarked nearest station according to
        #       user's current location

        def get_queryset(self):
            # pylint:enable=arguments-differ
            """get quryset method"""
            # These are the query params we will be using to extract
            # data from database
            user_latitude = self.request.query_params.get(
                "latitude", 51.145333
            )
            user_longitude = self.request.query_params.get(
                "longitude", -0.979814
            )
            get_bookmarks = self.request.query_params.get(
                "get_bookmarks", None
            )

            # **(Promotions dependency but to avoid code reusability
            # we are using this API)
            # Promotion id will help to filter stations who have the promotions
            promotion_id = self.request.query_params.get("promotion_id", None)

            # **(Promotions dependency but to avoid code reusability
            # we are using this API) Shop id will help to filter stations
            # who have the promotions from the shop whose
            # id is 'shop_id'
            shop_id = self.request.query_params.get("shop_id", None)

            # Fetching all  stations data (it has deleted=NO because
            # we have used soft delete functionality for station )
            queryset = Stations.objects.filter(deleted=NO)
            if promotion_id:
                # Filteration of stations according to promotion available on them.
                queryset = Stations.objects.filter(
                    station_promotions__promotion_id_id=promotion_id,
                    deleted=NO,
                )

            if shop_id:
                # Filteration of stations according to shop id.
                queryset = Stations.objects.filter(
                    station_promotions__promotion_id__shop_ids__contains=shop_id,
                    deleted=NO,
                )

            # The following two lines are used for user's bookmarked stations
            if get_bookmarks and self.request.auth:
                user = self.request.user
                queryset = Stations.objects.filter(
                    user_bookmarks__user_id=user,
                    user_bookmarks__bookmark_status="bookmarked",
                )

            # This function calculates the distance between station
            # and user current location
            if user_latitude and user_longitude:
                user_latitude = float(user_latitude)
                user_longitude = float(user_longitude)

                def get_station_distance_station(station):
                    return get_station_distance(
                        station, user_latitude, user_latitude
                    )

                # Sorting of queryset according to user's current location

                queryset = sorted(queryset, key=get_station_distance_station)

                def station_filter_distance(station):
                    """filter station"""
                    distance = get_distance(
                        {
                            "latitude": station.latitude,
                            "longitude": station.longitude,
                        },
                        {
                            "latitude": user_latitude,
                            "longitude": user_longitude,
                        },
                    )
                    return bool(distance < RADIUS)

                # Sorting of queryset according to user's current location

                queryset = filter(station_filter_distance, queryset)
                queryset = list(queryset)
            return queryset

    except COMMON_ERRORS as exception:
        print(
            f"Station Finder Radius ViewSet failed due to exception -> \
                {exception}"
        )


# # This API is used to fetched details of particular station
class StationDetailsAPI(APIView):
    """station details vieset api"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, station_details_request):
        """get method to fetch station finder stations"""
        try:
            if not station_details_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                station_details_request.user.id, station_details_request.auth
            ):
                return MULTIPLE_LOGIN
            station_id = self.request.query_params.get("station_id", None)
            # data taking from cache
            cache_data = redis_connection.get(f"station-info-{station_id}")
            if (
                cache_data is not None
                and cache_data != b""
                and cache_data != b"[]"
                and cache_data != b"Not Available"
            ):
                data = cache_data.decode("utf-8")
                data_from_cache = json.loads(data)
                if (
                    "site_id" in data_from_cache
                    and data_from_cache["site_id"] is not None
                    and data_from_cache["site_id"] != ""
                ):
                    if data_from_cache["status"] == COMING_SOON_CONST:
                        return Response(
                            {
                                "status_code": status.HTTP_200_OK,
                                "status": False,
                                "message": "Station is not active now.",
                            }
                        )
                    # get valid loyalties
                    station_loyalties = return_station_loyalties(
                        None,
                        station_id,
                        station_details_request.user,
                        False,
                    )
                    data_from_cache["station_loyalties"]=station_loyalties
                    
                    # sending site id in driivz request
                    response = location_data_api(data_from_cache["site_id"])
                    if response.status_code == 200:
                        data_from_cache = updating_tariff(
                            response.content, data_from_cache
                        )
                        redis_connection.set(
                            f"station-info-{station_id}",
                            array_to_string_converter(data_from_cache),
                        )
                    user_bookmark = Bookmarks.objects.filter(
                        bookmarked_station_id=station_id,
                        user_id_id=station_details_request.user.id,
                    )
                    data_from_cache["bookmark_status"] = bool(
                        user_bookmark.first()
                        and user_bookmark.first().bookmark_status
                        == "bookmarked"
                    )
                    if data_from_cache["is_ev"] is True:
                        data_from_cache["preauthorize_money_ev"] = float(
                            filter_function_for_base_configuration(
                                "preauthorize_money_ev", 0
                            )
                        )
                        data_from_cache[
                            "wallet_preauthorize_money_ev"
                        ] = float(
                            filter_function_for_base_configuration(
                                "wallet_preauthorize_money_ev", 0
                            )
                        )
                    else:
                        data_from_cache["preauthorize_money_ev"] = False
                        data_from_cache["wallet_preauthorize_money_ev"] = False

                    return Response(
                        {
                            "status_code": status.HTTP_200_OK,
                            "status": True,
                            "message": "Fetched stations.",
                            "data": data_from_cache,
                        }
                    )

            # Data taking from database if not in cache
            queryset = Stations.objects.filter(
                id__exact=station_id,
                deleted=NO,
                status__in=ACTIVE_STATION_STATUSES,
            ).first()
            if queryset is not None and queryset.status == COMING_SOON_CONST:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": False,
                        "message": "Station is not active now.",
                    }
                )
            if queryset is not None:
                promotions_details = StationDetailSerializer(queryset)
                station_loyalties = return_station_loyalties(
                    None,
                    station_id,
                    station_details_request.user,
                    False,
                )
                stations_basic_details = StationSerializer(
                    queryset,
                    context={
                        "user_id": station_details_request.user.id,
                        "is_detail_api": True,
                    },
                )
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "Fetched stations.",
                        "data": {
                            **promotions_details.data,
                            **stations_basic_details.data,
                            "station_loyalties":station_loyalties,
                            "preauthorize_money_ev": float(
                                filter_function_for_base_configuration(
                                    "preauthorize_money_ev", 0
                                )
                            )
                            if stations_basic_details.data["is_ev"] is True
                            else False,
                            "wallet_preauthorize_money_ev": float(
                                filter_function_for_base_configuration(
                                    "wallet_preauthorize_money_ev", 0
                                )
                            )
                            if stations_basic_details.data["is_ev"] is True
                            else False,
                        },
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "status": False,
                    "message": "Station with provided id not found.",
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Station Details API failed for user -> \
                    {station_details_request.user.id} due to exception -> \
                        {exception}"
            )
            return API_ERROR_OBJECT


# This API will return list of all map markers with there names
class IconsAPI(APIView):
    """icons api"""

    # Permission classes are used to restrict the user
    permission_classes = [permissions.AllowAny]

    @classmethod
    def get(cls, request):
        """return icon information"""
        try:
            brands = []
            speeds = []
            connector_list = []
            ev_statuses = []
            others = []
            # speed_list = [MFG_RAPID, MFG_NORMAL, OTHER_RAPID, OTHER_NORMAL]
            speed_list = [MFG_RAPID, MFG_NORMAL]
            icons_from_cache = redis_connection.get("icons_from_cache")

            if icons_from_cache and icons_from_cache.decode("utf-8") != "null":
                icons_data = string_to_array_converter(
                    icons_from_cache.decode("utf-8")
                )[0]
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "Fetched list of icons.",
                        "data": icons_data,
                    }
                )
            station_brands = [
                station["brand"]
                for station in Stations.objects.all()
                .values("brand")
                .distinct()
            ]
            markers = MapMarkerConfigurations.objects.all()
            brands = [
                {
                    "name": marker.map_marker_key,
                    "image": marker.get_image_path(),
                }
                for marker in markers
                if marker.map_marker_key in station_brands
            ]
            speeds = [
                {
                    "name": marker.map_marker_key,
                    "image": marker.get_image_path(),
                }
                for marker in markers
                if marker.map_marker_key in speed_list
            ]

            connectors = ConnectorConfiguration.objects.all().order_by(
                "sorting_order"
            )
            for connector in connectors:
                connector_list.append(
                    {
                        "name": connector.connector_plug_type,
                        "image": connector.get_image_path(),
                    }
                )
            coming_soon_marker = MapMarkerConfigurations.objects.filter(
                map_marker_key="-".join(COMING_SOON_CONST.split(" "))
            ).first()
            if coming_soon_marker:
                others.append(
                    {
                        "name": COMING_SOON_CONST,
                        "image": coming_soon_marker.get_image_path(),
                    }
                )

            ev_status_list = [
                "Available",
                "Occupied",
                "Unknown",
                "Loading",
            ]
            for speed in speed_list:
                for ev_status in ev_status_list:
                    ev_statuses.append(
                        {
                            "status": f"{speed}-{ev_status}",
                            "icon": MapMarkerConfigurations.objects.filter(
                                map_marker_key=f"{speed}-{ev_status}"
                            )
                            .first()
                            .get_image_path(),
                        }
                    )

            redis_connection.set(
                "icons_from_cache",
                array_to_string_converter(
                    [
                        {
                            "speed_markers": speeds,
                            "brand_markers": brands,
                            "connector_markers": connector_list,
                            "ev_status": ev_statuses,
                            "others": others,
                        }
                    ]
                ),
            )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Fetched list of icons.",
                    "data": {
                        "speed_markers": speeds,
                        "brand_markers": brands,
                        "connector_markers": connector_list,
                        "ev_status": ev_statuses,
                        "others": others,
                    },
                }
            )

        except COMMON_ERRORS as exception:
            print(
                f"Icons API failed for user -> {request.user.id}\
                      due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


# This API will be used to submit the review for particular station


class ReviewPostAPI(APIView):
    """This class view takes data and create review row in the database"""

    # This post() function is used to make the post action to API
    @classmethod
    def post(cls, review_post_request):
        """post request to add review"""
        try:
            # Data required to submit the review.
            station_id = review_post_request.data.get("station_id", None)
            review = review_post_request.data.get("review", None)

            # If bearer token is passed to API then we can get
            # the current user with request.user
            user = review_post_request.user
            # Based on user status of authentication we will perform queries
            # the request.auth returns null if user is not authenticated
            if not review_post_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                review_post_request.user.id, review_post_request.auth
            ):
                return MULTIPLE_LOGIN

            # Condition to check data require to make a review is
            # passed to API or not.
            if station_id is None or review is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Please provide valid data",
                    }
                )
            # Checking whether the station with provided id is
            # present in database or not.
            try:
                station = Stations.objects.get(id=station_id)
            except ObjectDoesNotExist:
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "status": False,
                        "message": "No such station exists",
                    }
                )

            if station.status == COMING_SOON_CONST:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            "Cant add reviews on coming soon stations."
                        ),
                    }
                )

            # The flag_status will be set to True if user entered any
            # bad words or
            # abussive words.
            flag_status = profanity.contains_profanity(review)
            # Checking whether image is provided for review
            #   if yes ,then -
            #       The image which will come from API query param is in base64
            #       format so wehave to convert the image to file so that we
            #       can upload that to database
            #   if no , then -
            #       we wont pass any image parameter in temp data and it will
            #       be set tu null in database.

            temp_data = {
                "user_id": user.id,
                "station_id": station_id,
                "review": review,
                "flag": YES if flag_status else NO,
                "status": "pending",
                "post_date": timezone.localtime(timezone.now()),
            }
            # The insert operation through serializer is done by following code
            serializer = ReviewsSerializer(data=temp_data)
            serializer.is_valid(raise_exception=True)
            review = serializer.save()

            # Condition to check whether review
            # is submitted successfully or not.
            if review:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "Thanks for sharing review. We will \
                            post it once it's  been verified.",
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                    "status": False,
                    "message": "Review not submitted.",
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Review Post API failed for user -> \
                    {review_post_request.user.id} due to exception -> \
                        {exception}"
            )
            return API_ERROR_OBJECT


# This API will return all the data to make filter operation
# on station list data station finder


class FilterDataList(APIView):
    """This class view returns list of data we can use for
    filtering stations data"""

    # permission_classes = [permissions.IsAuthenticated]

    @classmethod
    def get(cls, _):
        """get filter list"""
        try:
            # List declaration to append data
            amenities = []
            shops = []
            connectors = []
            charging_types = []
            brands = []
            data = redis_connection.get("station_finder_filter_list")
            if data and data.decode("utf-8") != "null":
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "successfully loaded filter data",
                        "data": string_to_array_converter(
                            data.decode("utf-8")
                        )[0],
                    }
                )
            # Database call to get all the brands available on station. \
            # (This query returns unique brand names list)
            fuel_brands = Stations.objects.values("brand").distinct()

            for i in fuel_brands:
                if i["brand"] != "nan" and len(i["brand"]) > 0:
                    brands.append(
                        {
                            "brand": i["brand"],
                            "brand_logo": (
                                MapMarkerConfigurations.objects.filter(
                                    map_marker_key=i["brand"]
                                )
                                .first()
                                .get_image_path()
                            ),
                        }
                    )
            # end brands query

            # Database call to get all the services and we have shops
            # and amenities in same database so we are
            # separating them with if condition
            services = ServiceConfiguration.objects.filter(
                ~Q(image_path=None),
                id__in=StationServices.objects.filter(deleted=NO)
                .values_list("service_id_id", flat=True)
                .distinct(),
            )
            for i in services:
                if i.service_type == "Amenity":
                    if i.image_path_with_text is not None:
                        amenities.append(
                            {
                                "service": i.service_name,
                                "image": i.get_image_path_with_text(),
                            }
                        )
                else:
                    shops.append(
                        {
                            "service": i.service_name,
                            "image": i.get_image_path(),
                        }
                    )

            # end services query

            # Database call to get charging speed of connectors.
            # (This query returns list
            # containing unique values of connector speed)
            connectors_db = ConnectorConfiguration.objects.filter(
                connector_plug_type__in=StationConnector.objects.filter(
                    deleted=NO, status=ACTIVE
                )
                .values_list("plug_type_name", flat=True)
                .distinct()
            ).order_by("sorting_order")
            for i in connectors_db:
                connectors.append(
                    {
                        "connector_type": i.connector_plug_type,
                        "image": i.get_image_path(),
                    }
                )
            # end connectors query

            (
                mfg_rapid_count,
                mfg_normal_count,
                other_rapid_count,
                other_normal_count,
            ) = get_devices_speed()
            if mfg_rapid_count > 0:
                charging_types.append(
                    {
                        "charging_type": MFG_RAPID,
                        "image": MapMarkerConfigurations.objects.get(
                            map_marker_key=MFG_RAPID
                        ).get_image_path(),
                    }
                )
            if mfg_normal_count > 0:
                charging_types.append(
                    {
                        "charging_type": MFG_NORMAL,
                        "image": MapMarkerConfigurations.objects.get(
                            map_marker_key=MFG_NORMAL
                        ).get_image_path(),
                    }
                )
            if other_rapid_count > 0:
                charging_types.append(
                    {
                        "charging_type": OTHER_RAPID,
                        "image": MapMarkerConfigurations.objects.get(
                            map_marker_key=OTHER_RAPID
                        ).get_image_path(),
                    }
                )
            if other_normal_count > 0:
                charging_types.append(
                    {
                        "charging_type": OTHER_NORMAL,
                        "image": MapMarkerConfigurations.objects.get(
                            map_marker_key=OTHER_NORMAL
                        ).get_image_path(),
                    }
                )

            redis_connection.set(
                "station_finder_filter_list",
                array_to_string_converter(
                    [
                        {
                            "fuel_brands": brands,
                            "shops": shops,
                            "amenities": amenities,
                            "charging_types": charging_types,
                            "connectors": connectors,
                        }
                    ]
                ),
            )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "successfully loaded filter data",
                    "data": {
                        "fuel_brands": brands,
                        "shops": shops,
                        "amenities": amenities,
                        "charging_types": charging_types,
                        "connectors": connectors,
                    },
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Filter Data List API failed due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


# Bookmark API (this API bookmark a station for current user)
class BookmarkStationAPI(APIView):
    """This class view API helps user to add his bookmark stations"""

    # This post() function is used to make the post action to API
    @classmethod
    def post(cls, bookmark_request):
        """post method to bookmark station"""
        try:
            # Station_id will be required to bookmark a station
            station_id = bookmark_request.data.get("station_id", None)

            # If bearer token is passed to API then we can get the
            # current user with request.user
            user = bookmark_request.user

            # Based on user status of authentication we will perform queries
            # the request.auth returns null if user is not authenticated
            if not bookmark_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                bookmark_request.user.id, bookmark_request.auth
            ):
                return MULTIPLE_LOGIN

            if station_id is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Please provide valid data",
                    }
                )

            # Checking whether station with given id exists or not
            try:
                station = Stations.objects.get(id=station_id)
            except ObjectDoesNotExist:
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "status": False,
                        "message": "No such station exists",
                    }
                )

            temp_data = {
                "user_id": user.id,
                "bookmarked_station_id": station_id,
                "bookmark_status": "bookmarked",
                "created_date": timezone.localtime(timezone.now()),
            }

            bookmarks = Bookmarks.objects.filter(
                user_id=user, bookmarked_station_id=station
            )

            # check user has previous bookmark for station or not
            bookmarked_status = False
            if bookmarks.first():
                if bookmarks.first().bookmark_status == "bookmarked":
                    bookmarked_status = False
                    bookmarked = bookmarks.update(
                        bookmark_status="bookmarked-removed",
                        updated_date=timezone.localtime(timezone.now()),
                    )
                else:
                    bookmarked_status = True
                    bookmarked = bookmarks.update(
                        bookmark_status="bookmarked",
                        updated_date=timezone.localtime(timezone.now()),
                    )
            else:
                bookmarked_status = True
                # The insert operation through serializer is done by
                # following code
                serializer = BookmarksSerializer(data=temp_data)
                serializer.is_valid(raise_exception=True)
                bookmarked = serializer.save()

            # Condition to checked whether bookmark is successful or not.
            if not bookmarked:
                return Response(
                    {
                        "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                        "status": False,
                        "message": "Bookmark failed.",
                        "bookmark_status": False,
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Station added to favourite successfully!."
                    if bookmarked_status
                    else "Station removed from favourite successfully!.",
                    "bookmark_status": bookmarked_status,
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Bookmark Station API failed for user -> \
                {bookmark_request.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT
