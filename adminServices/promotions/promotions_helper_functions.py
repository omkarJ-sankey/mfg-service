"""promotions helper functions"""
# Date - 01/02/2022

# File details-
#   Author          - Manish Pawar
#   Description     - This file contains helper functions for promotions.
#   Name            - Promotions helper functions
#   Modified by     - Vismay Raul
#   Modified date   - 11/07/2023

# imports required to create views
import threading
import itertools


from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.core.cache import cache
from django.conf import settings

# pylint:disable=import-error
from sharedServices.model_files.promotions_models import (
    Promotions,
    PromotionsAvailableOn,
)
from sharedServices.common import (
    remove_all_cache,
    export_data_function_multi_tabs,
    string_to_array_converter,
)

from sharedServices.model_files.station_models import Stations

from sharedServices.shared_station_serializer import (
    caching_station_finder_data,
)
from sharedServices.constants import NO

from adminServices.stations.views import station_site_locations_list

from adminServices.promotions.app_level_constants import (
    LIST_OF_ITERATION_FILDS_FOR_PROMOTIONS_EXPORT,
    LIST_OF_ITERATION_FILDS_FOR_PROMOTIONS_ASSIGN_EXPORT,
    EMPTY_OFFER_TYPE_LIST,
)

CACHE_TTL = getattr(settings, "CACHE_TTL", DEFAULT_TIMEOUT)


def remove_promotions_cached_data():
    """this function is used to remove cached data of promotions views"""
    cache.expire("cache_promotions", timeout=0)
    start_caching_promotions_data = threading.Thread(
        target=caching_station_finder_data,
        daemon=True
    )
    start_caching_promotions_data.start()
    start_removing_promotions_cached_data = threading.Thread(
        target=remove_all_cache,
        daemon=True
    )
    start_removing_promotions_cached_data.start()


def all_stations_qs():
    """all station queryset"""
    return Stations.objects.filter(deleted=NO)


# this function returns all available for values for dropdown.


def return_available_for_values():
    """Promotion available for values"""
    return ["App only", "IN SITE"]


# this function returns offer type for values for dropdown.
def return_offer_type_values():
    """promotion offer type values"""
    offer_types = Promotions.objects.all().values("offer_type").distinct()
    offer_type_list = []
    for offer_type in offer_types:
        if offer_type and len(offer_type["offer_type"]) > 0:
            offer_type_list.append(offer_type["offer_type"])
    return (
        offer_type_list if len(offer_type_list) > 0 else EMPTY_OFFER_TYPE_LIST
    )


def return_ops_regions():
    """operation regions"""
    ops_regions = station_site_locations_list()[0]
    operation_regions = []
    for ops_region in ops_regions:
        if (
            ops_region["operation_region"]
            and ops_region["operation_region"] != "nan"
        ):
            operation_regions.append(ops_region["operation_region"])
    return operation_regions


def return_status_list():
    """promotion status list"""
    return ["Active", "Inactive"]


def return_station_list(promotion_assign, parameter):
    """promotion list"""
    # station ids
    stations_queryset = promotion_assign.values(parameter).distinct()
    temp_promotion_string = ""
    for count, s_id in enumerate(stations_queryset):
        if count == len(stations_queryset) - 1:
            temp_promotion_string += s_id[parameter]
        else:
            temp_promotion_string += f"{s_id[parameter]}|"
    return temp_promotion_string


