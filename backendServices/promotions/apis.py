"""promotions apis"""
# Date - 26/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on APIs
#                       related to promotions.
#   Name            - Promotions API
#   Modified by     - Shivkumar Kumbhar
#   Modified date   - 29/03/2023


# These are all the imports that we are exporting from
# different module's from project or library.

from datetime import datetime
import googlemaps
from decouple import config

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from django.db.models import Q
from django.utils import timezone

# pylint:disable=import-error
from sharedServices.common import (
    PROMOTION_RADIUS,
    array_to_string_converter,
    get_distance,
    get_station_distance,
    string_to_array_converter,
    redis_connection,
)
from sharedServices.constants import (
    DEFAULT_LATITUDE_FOR_PROMOTIONS_AND_STATION_FINDER,
    DEFAULT_LONGITUDE_FOR_PROMOTIONS_AND_STATION_FINDER,
    NO,
    SUCCESS_PROMOTIONS,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
)
from sharedServices.model_files.promotions_models import (
    Promotions,
    PromotionsAvailableOn,
)

from sharedServices.model_files.station_models import (
    Stations,
)
from sharedServices.model_files.config_models import (
    ServiceConfiguration,
)

from .serializers import (
    PromotionsSerializers,
)
from .app_level_constants import END_TIME

gmaps = googlemaps.Client(key=config("DJANGO_APP_GOOGLE_API_KEY"))


