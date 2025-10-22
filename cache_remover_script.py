"""This file helps to delete entire data from database
and reimport the neccessary data."""


import os
import django
import redis
# pylint:disable=import-error
from sharedServices.common import (
    redis_connection,
    array_to_string_converter,
    caching_trip_planner_data,
)

# pylint:disable=import-error
from sharedServices.shared_station_serializer import (
    caching_station_finder_data
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backendServices.settings")


django.setup()


def removed_cached_data():
    """remove cache function"""
    try:
        redis_connection.set(
            "station_finder_cache_data_updated_v3", array_to_string_converter(None)
        )
        redis_connection.set(
            "station_finder_filter_list", array_to_string_converter(None)
        )
        redis_connection.set(
            "api_promotions_stations", array_to_string_converter(None)
        )
        redis_connection.set(
            "api_promotions_shops", array_to_string_converter(None)
        )
        redis_connection.set(
            "trip_planner_filter", array_to_string_converter(None)
        )
        redis_connection.set(
            "icons_from_cache", array_to_string_converter(None)
        )
        redis_connection.set(
            "electric_vehicle_cache_data", array_to_string_converter(None)
        )
        caching_station_finder_data()
        caching_trip_planner_data()
    except (
        redis.exceptions.ConnectionError,
        redis.exceptions.TimeoutError,
    ) as error:
        print("Failed to remove cache due to->", error)

if __name__ == "__main__":
    removed_cached_data()
