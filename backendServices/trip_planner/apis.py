"""trip planner apis"""
# Date - 21/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on APIs related
#                       to Trip planner data.
#   Name            - Trip planner APIs
#   Modified by     - Shivkumar Kumbhar
#   Modified date   - 21/06/2021


# These are all the imports that we are exporting from
# different module's from project or library.
import googlemaps
from decouple import config
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.core.exceptions import RequestAborted
from django.db.models import Q

# pylint:disable=import-error
from sharedServices.model_files.promotions_models import Promotions
from sharedServices.model_files.config_models import (
    ServiceConfiguration,
    MapMarkerConfigurations,
)
from sharedServices.model_files.station_models import Stations
from sharedServices.model_files.trip_models import Trips
from sharedServices.common import (
    array_to_string_converter,
    handle_concurrent_user_login,
    redis_connection,
    string_to_array_converter,
    time_formatter_for_hours,
)
from sharedServices.constants import (
    SOMETHING_WRONG,
    YES,
    NO,
    COMMON_ERRORS,
    GMAP_ERRORS,
    API_ERROR_OBJECT,
    IS_EV_KEYS,
)
from sharedServices.shared_station_serializer import StationSerializer
from backendServices.backend_app_constants import (
    INVALID_TRIP_ID,
    MULTIPLE_LOGIN,
    TRIP_ID_NOT_PROVIDED,
    TRIP_NOT_FOUND,
    UNAUTHORIZED,
)
from .serializers import AddTripsSerializer, TripsSerializer
from .trips_helper_functions import (
    decode_polyline,
    foreign_key_extracter,
    filter_stations_for_trips,
    get_trip_planner_routes,
    get_location_cord,
)

gmaps = googlemaps.Client(key=config("DJANGO_APP_GOOGLE_API_KEY"))


class FilterListForTripPlanner(APIView):
    """This class view API fetches filter list of stations_trip"""

    permission_classes = [
        IsAuthenticated,
    ]

    @classmethod
    def get(cls, filter_trip_request):
        """get metho for fetching filters"""
        try:
            if not filter_trip_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                filter_trip_request.user.id, filter_trip_request.auth
            ):
                return MULTIPLE_LOGIN
            trip_id = filter_trip_request.data.get("trip_id", False)
            stations_trip = Stations.objects.filter(deleted=NO)
            filters = foreign_key_extracter(
                [station.id for station in stations_trip]
            )
            if trip_id:
                trips = Trips.objects.filter(
                    id=trip_id, user_id=filter_trip_request.user
                )
                if trips.first():
                    trip_data = trips.first().trip_data
                    trip_data = string_to_array_converter(trip_data)
                    filters["add_stop_automatically"] = trip_data[1][
                        "add_stops"
                    ]
                    filters["ev_range"] = trips.first().ev_range
                    filters[
                        "state_of_charge"
                    ] = trips.first().ev_current_battery
                    filters[
                        "station_distance"
                    ] = trips.first().station_distance
                    filters["start_formatted_adrress"] = gmaps.reverse_geocode(
                        trips.first().source
                    )[0]["formatted_address"]
                    filters[
                        "destination_formatted_adrress"
                    ] = gmaps.reverse_geocode(trips.first().destination)[0][
                        "formatted_address"
                    ]
                    filters["start_place_id"] = trips.first().source
                    filters["end_place_id"] = trips.first().destination

                    store_ids = string_to_array_converter(
                        trips.first().store_id
                    )

                    for store in filters["stores"]:
                        if store["id"] in store_ids:
                            store["applied"] = True

                    amenity_ids = string_to_array_converter(
                        trips.first().amenity_id
                    )

                    for amenity in filters["amenities"]:
                        if amenity["id"] in amenity_ids:
                            amenity["applied"] = True

                    connector_type_ids = string_to_array_converter(
                        trips.first().connector_type_id
                    )

                    for connector_type in filters["connector_types"]:
                        if connector_type["connectors"] in connector_type_ids:
                            connector_type["applied"] = True

                    charging_types = string_to_array_converter(
                        trips.first().charging_types
                    )

                    for charging_type in filters["charging_types"]:
                        if charging_type["charging_type"] in charging_types:
                            charging_type["applied"] = True

                    filters["trip_options_filter"] = string_to_array_converter(
                        trips.first().trip_options_filter
                    )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Successfully fetched filters",
                    "data": filters,
                }
            )
        except COMMON_ERRORS + GMAP_ERRORS as exception:
            print(
                f"Filter List For Trip Planner failed for user -> \
                    {filter_trip_request.user.id} due to exception\
                          -> {exception}"
            )
            return API_ERROR_OBJECT


def sort_location_trip(direction_routes):
    """Sort location"""
    count_chk = 0
    incrementer_chk = 0
    new_direction_routes = []
    while count_chk < len(direction_routes):
        if direction_routes[count_chk]["route_not_able_to_find"] is not True:
            new_direction_routes.append(direction_routes[count_chk])
            incrementer_chk = incrementer_chk + 1
        count_chk = count_chk + 1

    if 0 < incrementer_chk < len(direction_routes):
        direction_routes = []
        direction_routes = new_direction_routes

    def sort_routes(direction):
        return direction["total_duration_for_sorting"]

    sorted_routes = sorted(direction_routes, key=sort_routes)
    placeholder_image = MapMarkerConfigurations.objects.filter(
        map_marker_key="Placeholder"
    )
    return Response(
        {
            "status_code": status.HTTP_200_OK,
            "status": True,
            "message": "Successfully loaded stations_trip!!.",
            "data": {
                "direction_response": sorted_routes,
                "placeholder_image": (
                    placeholder_image.first().get_image_path()
                    if placeholder_image.first()
                    else ""
                ),
            },
        }
    )


# Route finder API


class TripPlannerStations(APIView):
    """This class view API fetches station on a particular route"""

    permission_classes = [
        IsAuthenticated,
    ]
    # This post() function is used to make the post action to API

    @classmethod
    def post(cls, trip_plan_request):
        """post method to ftech all stations_trip on route"""
        try:
            if not trip_plan_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                trip_plan_request.user.id, trip_plan_request.auth
            ):
                return MULTIPLE_LOGIN
            try:
                start_position_place_id = trip_plan_request.data[
                    "start_place_id"
                ]
                end_position_place_id = trip_plan_request.data["end_place_id"]
                is_electric = trip_plan_request.data.get("is_electric", True)
                station_distance_data = int(
                    trip_plan_request.data.get("station_distance", "1")
                )
                ev_range_data = int(
                    trip_plan_request.data.get("ev_range", "100")
                )
                if is_electric:
                    state_of_charge_data = int(
                        trip_plan_request.data.get("state_of_charge", "50")
                    )
                else:
                    state_of_charge_data = 100
                add_stop_automatically = trip_plan_request.data.get(
                    "add_stop_automatically", False
                )
                add_spot_data = trip_plan_request.data.get("add_spot", False)
                add_spot_place_id = trip_plan_request.data.get(
                    "add_spot_place_id", False
                )

                trip_planning_option = trip_plan_request.data[
                    "trip_planning_options"
                ]
                amenity_filters = trip_plan_request.data["amenity_filters"]
                connector_type_filters = trip_plan_request.data[
                    "connector_type_filters"
                ]
                store_filters = trip_plan_request.data["store_filters"]
                charging_type_filters = trip_plan_request.data[
                    "charging_type_filters"
                ]
            except (KeyError, AttributeError):
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Please provide all the data \
                            to find best routes.",
                    }
                )

            if ev_range_data == 0:
                ev_range_data = 100

            # Getting the formated address from place ids
            start_address_data = gmaps.reverse_geocode(
                start_position_place_id
            )[0]["formatted_address"]
            end_address_data = gmaps.reverse_geocode(end_position_place_id)[0][
                "formatted_address"
            ]
            source_coordinate = gmaps.geocode(start_address_data)[0][
                "geometry"
            ]["location"]
            destination_coordinate = gmaps.geocode(end_address_data)[0][
                "geometry"
            ]["location"]
            add_spot_address_data = ""
            direction_response_trip = get_location_cord(
                add_spot_data,
                add_spot_place_id,
                start_address_data,
                end_address_data,
                trip_planning_option,
            )
            if is_electric:
                stations_trip = Stations.objects.filter(
                    station_type__in=IS_EV_KEYS, deleted=NO
                )
            else:
                stations_trip = Stations.objects.filter(
                    ~Q(station_type__in=IS_EV_KEYS), deleted=NO
                )
            stations_trip = filter_stations_for_trips(
                stations_trip,
                amenity_filters,
                connector_type_filters,
                store_filters,
                charging_type_filters,
            )
            # coming from cache
            routes_stations_array = list(
                filter(
                    lambda station: station["id"]
                    in [st.id for st in stations_trip],
                    string_to_array_converter(
                        redis_connection.get(
                            "trip_planner_api_stations"
                        ).decode("utf-8")
                    ),
                )
            )
            direction_routes = get_trip_planner_routes(
                stations_trip,
                routes_stations_array,
                direction_response_trip,
                ev_range_data,
                state_of_charge_data,
                station_distance_data,
                add_spot_data,
                add_spot_address_data,
                start_address_data,
                end_address_data,
                trip_planning_option,
                source_coordinate,
                destination_coordinate,
                add_stop_automatically,
            )
            if len(direction_routes) == 0:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "No routes found for your selection.",
                    }
                )

            return sort_location_trip(direction_routes)
        except COMMON_ERRORS + GMAP_ERRORS as exception:
            print(
                f"Trip Planner Stations failed for user -> \
                    {trip_plan_request.user.id} due to exception -> \
                        {exception}"
            )
            return API_ERROR_OBJECT


class AddTrip(APIView):
    """This class view API helps user to add his trips"""

    # This post() function is used to make the post action to API
    permission_classes = [IsAuthenticated]

    @classmethod
    def post(cls, add_trip_request):
        """add trip post method"""
        try:
            if not add_trip_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                add_trip_request.user.id, add_trip_request.auth
            ):
                return MULTIPLE_LOGIN

            update_trip = add_trip_request.data.get("update_trip", False)
            filters = add_trip_request.data["applied_filters"]
            add_spot_place_id = add_trip_request.data.get(
                "add_spot_place_id", False
            )

            data = {
                "user_id": add_trip_request.user.id,
                "source": add_trip_request.data["source"],
                "destination": add_trip_request.data["destination"],
                "store_id": array_to_string_converter(filters["store_ids"]),
                "amenity_id": array_to_string_converter(
                    filters["amenity_ids"]
                ),
                "charging_types": array_to_string_converter(
                    filters["charging_types"]
                ),
                "miles": add_trip_request.data["miles"],
                "duration": time_formatter_for_hours(
                    int(add_trip_request.data["duration"]) * 60
                ),
                "ev_range": add_trip_request.data["ev_range"],
                "ev_current_battery": add_trip_request.data[
                    "ev_current_battery"
                ],
                "trip_options_filter": array_to_string_converter(
                    filters["trip_planning_options"]
                ),
                "connector_type_id": array_to_string_converter(
                    filters["connector_types"]
                ),
                "add_stop_automatically": YES
                if add_trip_request.data.get("add_stops", False)
                else NO,
                "add_spot_place_id": add_spot_place_id
                if add_spot_place_id
                else "",
                "stations_data": array_to_string_converter(
                    add_trip_request.data["stations_data"]
                ),
                "is_electric": YES
                if add_trip_request.data.get("is_electric", False)
                else NO,
                "saved": YES,
                "created_date": timezone.localtime(timezone.now()),
            }
            message = ""
            if update_trip:
                trip_id = add_trip_request.data.get("trip_id", False)
                if trip_id is False:
                    return TRIP_ID_NOT_PROVIDED

                try:
                    trip_id = int(trip_id)
                except ValueError:
                    return INVALID_TRIP_ID
                trip = Trips.objects.filter(id=trip_id)
                if trip.first() is None:
                    return Response(
                        {
                            "status_code": status.HTTP_404_NOT_FOUND,
                            "status": False,
                            "message": "Trip with provided id not found!",
                        }
                    )
                serializer = AddTripsSerializer(trip.first(), data=data)
                serializer.is_valid(raise_exception=True)
                trip_added = serializer.save()
                message = "Trip updated successfully!!"
            if not update_trip:
                serializer = AddTripsSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                trip_added = serializer.save()

                message = "Trip added successfully!!"
            if trip_added:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": message,
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                    "status": False,
                    "message": SOMETHING_WRONG,
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Add Trip API failed for user -> \
                   {add_trip_request.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


class EditTripdata(APIView):
    """edit trip api view"""

    # This API is used to fetch the user trip details
    permission_classes = [IsAuthenticated]

    @classmethod
    def get(cls, edit_trip_request):
        """get method to fetch edit data"""
        try:
            if not edit_trip_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                edit_trip_request.user.id, edit_trip_request.auth
            ):
                return MULTIPLE_LOGIN
            trip_id = edit_trip_request.data["trip_id"]
            trips = Trips.objects.filter(
                id=trip_id, user_id_id=edit_trip_request.user.id
            )
            if trips.first() is None:
                return Response(
                    {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "status": False,
                        "message": SOMETHING_WRONG,
                    }
                )

            trip_data = string_to_array_converter(trips.first().trip_data)
            station_ids = string_to_array_converter(
                trips.first().stations_data
            )

            start_address_data = gmaps.reverse_geocode(trips.first().source)[
                0
            ]["formatted_address"]
            end_address_data = gmaps.reverse_geocode(
                trips.first().destination
            )[0]["formatted_address"]
            # fetching stores

            road_coords = decode_polyline(trip_data[0]["overview_polyline"])
            route_stations = []
            for station_id in station_ids:
                station = Stations.objects.get(id=station_id)
                promotions_on_stations = Promotions.objects.filter(
                    station_available_promotions__station_id=station,
                    station_available_promotions__deleted=NO,
                    status="Active",
                    end_date__gte=timezone.localtime(timezone.now()),
                    deleted=NO,
                )
                stations_promotions = []
                promotion_available = False
                if len(promotions_on_stations) > 0:
                    promotion_available = True
                    station_promotion = promotions_on_stations.first()
                    shop_ids = string_to_array_converter(
                        station_promotion.shop_ids
                    )

                    service_image = ServiceConfiguration.objects.get(
                        service_name=shop_ids[0]
                    )
                    stations_promotions.append(
                        {
                            "offer_by": service_image.get_image_path(),
                            "promotion_title": (
                                station_promotion.promotion_title
                            ),
                        }
                    )
                route_stations.append(
                    {
                        "id": station.id,
                        "station_id": station.station_id,
                        "station_name": station.station_name,
                        "lat": station.latitude,
                        "lon": station.longitude,
                        "station_address": f"{station.station_address1} ,\
                            {station.station_address2} ,\
                                {station.station_address3}",
                        "promotion_available": promotion_available,
                        "station_promotions": stations_promotions,
                    }
                )

            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": False,
                    "message": "Successfully loaded trip data!!.",
                    "data": {
                        "start_location": start_address_data,
                        "start_place_id": trips.first().source,
                        "destination": end_address_data,
                        "end_place_id": trips.first().destination,
                        "route_distance": trips.first().miles,
                        "route_duration": trips.first().duration,
                        "route_stations": route_stations,
                        "route_data": trip_data,
                        "polyline_points": road_coords,
                    },
                }
            )
        except COMMON_ERRORS + GMAP_ERRORS:
            return API_ERROR_OBJECT

    @classmethod
    def post(cls, edit_trip_post):
        """edit post method"""
        try:
            if not edit_trip_post.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                edit_trip_post.user.id, edit_trip_post.auth
            ):
                return MULTIPLE_LOGIN
            trip_id = edit_trip_post.data["trip_id"]

            trips = Trips.objects.filter(
                user_id_id=edit_trip_post.user.id, id=trip_id
            )
            if trips.first():
                filters = edit_trip_post.data["applied_filters"]
                user_id = edit_trip_post.user.id
                store_id = array_to_string_converter(filters["store_ids"])
                amenity_id = array_to_string_converter(filters["amenity_ids"])
                charging_types = array_to_string_converter(
                    filters["charging_types"]
                )
                trip_options_filter = array_to_string_converter(
                    filters["trip_planning_options"]
                )
                connector_type_id = array_to_string_converter(
                    filters["connector_types"]
                )
                trip_data = array_to_string_converter(
                    [
                        edit_trip_post.data["trip_data"],
                        {"add_stops": edit_trip_post.data["add_stops"]},
                    ]
                )
                stations_data = array_to_string_converter(
                    edit_trip_post.data["stations_data"]
                )
                serializer = AddTripsSerializer(
                    trips,
                    data={
                        "user_id": user_id,
                        "source": edit_trip_post.data["source"],
                        "destination": edit_trip_post.data["destination"],
                        "store_id": store_id,
                        "amenity_id": amenity_id,
                        "charging_types": charging_types,
                        "miles": edit_trip_post.data["miles"],
                        "duration": edit_trip_post.data["duration"],
                        "ev_range": edit_trip_post.data["ev_range"],
                        "ev_current_battery": edit_trip_post.data[
                            "ev_current_battery"
                        ],
                        "trip_options_filter": trip_options_filter,
                        "connector_type_id": connector_type_id,
                        "trip_data": trip_data,
                        "stations_data": stations_data,
                        "saved": YES,
                        "updated_date": timezone.localtime(timezone.now()),
                    },
                    many=True,
                )
                serializer.is_valid(raise_exception=True)
                trip_updated = serializer.save()
                if trip_updated:
                    return Response(
                        {
                            "status_code": status.HTTP_200_OK,
                            "status": True,
                            "message": "Trip updated successfully!!.",
                        }
                    )
            return Response(
                {
                    "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                    "status": False,
                    "message": SOMETHING_WRONG,
                }
            )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT


class GetTripData(APIView):
    """get trip data"""

    permission_classes = [IsAuthenticated]

    # This API is used to fetch the user trip details
    @classmethod
    def post(cls, get_trip_data_request):
        """post method to fetch saved trip data"""
        try:
            if not get_trip_data_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                get_trip_data_request.user.id, get_trip_data_request.auth
            ):
                return MULTIPLE_LOGIN
            trip_id = get_trip_data_request.data.get("trip_id", False)
            if trip_id is False:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Trip id not provided!!",
                    }
                )

            try:
                trip_id = int(trip_id)
            except ValueError:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Provided trip id is not valid!!",
                    }
                )
            trips = Trips.objects.filter(
                id=trip_id, user_id=get_trip_data_request.user
            )
            if trips.first() is None:
                return TRIP_NOT_FOUND

            applied_filters = {
                "store_ids": string_to_array_converter(trips.first().store_id),
                "amenity_ids": string_to_array_converter(
                    trips.first().amenity_id
                ),
                "charging_types": string_to_array_converter(
                    trips.first().charging_types
                ),
                "trip_planning_option": string_to_array_converter(
                    trips.first().trip_options_filter
                ),
                "connector_types": string_to_array_converter(
                    trips.first().connector_type_id
                ),
            }

            station_ids = string_to_array_converter(
                trips.first().stations_data
            )
            start_address_data = gmaps.reverse_geocode(trips.first().source)[
                0
            ]["formatted_address"]
            end_address_data = gmaps.reverse_geocode(
                trips.first().destination
            )[0]["formatted_address"]

            add_spot_address_data = ""
            if len(trips.first().add_spot_place_id) > 0:
                add_spot_address_data = gmaps.reverse_geocode(
                    trips.first().add_spot_place_id
                )[0]["formatted_address"]

            source_coordinate = gmaps.geocode(start_address_data)[0][
                "geometry"
            ]["location"]
            destination_coordinate = gmaps.geocode(end_address_data)[0][
                "geometry"
            ]["location"]
            add_spot_coordinates = None
            if len(add_spot_address_data) > 0:
                add_spot_coordinates = gmaps.geocode(add_spot_address_data)[0][
                    "geometry"
                ]["location"]
            data = {
                "trip_id": trip_id,
                "is_elctric": trips.first().is_electric,
                "source": {
                    "address": start_address_data,
                    "coordinates": source_coordinate,
                    "place_id": trips.first().source,
                },
                "end": {
                    "address": end_address_data,
                    "coordinates": destination_coordinate,
                    "place_id": trips.first().destination,
                },
                "add_spot": {
                    "address": add_spot_address_data,
                    "coordinates": add_spot_coordinates,
                    "place_id": trips.first().add_spot_place_id,
                },
                "route_distance": trips.first().miles,
                "route_duration": trips.first().duration,
                "route_stations": StationSerializer(
                    Stations.objects.filter(id__in=station_ids),
                    many=True,
                    read_only=True,
                ).data,
                "applied_filters": applied_filters,
                "station_distance": trips.first().station_distance,
                "state_of_charge": trips.first().ev_current_battery,
                "ev_range": trips.first().ev_range,
                "add_stops ": trips.first().add_stop_automatically,
            }
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": False,
                    "message": "Successfully loaded trip data!!.",
                    "data": data,
                }
            )
        except COMMON_ERRORS + GMAP_ERRORS as exception:
            print(
                f"Add Trip API failed for user -> \
                    {get_trip_data_request.user.id} due to exception -> \
                        {exception}"
            )
            return API_ERROR_OBJECT


class DeleteTrip(APIView):
    """delete trip API"""

    permission_classes = [IsAuthenticated]

    # This API is used to fetch the user trip details
    @classmethod
    def post(cls, delete_trip_request):
        """post data to delete trip"""
        try:
            if not delete_trip_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                delete_trip_request.user.id, delete_trip_request.auth
            ):
                return MULTIPLE_LOGIN
            trip_id = delete_trip_request.data.get("trip_id", None)
            if trip_id is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Please provide trip id!!.",
                    }
                )
            trip = Trips.objects.filter(id=trip_id)
            if trip.first() is None:
                return Response(
                    {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "status": False,
                        "message": "Trip with provided id not found!!.",
                    }
                )

            trip_deleted = trip.update(deleted=YES)
            if trip_deleted:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": False,
                        "message": "Trip deleted.",
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                    "status": False,
                    "message": SOMETHING_WRONG,
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Delete Trip API failed for user -> \
                    {delete_trip_request.user.id} \
                        due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


class PlannedTripsViewset(APIView):
    """This class view API helps user to access his planned trips"""

    permission_classes = [IsAuthenticated]

    # This post() function is used to make the post action to API
    @classmethod
    def get(cls, planned_trip_request):
        """get method to fetch user's planned trips"""
        try:
            if not planned_trip_request.auth:
                return UNAUTHORIZED
            if not handle_concurrent_user_login(
                planned_trip_request.user.id, planned_trip_request.auth
            ):
                return MULTIPLE_LOGIN
            try:
                user_trips = Trips.objects.filter(
                    user_id=planned_trip_request.user, deleted=NO, saved=YES
                ).order_by("-created_date")
            except (ValueError, RequestAborted):
                return Response(
                    {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "status": False,
                        "message": SOMETHING_WRONG,
                    }
                )

            serializer = TripsSerializer(user_trips, many=True)
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Successfully fetched planned trips!!.",
                    "data": serializer.data,
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Planned Trips Viewset failed for user -> \
                    {planned_trip_request.user.id} due to exception -> \
                        {exception}"
            )
            return API_ERROR_OBJECT


class FavouriteTripsViewset(APIView):
    """This class view API helps user to add his trips"""

    permission_classes = [IsAuthenticated]

    # This post() function is used to make the post action to API
    @classmethod
    def get(cls, favourite_trip_request):
        """get method to fetch users favourite trips"""
        try:
            if not favourite_trip_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                favourite_trip_request.user.id, favourite_trip_request.auth
            ):
                return MULTIPLE_LOGIN
            try:
                user_trips = Trips.objects.filter(
                    user_id=favourite_trip_request.user,
                    deleted=NO,
                    saved=YES,
                    favourite=YES,
                ).order_by("-created_date")
            except (ValueError, RequestAborted):
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": SOMETHING_WRONG,
                    }
                )

            serializer = TripsSerializer(user_trips, many=True)

            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Successfully fetched fevourite trips!!.",
                    "data": serializer.data,
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Favourite Trips Viewset failed for user -> \
                    {favourite_trip_request.user.id} due to exception \
                        -> {exception}"
            )
            return API_ERROR_OBJECT


class AddTripToFavouritesAPI(APIView):
    """This class view API helps user to add his trips to favourites"""

    permission_classes = [IsAuthenticated]

    # This post() function is used to make the post action to API
    @classmethod
    def post(cls, add_trip_request):
        """post method to add user trip to favourite"""
        try:
            if not add_trip_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                add_trip_request.user.id, add_trip_request.auth
            ):
                return MULTIPLE_LOGIN
            # trip_id will be required to add trips in favourites
            trip_id = add_trip_request.data.get("trip_id")
            trip = Trips.objects.filter(
                id__exact=int(trip_id), user_id=add_trip_request.user
            )
            if trip.first():
                if trip.first().favourite == YES:
                    trip.update(favourite=NO)
                else:
                    trip.update(favourite=YES)

                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "Trip added to favourites successfully!!.",
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                    "status": False,
                    "message": SOMETHING_WRONG,
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Add Trip To Favourites API failed for user -> \
                    {add_trip_request.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT
