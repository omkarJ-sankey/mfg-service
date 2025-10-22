import threading

from django.core.cache import cache
from .common import (
    redis_connection,
    remove_all_cache
)
from .shared_station_serializer import (
    caching_station_finder_data
)


def update_stations_cache():
    cache.expire("checkbox_for_assign_promotions", timeout=0)
    cache.expire("cache_station_for_filteration", timeout=0)
    cache.expire("promotion_cached_available_stations", timeout=0)
    cache.expire("cache_stations", timeout=0)
    redis_connection.delete("station_data_for_admin_loyalties_and_promotions")
    redis_connection.delete("station_data")
    redis_connection.delete("charge_points")
    start_caching_station_finder_data = threading.Thread(
        target=caching_station_finder_data,
        daemon=True
    )
    start_caching_station_finder_data.start()
    start_removing_all_cached_data = threading.Thread(
        target=remove_all_cache,
        daemon=True
    )
    start_removing_all_cached_data.start()