def export_promotion_data(data):
    """this function is used to export promotion data"""
    promotions_ids = [promotion["id"] for promotion in data]
    promotions_to_export = Promotions.objects.filter(
        id__in=promotions_ids
    ).values(
        "id",
        "product",
        "unique_code",
        "m_code",
        "start_date",
        "end_date",
        "retail_barcode",
        "promotion_title",
        "available_for",
        "offer_type",
        "londis_code",
        "budgen_code",
        "price",
        "quantity",
        "offer_details",
        "terms_and_conditions",
        "status",
        "shop_ids",
    )
    ids = [export_promotion["id"] for export_promotion in promotions_to_export]

    promotion_assign = (
        PromotionsAvailableOn.objects.prefetch_related(
            "promotion_id", "station_id"
        )
        .only("promotion_id_id", "deleted")
        .filter(promotion_id_id__in=ids, deleted=NO)
        .values(
            "station_id__station_id",
            "operation_region",
            "region",
            "area",
            "promotion_id_id",
        )
    )
    # station
    promotion_assign_data = [
        {promotion["promotion_id_id"]: promotion["station_id__station_id"]}
        for promotion in promotion_assign
        if promotion["promotion_id_id"]
    ]
    promotion_dict = {}
    for item in promotion_assign_data:
        key, value = next(iter(item.items()))
        promotion_dict.setdefault(key, []).append(value)
    promotion_assign_data = [
        {key: " | ".join(list(set(values)))}
        for key, values in promotion_dict.items()
    ]
    promotion_assign_data = dict(
        itertools.chain.from_iterable(
            item.items() for item in promotion_assign_data
        )
    )

    # ops region
    temp_promotion_ops_regions_string = [
        {promotion["promotion_id_id"]: promotion["operation_region"]}
        for promotion in promotion_assign
        if promotion["promotion_id_id"]
    ]
    operation_region_dict = {}
    for item in temp_promotion_ops_regions_string:
        key, value = next(iter(item.items()))
        operation_region_dict.setdefault(key, []).append(value)

    temp_promotion_ops_regions_string = [
        {key: " | ".join(list(set(values)))}
        for key, values in operation_region_dict.items()
    ]
    temp_promotion_ops_regions_string = dict(
        itertools.chain.from_iterable(
            item.items() for item in temp_promotion_ops_regions_string
        )
    )

    # regions
    temp_promotion_regions_string = [
        {promotion["promotion_id_id"]: promotion["region"]}
        for promotion in promotion_assign
        if promotion["promotion_id_id"]
    ]
    region_dict = {}
    for item in temp_promotion_regions_string:
        key, value = next(iter(item.items()))
        region_dict.setdefault(key, []).append(value)

    temp_promotion_regions_string = [
        {key: " | ".join(list(set(values)))}
        for key, values in region_dict.items()
    ]
    temp_promotion_regions_string = dict(
        itertools.chain.from_iterable(
            item.items() for item in temp_promotion_regions_string
        )
    )

    # areas
    temp_promotion_station_areas_string = [
        {promotion["promotion_id_id"]: promotion["area"]}
        for promotion in promotion_assign
        if promotion["promotion_id_id"]
    ]
    area_dict = {}
    for item in temp_promotion_station_areas_string:
        key, value = next(iter(item.items()))
        area_dict.setdefault(key, []).append(value)

    temp_promotion_station_areas_string = [
        {key: " | ".join(list(set(values)))}
        for key, values in area_dict.items()
    ]
    temp_promotion_station_areas_string = dict(
        itertools.chain.from_iterable(
            item.items() for item in temp_promotion_station_areas_string
        )
    )

    for export_promotion in promotions_to_export:
        temp_promotion_shop_ids_string = ""
        if export_promotion["shop_ids"]:
            for count, shop_id in enumerate(
                string_to_array_converter(export_promotion["shop_ids"])
            ):
                if (
                    count
                    == len(
                        string_to_array_converter(export_promotion["shop_ids"])
                    )
                    - 1
                ):
                    temp_promotion_shop_ids_string += shop_id
                else:
                    temp_promotion_shop_ids_string += f"{shop_id}|"

        export_promotion["station_ids"] = (
            promotion_assign_data[export_promotion["id"]]
            if export_promotion["id"] in promotion_assign_data
            else ""
        )
        export_promotion["shop_ids"] = temp_promotion_shop_ids_string
        export_promotion["ops_regions"] = (
            temp_promotion_ops_regions_string[export_promotion["id"]]
            if export_promotion["id"] in temp_promotion_ops_regions_string
            else ""
        )
        export_promotion["regions"] = (
            temp_promotion_regions_string[export_promotion["id"]]
            if export_promotion["id"] in temp_promotion_regions_string
            else ""
        )
        export_promotion["areas"] = (
            temp_promotion_station_areas_string[export_promotion["id"]]
            if export_promotion["id"] in temp_promotion_station_areas_string
            else ""
        )
        export_promotion["start_date"] = export_promotion["start_date"].date()
        export_promotion["end_date"] = export_promotion["end_date"].date()
        export_promotion["image_1"] = ""
        export_promotion["image_2"] = ""
    response = export_data_function_multi_tabs(
        [promotions_to_export, promotions_to_export],
        [
            LIST_OF_ITERATION_FILDS_FOR_PROMOTIONS_EXPORT,
            LIST_OF_ITERATION_FILDS_FOR_PROMOTIONS_ASSIGN_EXPORT,
        ],
        [
            [
                "id",
                "product",
                "unique_code",
                "m_code",
                "start_date",
                "end_date",
                "retail_barcode",
                "promotion_title",
                "available_for",
                "offer_type",
                "londis_code",
                "budgen_code",
                "price",
                "quantity",
                "offer_details",
                "terms_and_conditions",
                "status",
                "image_1",
                "image_2",
            ],
            [
                "id",
                "station_ids",
                "unique_code",
                "shop_ids",
                "ops_regions",
                "regions",
                "areas",
            ],
        ],
        ["Promotions", "Promotion assign"],
    )
    return response