# This API will be used to fetched the promotions details
class PromotionDetailViewSet(APIView):
    """promotion detail api viewset"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """get promotion details"""
        try:
            # Promotion id will be taken from query params and
            # used to get the particular promotion
            user_latitude = self.request.query_params.get("latitude", False)
            user_longitude = self.request.query_params.get("longitude", False)

            promotion_id = self.request.query_params.get("promotion_id", False)

            if user_latitude and user_longitude:
                user_latitude = float(user_latitude)
                user_longitude = float(user_longitude)
            else:
                user_latitude = float(
                    DEFAULT_LATITUDE_FOR_PROMOTIONS_AND_STATION_FINDER
                )
                user_longitude = float(
                    DEFAULT_LONGITUDE_FOR_PROMOTIONS_AND_STATION_FINDER
                )
            if promotion_id is False:
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": "Please provide valid data",
                    }
                )
            try:
                queryset = Promotions.objects.filter(
                    id__exact=promotion_id,
                    status="Active",
                    end_date__gte=timezone.localtime(timezone.now()),
                    start_date__lte=timezone.localtime(timezone.now()),
                    deleted=NO,
                )
                promotions = []
                promotion_stations = PromotionsAvailableOn.objects.filter(
                    promotion_id_id=promotion_id,
                    promotion_id__status="Active",
                    promotion_id__end_date__gte=timezone.localtime(
                        timezone.now()
                    ),
                    promotion_id__start_date__lte=timezone.localtime(
                        timezone.now()
                    ),
                    promotion_id__deleted=NO,
                    deleted=NO,
                ).values(
                    "station_id_id",
                    "station_id__latitude",
                    "station_id__longitude",
                )

                def get_station_distance_promotion(station):
                    return get_station_distance(
                        station, user_latitude, user_longitude
                    )

                promotion_stations = sorted(
                    list(
                        map(
                            lambda station: {
                                "latitude": station["station_id__latitude"],
                                "longitude": station["station_id__longitude"],
                                "station_id_id": station["station_id_id"],
                            },
                            promotion_stations,
                        )
                    ),
                    key=get_station_distance_promotion,
                )
                station_id = None
                if len(promotion_stations) > 0:
                    station_id = promotion_stations[0]["station_id_id"]
                    station_promotions = (
                        Promotions.objects.filter(
                            ~Q(id=queryset.first().id),
                            ~Q(image=None),
                            station_available_promotions__station_id_id=(
                                station_id
                            ),
                            station_available_promotions__deleted=NO,
                            deleted=NO,
                            status="Active",
                            end_date__gte=timezone.localtime(timezone.now()),
                            start_date__lte=timezone.localtime(timezone.now()),
                        )
                        .values("id", "image")
                        .distinct()
                    )

                    for promotion in station_promotions:
                        promotion["image"] = (
                            config("DJANGO_APP_CDN_BASE_URL")
                            + promotion["image"]
                        )
                    if len(station_promotions) > 0:
                        promotions = list(station_promotions)

                serializer = PromotionsSerializers(
                    queryset.first(), context={"station_id": station_id}
                )
            except AttributeError:
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": "Something went wrong.",
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": SUCCESS_PROMOTIONS,
                    "data": {
                        "promotion_data": serializer.data,
                        "other_promotions": promotions,
                    },
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Promotion Detail ViewSet API failed for user -> \
                    {request.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


# This API will be used to fetched the promotions for
# particular station in directions.


class PromotionFromStation(APIView):
    """promotions by stations api"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """get promotions by available on station"""
        try:
            # Station id will be used to fetch promotions from that station.
            station_id = self.request.query_params.get("station_id", None)

            station = Stations.objects.filter(id=station_id)
            if station_id is None and station.first() is None:
                return Response(
                    {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "status": False,
                        "message": "Please provide valid data",
                    }
                )

            promotions = []
            station_promotions = (
                Promotions.objects.filter(
                    ~Q(image=None),
                    station_available_promotions__station_id_id=station_id,
                    station_available_promotions__deleted=NO,
                    deleted=NO,
                    status="Active",
                    end_date__gte=timezone.localtime(timezone.now()),
                    start_date__lte=timezone.localtime(timezone.now()),
                )
                .values("id", "image")
                .distinct()
            )
            if len(station_promotions):
                promotions = list(station_promotions)

            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": SUCCESS_PROMOTIONS,
                    "data": {
                        "station_detail": f"{station.first().station_id},\
                            {station.first().station_name}",
                        "prommotion": promotions,
                    },
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Promotion From Station API failed for user -> \
                    {request.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


def promotions_api_query_set_data():
    """get promotions data from promotions table queryset"""
    api_promotions_promotion_data = redis_connection.get(
        "api_promotions_promotion_data"
    )
    if (
        api_promotions_promotion_data
        and api_promotions_promotion_data.decode("utf-8") != "null"
    ):
        promotion_data = string_to_array_converter(
            api_promotions_promotion_data.decode("utf-8")
        )
    else:
        promotion_data = []
        promotion_qs = (
            Promotions.objects.filter(
                ~Q(image=None),
                station_available_promotions__deleted=NO,
                deleted=NO,
                status="Active",
            )
            .values("id", "image", "end_date", "start_date", "shop_ids")
            .distinct()
        )
        promotions_array = [
            {
                "id": promotion["id"],
                "image": promotion["image"],
                "end_date": promotion["end_date"].date().strftime("%d/%m/%Y"),
                "start_date": promotion["start_date"]
                .date()
                .strftime("%d/%m/%Y"),
                "shops": string_to_array_converter(promotion["shop_ids"]),
            }
            for promotion in promotion_qs
        ]
        promotions_station_qs = list(
            Promotions.objects.filter(
                ~Q(image=None),
                station_available_promotions__deleted=NO,
                deleted=NO,
                status="Active",
            )
            .values(
                "id",
                "image",
                "station_available_promotions__station_id_id",
                "station_available_promotions__station_id__latitude",
                "station_available_promotions__station_id__longitude",
            )
            .distinct()
        )
        promotion_data = [promotions_array, promotions_station_qs]

        redis_connection.set(
            "api_promotions_promotion_data",
            array_to_string_converter(list(promotion_data)),
        )

    return promotion_data


def return_promotion_availale_stations_list():
    """returns promotions available stations list"""
    redis_connection.set(
        "api_promotions_promotion_data", array_to_string_converter(None)
    )
    local_time = timezone.localtime(timezone.now())
    return (
        Stations.objects.filter(
            deleted=NO,
            station_promotions__promotion_id__status="Active",
            station_promotions__deleted=NO,
            station_promotions__promotion_id__deleted=NO,
            station_promotions__promotion_id__end_date__gte=local_time,
            station_promotions__promotion_id__start_date__lte=local_time,
        )
        .values("id", "station_name", "latitude", "longitude")
        .distinct()
    )


# Under development API
# This API will return all data related to promotions
# tab on home page of MFG EV app.


class PromotionsAPIViewset(APIView):
    """promotions deals api"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """get promotion deals"""
        try:
            # User co-ordinates passed in query params, to fetch nearby
            # stations's promotions
            user_latitude = self.request.query_params.get("latitude", False)
            user_longitude = self.request.query_params.get("longitude", False)

            if user_latitude and user_longitude:
                user_latitude = float(user_latitude)
                user_longitude = float(user_longitude)
            else:
                user_latitude = float(
                    DEFAULT_LATITUDE_FOR_PROMOTIONS_AND_STATION_FINDER
                )
                user_longitude = float(
                    DEFAULT_LONGITUDE_FOR_PROMOTIONS_AND_STATION_FINDER
                )
            api_promotions_stations_data = redis_connection.get(
                "api_promotions_stations"
            )
            if (
                api_promotions_stations_data
                and api_promotions_stations_data.decode("utf-8") != "null"
            ):
                stations = string_to_array_converter(
                    api_promotions_stations_data.decode("utf-8")
                )
            else:
                stations = return_promotion_availale_stations_list()
                redis_connection.set(
                    "api_promotions_stations",
                    array_to_string_converter(list(stations)),
                )

            def get_station_distance_promotion(station):
                return get_station_distance(
                    station, user_latitude, user_longitude
                )

            # location (nearest-farest)
            stations = sorted(
                list(
                    filter(
                        lambda station: (
                            get_distance(
                                {
                                    "latitude": station["latitude"],
                                    "longitude": station["longitude"],
                                },
                                {
                                    "latitude": user_latitude,
                                    "longitude": user_longitude,
                                },
                            )
                            <= PROMOTION_RADIUS
                        ),
                        stations,
                    )
                ),
                key=get_station_distance_promotion,
            )
            promotion_qs, promotion_assign_qs = promotions_api_query_set_data()

            nearest_station = None
            if len(stations) > 0:
                nearest_station = stations[0]
            # Fetching promotions of nearest station
            nearest_promotions = []

            def get_newest_promotions(promotion):
                """this function is used to return start date of
                promotion for sorting"""
                return datetime.strptime(promotion["start_date"], "%d/%m/%Y")

            if nearest_station:
                nearby_station_promotion = list(
                    filter(
                        lambda promotion: (
                            promotion[
                                "station_available_promotions__station_id_id"
                            ]
                            == nearest_station["id"]
                        ),
                        promotion_assign_qs,
                    )
                )
                nearby_station_promotion_ids = [
                    promotion["id"] for promotion in nearby_station_promotion
                ]
                nearest_promotions = sorted(
                    list(
                        filter(
                            lambda promotion: (
                                promotion["id"] in nearby_station_promotion_ids
                                and datetime.strptime(
                                    f'{promotion["end_date"]} {END_TIME}',
                                    "%d/%m/%Y %H:%M:%S",
                                )
                                >= timezone.localtime(timezone.now()).replace(
                                    tzinfo=None
                                )
                                and datetime.strptime(
                                    promotion["start_date"], "%d/%m/%Y"
                                )
                                <= timezone.localtime(timezone.now()).replace(
                                    tzinfo=None
                                )
                            ),
                            promotion_qs,
                        )
                    ),
                    key=get_newest_promotions,
                )

            deals = []
            deals_promotion = list(
                filter(
                    lambda promotion: (
                        promotion[
                            "station_available_promotions__station_id_id"
                        ]
                        in [st["id"] for st in stations]
                    ),
                    promotion_assign_qs,
                )
            )

            deals_promotion_ids = [
                promotion["id"] for promotion in deals_promotion
            ]
            deal = sorted(
                list(
                    filter(
                        lambda promotion: (
                            promotion["id"] in deals_promotion_ids
                            and datetime.strptime(
                                f'{promotion["end_date"]} {END_TIME}',
                                "%d/%m/%Y %H:%M:%S",
                            )
                            >= timezone.localtime(timezone.now()).replace(
                                tzinfo=None
                            )
                            and datetime.strptime(
                                promotion["start_date"], "%d/%m/%Y"
                            )
                            <= timezone.localtime(timezone.now()).replace(
                                tzinfo=None
                            )
                        ),
                        promotion_qs,
                    )
                ),
                key=get_newest_promotions,
            )

            if len(deal) > 0:
                deals = list(deal)
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": SUCCESS_PROMOTIONS,
                    "data": {
                        "nearby_promotions": nearest_promotions,
                        "promotions": deals,
                    },
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Promotions API Viewset failed for user -> \
                    {request.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


class PromotionsFiltersAPIViewset(APIView):
    """Promotions filter API"""

    permission_classes = [IsAuthenticated]

    @classmethod
    def get(cls, request):
        """get api to fetch filters"""
        try:
            services = ServiceConfiguration.objects.filter(
                ~Q(service_type="Amenity", image_path=None)
            )

            shops = [
                {
                    "shop_name": service.service_name,
                    "image": service.get_image_path(),
                }
                for service in services
            ]

            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "successfully fetched promotion filters",
                    "data": {
                        "shops": shops,
                    },
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Promotions Filters API Viewset failed for user -> \
                    {request.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT
