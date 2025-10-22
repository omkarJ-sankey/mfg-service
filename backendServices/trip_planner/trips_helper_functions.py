"""trip planner helper functions"""
# Date - 31/01/2022


# File details-
#   Author          - Manish Pawar
#   Description     - This file contains helper functions for trip planner.
#   Name            - Trip planner APIs
#   Modified by     - Manish Pawar
#   Modified date   - 31/01/2022


# These are all the imports that we are exporting from
# different module's from project or library.
import collections
import googlemaps
from decouple import config
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.response import Response

# pylint:disable=import-error
from sharedServices.model_files.station_models import (
    ServiceConfiguration,
    StationConnector,
    Stations,
)
from sharedServices.model_files.config_models import (
    ConnectorConfiguration,
    MapMarkerConfigurations,
)
from sharedServices.constants import (
    MFG_NORMAL,
    MFG_RAPID,
    OTHER_NORMAL,
    OTHER_RAPID,
    DESTINATION_SOC,
    EMERGENCY_CHARGING_GAP,
    METER_TO_MILES_DIVIDER,
    MILES_TO_METER_MULTIPLIER,
    NAVIGATE_MODE,
    STATE_STATION_CHARGE,
    YES,
    NO,
    GOOGLE_MAPS_EXCEPTION,
)
from sharedServices.common import get_distance, time_formatter_for_hours


gmaps = googlemaps.Client(key=config("DJANGO_APP_GOOGLE_API_KEY"))


# this function decodes google maps polyline
def decode_polyline(polyline_str):
    """decode polyline function"""
    index, lat, lng = 0, 0, 0
    coordinates = []
    changes = {"latitude": 0, "longitude": 0}
    # Coordinates have variable length when encoded, so just keep
    # track of whether we've hit the end of the string. In each
    # while loop iteration, a single coordinate is decoded.
    while index < len(polyline_str):
        # Gather lat/lon changes, store them in a dictionary
        # to apply them later
        for unit in ["latitude", "longitude"]:
            shift, result = 0, 0
            while True:
                byte = ord(polyline_str[index]) - 63
                index += 1
                result |= (byte & 0x1F) << shift
                shift += 5
                if not byte >= 0x20:
                    break
            if result & 1:
                changes[unit] = ~(result >> 1)
            else:
                changes[unit] = result >> 1
        lat += changes["latitude"]
        lng += changes["longitude"]
        coordinates.append(
            {"latitude": lat / 100000.0, "longitude": lng / 100000.0}
        )
    return coordinates


def data_trips(amenities, stores, connectors):
    """trip data"""
    connector_list = []
    amenities_list = []
    store_list = []
    for i in amenities:
        if i["services_list__service_id"]:
            amenity = None
            try:
                amenity = ServiceConfiguration.objects.get(
                    id=i["services_list__service_id"]
                )
            except ObjectDoesNotExist:
                pass
            if amenity:
                amenities_list.append(
                    {
                        "id": str(amenity.id),
                        "service_name": amenity.service_name,
                        "image": amenity.get_image_path_with_text(),
                    }
                )

    for i in stores:
        if i["services_list__service_id"]:
            store = None
            try:
                store = ServiceConfiguration.objects.get(
                    id=i["services_list__service_id"]
                )
            except ObjectDoesNotExist:
                pass
            if store:
                store_list.append(
                    {
                        "id": str(store.id),
                        "service_name": store.service_name,
                        "image": store.get_image_path(),
                    }
                )
    for i in connectors:
        if i["station_connectors__plug_type_name"]:
            connector = ConnectorConfiguration.objects.filter(
                connector_plug_type_name=i[
                    "station_connectors__plug_type_name"
                ]
            )
            if connector.first():
                connector_list.append(
                    {
                        "id": str(connector.first().id),
                        "connectors": i["station_connectors__plug_type_name"],
                        "image": connector.first().get_image_path(),
                        "sorting_order": connector.first().sorting_order,
                    }
                )
    connector_list = sorted(
        connector_list, key=lambda connector: connector["sorting_order"]
    )
    return [connector_list, amenities_list, store_list]


def get_devices_speed(station_ids=None):
    """this function returns devices speed"""
    if station_ids:
        connector_charge_types = StationConnector.objects.filter(
            station_id_id__in=station_ids, deleted=NO
        ).values(
            "connector_type", "station_id__station_type", "station_id__is_mfg"
        )
    else:
        connector_charge_types = StationConnector.objects.filter(
            deleted=NO
        ).values(
            "connector_type", "station_id__station_type", "station_id__is_mfg"
        )

    mfg_rapid_count = 0
    mfg_normal_count = 0
    other_rapid_count = 0
    other_normal_count = 0
    for connector in connector_charge_types:
        if connector["station_id__is_mfg"]:
            if connector["connector_type"] == "Ultra-Rapid":
                mfg_rapid_count += 1
            else:
                mfg_normal_count += 1
        else:
            if connector["station_id__station_type"]:
                if connector["connector_type"] == "Ultra-Rapid":
                    other_rapid_count += 1
                else:
                    other_normal_count += 1

    return [
        mfg_rapid_count,
        mfg_normal_count,
        other_rapid_count,
        other_normal_count
    ]


def foreign_key_extracter(station_ids):
    """foreign key extracter"""
    amenities = (
        Stations.objects.filter(
            ~Q(
                services_list__service_id__image_path=None,
                services_list__service_id__image_path_with_text=None,
            ),
            id__in=station_ids,
            services_list__deleted=NO,
            services_list__service_id__service_type="Amenity",
        )
        .values("services_list__service_id")
        .distinct()
    )
    stores = (
        Stations.objects.filter(
            ~Q(services_list__service_id__image_path=None),
            services_list__service_id__service_type__in=[
                "Retail",
                "Food to go",
            ],
            services_list__deleted=NO,
            id__in=station_ids,
        )
        .values("services_list__service_id")
        .distinct()
    )
    connectors = (
        Stations.objects.filter(
            id__in=station_ids, deleted=NO, station_connectors__deleted=NO
        )
        .values("station_connectors__plug_type_name")
        .distinct()
    )
    charging_types_array = []
    (
        mfg_rapid_count,
        mfg_normal_count,
        other_rapid_count,
        other_normal_count
    ) = get_devices_speed(station_ids)
    if mfg_rapid_count > 0:
        charging_types_array.append(
            {
                "charging_type": MFG_RAPID,
                "count": mfg_rapid_count,
                "image": MapMarkerConfigurations.objects.get(
                    map_marker_key=MFG_RAPID
                ).get_image_path(),
            }
        )
    if mfg_normal_count > 0:
        charging_types_array.append(
            {
                "charging_type": MFG_NORMAL,
                "count": mfg_normal_count,
                "image": MapMarkerConfigurations.objects.get(
                    map_marker_key=MFG_NORMAL
                ).get_image_path(),
            }
        )
    if other_rapid_count > 0:
        charging_types_array.append(
            {
                "charging_type": OTHER_RAPID,
                "count": other_rapid_count,
                "image": MapMarkerConfigurations.objects.get(
                    map_marker_key=OTHER_RAPID
                ).get_image_path(),
            }
        )
    if other_normal_count > 0:
        charging_types_array.append(
            {
                "charging_type": OTHER_NORMAL,
                "count": other_normal_count,
                "image": MapMarkerConfigurations.objects.get(
                    map_marker_key=OTHER_NORMAL
                ).get_image_path(),
            }
        )

    (connector_list, amenities_list, store_list) = data_trips(
        amenities, stores, connectors
    )

    return {
        "charging_types": charging_types_array,
        "connector_types": connector_list,
        "stores": store_list,
        "amenities": amenities_list,
    }


def filter_stations(data, filters):
    """this function filters stations"""
    table = data
    for i in filters:
        for key, value in i.items():
            if len(value) > 0:
                table = table.filter(
                    **{key: [
                        int(v)
                        if v.isnumeric()
                        else v
                        for v in value
                    ]}
                ).distinct()

    return table


def filter_stations_for_trips(*arg):
    """this function filters stations for trips"""
    (
        stations,
        amenity_filters,
        connector_type_filters,
        store_filters,
        charging_type_filters,
    ) = arg

    stations = filter_stations(
        stations,
        [
            {"services_list__service_id_id__in": amenity_filters},
            {"station_connectors__plug_type_name__in": connector_type_filters},
            {"services_list__service_id_id__in": store_filters},
        ],
    )
    station_by_charging_types = None

    if MFG_RAPID in charging_type_filters:
        station_by_charging_types = stations.filter(
            deleted=NO,
            is_mfg=YES,
            station_connectors__connector_type="Ultra-Rapid",
        ).distinct()
    if MFG_NORMAL in charging_type_filters:
        if station_by_charging_types:
            station_by_charging_types = (
                station_by_charging_types
                | stations.filter(
                    ~Q(station_connectors__connector_type="Ultra-Rapid"),
                    deleted=NO,
                    is_mfg=YES,
                ).distinct()
            )
        else:
            station_by_charging_types = stations.filter(
                ~Q(station_connectors__connector_type="Ultra-Rapid"),
                deleted=NO,
                is_mfg=YES,
            ).distinct()

    if OTHER_RAPID in charging_type_filters:
        if station_by_charging_types:
            station_by_charging_types = (
                station_by_charging_types
                | stations.filter(
                    is_mfg=NO,
                    deleted=NO,
                    station_connectors__connector_type="Ultra-Rapid",
                ).distinct()
            )

        else:
            station_by_charging_types = stations.filter(
                is_mfg=NO,
                deleted=NO,
                station_connectors__connector_type="Ultra-Rapid",
            ).distinct()

    if OTHER_NORMAL in charging_type_filters:
        if station_by_charging_types:
            station_by_charging_types = (
                station_by_charging_types
                | stations.filter(
                    ~Q(station_connectors__connector_type="Ultra-Rapid"),
                    is_mfg=NO,
                    deleted=NO,
                ).distinct()
            )

        else:
            station_by_charging_types = stations.filter(
                ~Q(station_connectors__connector_type="Ultra-Rapid"),
                is_mfg=NO,
                deleted=NO,
            ).distinct()

    if station_by_charging_types:
        stations = station_by_charging_types

    return stations


def get_route_stations(
    stations,
    added_stations,
    route_co_ordinates,  # this will be the list of co ordinates for backtrack
    station_distance,
    ev_range,
    first_road_co_ordinate,
):
    """this function returns"""
    new_index = len(route_co_ordinates) - 1

    station_can_be_added = False
    station_found_index = 0
    while new_index != 0:
        lat = route_co_ordinates[new_index]["latitude"]
        long = route_co_ordinates[new_index]["longitude"]

        def get_station_distance(station):
            distance = get_distance(
                {
                    "latitude": station.latitude,
                    "longitude": station.longitude,
                },
                {
                    "latitude": lat,
                    "longitude": long,
                },
            )
            return distance

        # Sorting of queryset according to user's current location
        station_finder_data = sorted(stations, key=get_station_distance)
        if len(station_finder_data) > 0:
            # logic to increase radius to find station
            if len(added_stations) > 0:
                if get_distance(
                    {
                        "latitude": station_finder_data[0].latitude,
                        "longitude": station_finder_data[0].longitude,
                    },
                    {
                        "latitude": added_stations[-1].latitude,
                        "longitude": added_stations[-1].longitude,
                    },
                ) < (ev_range * MILES_TO_METER_MULTIPLIER):
                    station_can_be_added = True
                else:
                    new_index -= 1
                    continue
            else:
                if get_distance(
                    {
                        "latitude": station_finder_data[0].latitude,
                        "longitude": station_finder_data[0].longitude,
                    },
                    {
                        "latitude": first_road_co_ordinate["latitude"],
                        "longitude": first_road_co_ordinate["longitude"],
                    },
                ) < (ev_range * MILES_TO_METER_MULTIPLIER):
                    station_can_be_added = True
                else:
                    new_index -= 1
                    continue
            co_ordinate_to_station_distance = get_distance(
                {
                    "latitude": station_finder_data[0].latitude,
                    "longitude": station_finder_data[0].longitude,
                },
                {
                    "latitude": route_co_ordinates[new_index]["latitude"],
                    "longitude": route_co_ordinates[new_index]["longitude"],
                },
            )
            if co_ordinate_to_station_distance < (
                station_distance * MILES_TO_METER_MULTIPLIER
            ):
                station_can_be_added = True
            else:
                station_can_be_added = False
            # end of logic to increase radius to find station
            if station_can_be_added:
                added_stations.append(station_finder_data[0])

                def get_coord_distance(co_ordinate):
                    distance = get_distance(
                        {
                            "latitude": co_ordinate["latitude"],
                            "longitude": co_ordinate["longitude"],
                        },
                        {
                            "latitude": station_finder_data[0].latitude,
                            "longitude": station_finder_data[0].longitude,
                        },
                    )
                    return distance

                station_coords = sorted(
                    route_co_ordinates.values(), key=get_coord_distance
                )
                if len(station_coords):
                    station_found_index = station_coords[0]["index"]
                if station_found_index >= new_index:
                    station_found_index = route_co_ordinates[
                        new_index
                    ]["index"]
                break
        new_index -= 1
    return [added_stations, station_can_be_added, station_found_index]


def get_location_cord(
    add_spot_data,
    add_spot_place_id,
    start_address_data,
    end_address_data,
    trip_planning_option,
):
    """Get location cord"""
    direction_response_trip = None
    try:
        if add_spot_data and add_spot_place_id:
            add_spot_address_data = gmaps.reverse_geocode(add_spot_place_id)[
                0
            ]["formatted_address"]
            direction_response_trip = gmaps.directions(
                start_address_data,
                end_address_data,
                mode=NAVIGATE_MODE,
                alternatives=True,
                waypoints=add_spot_address_data,
                avoid=list(trip_planning_option),
            )
        else:
            direction_response_trip = gmaps.directions(
                start_address_data,
                end_address_data,
                mode=NAVIGATE_MODE,
                alternatives=True,
                avoid=list(trip_planning_option),
            )
    except GOOGLE_MAPS_EXCEPTION:
        return Response(
            {
                "status_code": status.HTTP_404_NOT_FOUND,
                "status": False,
                "message": "No routes found.",
            }
        )
    return direction_response_trip


def get_station_distance_cord(
    stations,
    road_coords,
    ev_range,
    state_of_charge,
    back_track_array,
    station_distance,
    added_stations_collections,
    route_distance,
    max_ev_can_go
):
    """this function returns routes for particular user trip"""
    # Logic to find cords
    if station_distance > ev_range:
        return [
            True,
            [],
            added_stations_collections,
        ]
    if float(route_distance) < float(max_ev_can_go):
        return [
            False,
            [],
            added_stations_collections,
        ]
    first_road_cord = road_coords[0]
    back_track_array = road_coords
    for backtrack_array_index, _ in enumerate(back_track_array):
        back_track_array[backtrack_array_index][
            "index"
        ] = backtrack_array_index
    route_not_able_to_find = False
    added_stations = []
    distance_on_iteration = 0
    first_station_found = False
    iteration = 0
    temp_coordinate_array = {}
    eighty_five_percent_ev_range = ((ev_range / 100) * STATE_STATION_CHARGE)
    prev_index_station_found_at = 0
    while iteration < len(back_track_array):
        distance_on_iteration += int(
            get_distance(
                back_track_array[iteration], back_track_array[iteration + 1]
            )
        )
        temp_coordinate_array[
            len(temp_coordinate_array)
        ] = back_track_array[iteration]
        if not first_station_found:
            if distance_on_iteration > int(
                (
                    (ev_range / 100)
                    * (
                        state_of_charge - EMERGENCY_CHARGING_GAP
                        if state_of_charge > 10
                        else state_of_charge
                    )
                )
                * MILES_TO_METER_MULTIPLIER
            ):
                (
                    added_stations,
                    station_added,
                    backtracked_index,
                ) = get_route_stations(
                    stations,
                    added_stations,
                    temp_coordinate_array,
                    station_distance,
                    eighty_five_percent_ev_range,
                    first_road_cord,
                )
                if (
                    station_added is False or
                    backtracked_index <= prev_index_station_found_at
                ):
                    route_not_able_to_find = True
                    break
                iteration = backtracked_index
                prev_index_station_found_at = backtracked_index
                temp_coordinate_array = {}
                distance_on_iteration = 0
                first_station_found = True
        else:
            if distance_on_iteration > int(
                eighty_five_percent_ev_range * MILES_TO_METER_MULTIPLIER
            ):
                (
                    added_stations,
                    station_added,
                    backtracked_index,
                ) = get_route_stations(
                    stations,
                    added_stations,
                    temp_coordinate_array,
                    station_distance,
                    eighty_five_percent_ev_range,
                    first_road_cord,
                )
                if (
                    station_added is False or
                    backtracked_index <= prev_index_station_found_at
                ):
                    route_not_able_to_find = True
                    break
                iteration = backtracked_index
                prev_index_station_found_at = backtracked_index
                temp_coordinate_array = {}
                distance_on_iteration = 0

        iteration += 1
        if iteration == len(back_track_array) - 1:
            break
        # Logic end
    if route_not_able_to_find is False:
        distance_on_iteration_for_last_cord = 0
        last_coordinate_array = {}
        if len(added_stations) > 1:
            last_station = added_stations[len(added_stations) - 1]

            reversed_back_track_array = list(reversed(back_track_array))
            for road_var_inner, _ in enumerate(reversed_back_track_array):
                if road_var_inner == len(reversed_back_track_array) - 1:
                    break
                last_coordinate_array[
                    len(last_coordinate_array)
                ] = reversed_back_track_array[road_var_inner]
                distance_on_iteration_for_last_cord += int(
                    get_distance(
                        reversed_back_track_array[road_var_inner],
                        reversed_back_track_array[road_var_inner + 1],
                    )
                )
                if distance_on_iteration_for_last_cord > int(
                    ((ev_range / 100) * (DESTINATION_SOC + 5))
                    * MILES_TO_METER_MULTIPLIER
                ):
                    distance_between_last_cord_and_last_road_cord = int(
                        get_distance(
                            reversed_back_track_array[road_var_inner],
                            {
                                "latitude": last_station.latitude,
                                "longitude": last_station.longitude,
                            },
                        )
                    )

                    if distance_between_last_cord_and_last_road_cord > (
                        ((ev_range / 100) * (DESTINATION_SOC + 5))
                        * MILES_TO_METER_MULTIPLIER
                    ):
                        (
                            added_stations,
                            station_added,
                            backtracked_index,
                        ) = get_route_stations(
                            stations,
                            added_stations,
                            last_coordinate_array,
                            station_distance,
                            eighty_five_percent_ev_range,
                            first_road_cord,
                        )
                    break
    if iteration >= len(back_track_array) - 1:
        route_not_able_to_find = False
    if len(added_stations_collections) > 0:
        for added_stations_collection in added_stations_collections:
            if (len(added_stations_collection) == len(added_stations)) and (
                collections.Counter(added_stations_collection)
                == collections.Counter(added_stations)
            ):
                route_not_able_to_find = True
    else:
        if len(added_stations) == 0:
            route_not_able_to_find = True
    if not route_not_able_to_find:
        added_stations_collections.append(added_stations)
    return [
        route_not_able_to_find,
        added_stations,
        added_stations_collections,
    ]


def get_route_station_data(
    added_stations,
    add_spot,
    add_spot_address,
    start_address,
    end_address,
    trip_planning_options,
):
    """this function returns routes for particular user trip"""
    route_data = foreign_key_extracter([s_id.id for s_id in added_stations])
    waypoints = []
    waypoints = [
        gmaps.reverse_geocode((x.latitude, x.longitude))[0][
            "formatted_address"
        ]
        for x in added_stations
    ]
    if add_spot:
        waypoints.append(add_spot_address)
    direction_response_with_added_stations = gmaps.directions(
        start_address,
        end_address,
        mode=NAVIGATE_MODE,
        alternatives=True,
        waypoints=waypoints,
        avoid=list(trip_planning_options),
    )

    directions_durations = []
    direction_incrementer = 0
    for (
        direction_with_added_stations
    ) in direction_response_with_added_stations:
        temp_duration_container = []
        temp_duration_container.append(direction_incrementer)
        total_distance = 0
        total_duration = 0
        sorting_total_duration = 0

        for distance in direction_with_added_stations["legs"]:
            total_distance += distance["distance"]["value"]
            total_duration += distance["duration"]["value"]
        temp_duration_container.append(total_duration)
        sorting_total_duration = total_duration

        total_duration = time_formatter_for_hours(total_duration)
        total_distance = f"{round(total_distance/METER_TO_MILES_DIVIDER,1)} mi"
        temp_duration_container.append([total_distance, total_duration])
        directions_durations.append(temp_duration_container)
        direction_incrementer += 1

    def sort_directions(direction):
        return direction[1]

    sorted_directions = sorted(directions_durations, key=sort_directions)

    return [
        sorted_directions,
        sorting_total_duration,
        route_data,
        direction_response_with_added_stations,
    ]


def calculate_distance(direction):
    """this function returns routes for particular user trip"""
    total_distance = 0
    total_duration = 0
    sorting_total_duration = 0
    for distance in direction["legs"]:
        total_distance += distance["distance"]["value"]
        total_duration += distance["duration"]["value"]
    sorting_total_duration = total_duration
    total_duration = time_formatter_for_hours(total_duration)
    total_distance = f"{round(total_distance/METER_TO_MILES_DIVIDER,1)} mi"
    return [total_distance, total_duration, sorting_total_duration]


def get_trip_planner_routes(*arg):
    """this function returns routes for particular user trip"""
    (
        stations,
        route_stations_array,
        direction_response,
        ev_range,
        state_of_charge,
        station_distance,
        add_spot,
        add_spot_address,
        start_address,
        end_address,
        trip_planning_options,
        source_coordinates,
        destination_coordinates,
        add_stop_automatically,
    ) = arg
    direction_routes = []
    route_id = 0
    added_stations_collections = []
    route_stations_id = [st.id for st in stations]
    max_ev_can_go = (ev_range / 100) * state_of_charge
    for direction in direction_response:
        added_stations = []
        route_id += 1
        back_track_array = []
        road_coords = decode_polyline(
            direction["overview_polyline"]["points"]
        )  # Polyline decryption
        (
            total_distance,
            total_duration,
            sorting_total_duration,
        ) = calculate_distance(direction)
        route_total_distance_in_numbers = float(
            total_distance.split(" mi")[0]
        )
        if add_stop_automatically is True:
            (
                route_not_able_to_find,
                added_stations,
                added_stations_collections,
            ) = get_station_distance_cord(
                stations,
                road_coords,
                ev_range,
                state_of_charge,
                back_track_array,
                station_distance,
                added_stations_collections,
                route_total_distance_in_numbers,
                max_ev_can_go
            )
        else:
            route_not_able_to_find = False
        route_data = {
            "charging_types": [],
            "connector_types": [],
            "stores": [],
            "amenities": [],
        }
        if (
            len(route_stations_id) > 0 and
            max_ev_can_go < route_total_distance_in_numbers
        ):
            direction_response_with_added_stations = []
            if add_stop_automatically:
                (
                    sorted_directions,
                    sorting_total_duration,
                    route_data,
                    direction_response_with_added_stations,
                ) = get_route_station_data(
                    added_stations,
                    add_spot,
                    add_spot_address,
                    start_address,
                    end_address,
                    trip_planning_options,
                )
                total_duration = sorted_directions[0][2][1]
                total_distance = sorted_directions[0][2][0]
                direction_routes.append(
                    {
                        "route_id": route_id,
                        "source_coordinates": source_coordinates,
                        "route_not_able_to_find": route_not_able_to_find,
                        "destination_coordinates": destination_coordinates,
                        "route": {
                            "legs": direction_response_with_added_stations[
                                sorted_directions[0][0]
                            ]["legs"],
                            "polyline_points": decode_polyline(
                                direction_response_with_added_stations[
                                    sorted_directions[0][0]
                                ]["overview_polyline"]["points"]
                            ),
                        },
                        "total_distance": total_distance,
                        "total_duration": total_duration,
                        "total_duration_for_sorting": sorting_total_duration,
                        "have_stations": True,
                        "stations_on_route": route_stations_array,
                        "added_stations": list(
                            set([x.id for x in added_stations])
                        ),
                        "route_data": route_data,
                    }
                )
            else:

                direction_routes.append(
                    {
                        "route_id": route_id,
                        "source_coordinates": source_coordinates,
                        "route_not_able_to_find": route_not_able_to_find,
                        "destination_coordinates": destination_coordinates,
                        "route": {
                            "legs": direction["legs"],
                            "polyline_points": decode_polyline(
                                direction["overview_polyline"]["points"]
                            ),
                        },
                        "total_distance": total_distance,
                        "total_duration": total_duration,
                        "total_duration_for_sorting": sorting_total_duration,
                        "have_stations": True,
                        "stations_on_route": route_stations_array,
                        "added_stations": list(
                            set([x.id for x in added_stations])
                        ),
                        "route_data": route_data,
                    }
                )
        else:
            direction_routes.append(
                {
                    "route_id": route_id,
                    "route_not_able_to_find": route_not_able_to_find,
                    "source_coordinates": source_coordinates,
                    "destination_coordinates": destination_coordinates,
                    "route": {
                        "legs": direction["legs"],
                        "polyline_points": decode_polyline(
                            direction["overview_polyline"]["points"]
                        ),
                    },
                    "total_distance": total_distance,
                    "total_duration": total_duration,
                    "total_duration_for_sorting": sorting_total_duration,
                    "have_stations": False,
                    "stations_on_route": [],
                    "added_stations": [],
                    "route_data": route_data,
                }
            )

    return direction_routes
