"""loyalty helper functions"""
# Date - 03/01/2021

# File details-
#   Author          - Manish Pawar
#   Description     - This file contains helper functions for loyalty.
#   Name            - Loyalty Helper functions
#   Modified by     - Vismay Raul
#   Modified date   - 11/07/2023

import json
import threading
import itertools
from decouple import config

from io import StringIO

from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.conf import settings
from django.db.models import Q

# pylint:disable=import-error
from sharedServices.model_files.station_models import Stations, StationServices
from sharedServices.model_files.loyalty_models import (
    Loyalty,
    LoyaltyAvailableOn,
    LoyaltyProducts,
    LoyaltyOccurrences
)
from sharedServices.model_files.config_models import ServiceConfiguration
from sharedServices.model_files.notifications_module_models import PushNotifications
from sharedServices.common import (
    export_data_function_multi_tabs,
    remove_all_cache,
    redis_connection,
)

from sharedServices.constants import NO, LOYALTY_TYPES

from sharedServices.shared_station_serializer import (
    caching_station_finder_data,
)

# pylint:enable=import-error
CACHE_TTL = getattr(settings, "CACHE_TTL", DEFAULT_TIMEOUT)


def return_loyalty_data(loyalty_data, loyalty_pk, is_update=True):
    """this function returns loyalty data"""
    available_on_data = LoyaltyAvailableOn.objects.filter(
        loyalty_id_id=loyalty_data["id"], deleted=NO
    )
    ops_regions = list(
        set(available_on_data.values_list("operation_region", flat=True))
    )
    regions = list(set(available_on_data.values_list("region", flat=True)))
    area = list(set(available_on_data.values_list("area", flat=True)))
    stations = list(
        set(available_on_data.values_list("station_id_id", flat=True))
    )
    station_ids = list(
        set(available_on_data.values_list("station_id__station_id", flat=True))
    )
    shops = []
    start_date = loyalty_data["valid_from_date"]
    end_date = loyalty_data["valid_to_date"]
    if is_update:
        loyalty_data["valid_from_date"] = ""
        loyalty_data["valid_to_date"] = ""
    loyalty_data["start_date"] = start_date.strftime("%d/%m/%Y")
    loyalty_data["end_date"] = end_date.strftime("%d/%m/%Y")

    # Converting string into an array.
    if loyalty_data["shop_ids"]:
        input_output = StringIO(loyalty_data["shop_ids"])
        shop_ids = json.load(input_output)
        shops = [
            shop["service_name"]
            for shop in return_services_from_configurations()
            if (
                str(shop["service_name"]) in shop_ids
                or str(shop["id"]) in shop_ids
            )
        ]
    loyalty_products = list(
        LoyaltyProducts.objects.filter(
            loyalty_id_id=loyalty_data["id"], deleted=NO
        ).values(
            "id",
            "product_plu",
            "product_bar_code",
            "desc",
            "price",
            "redeem_product_promotion_price",
            "status",
        )
    )
    occurrences = list(
        {
            "id": occurrence["id"],
            "date": occurrence["date"].strftime("%d/%m/%Y"),
            "start_time": (
                f"{str(occurrence['start_time'].hour).zfill(2)}:{str(occurrence['start_time'].minute).zfill(2)}"
            ),
            "end_time": (
                f"{str(occurrence['end_time'].hour).zfill(2)}:{str(occurrence['end_time'].minute).zfill(2)}"
            ),
        }
        for occurrence in LoyaltyOccurrences.objects.filter(
            loyalty_id_id=loyalty_data["id"], deleted=NO
        ).values(
            "id",
            "date",
            "start_time",
            "end_time",
        )
    )
    loyalty_data["stations"] = stations
    loyalty_data["station_ids"] = station_ids
    loyalty_data["operation_regions"] = ops_regions
    loyalty_data["regions"] = regions
    loyalty_data["area"] = area
    loyalty_data["shop"] = shops
    loyalty_data["loyalty_products"] = loyalty_products
    loyalty_data["occurrences"] = occurrences
    loyalty_db_data = Loyalty.objects.filter(id__exact=loyalty_pk).first()
    loyalty_data["trigger_sites"] = loyalty_db_data.trigger_sites
    loyalty_data["transaction_count_for_costa_kwh_consumption"] = loyalty_db_data.transaction_count_for_costa_kwh_consumption
    loyalty_data["detail_site_check"] = loyalty_db_data.detail_site_check
    loyalty_data["display_on_charging_screen"] = loyalty_db_data.display_on_charging_screen
    
    if loyalty_data["image"]:
        loyalty_data["image"] = loyalty_db_data.get_loyalty_image()
    else:   
        loyalty_data["image"] = None

    if loyalty_data["reward_image"]:
        loyalty_data["reward_image"] = loyalty_db_data.get_loyalty_reward_image()
    else:
        loyalty_data["reward_image"]=None

    
    if (
        loyalty_data["loyalty_type"] in LOYALTY_TYPES and
        loyalty_data["reward_unlocked_notification_id_id"] and 
        loyalty_data["reward_expiration_notification_id_id"]
    ):
        reward_unlocked_notification_data = PushNotifications.objects.get(
            id=loyalty_data["reward_unlocked_notification_id_id"]
        )
        reward_expiration_notification_data = PushNotifications.objects.get(
            id=loyalty_data["reward_expiration_notification_id_id"]
        )
        loyalty_data[
            "reward_activated_notification_title"
        ] = reward_unlocked_notification_data.subject
        loyalty_data[
            "reward_activated_notification_description"
        ] = reward_unlocked_notification_data.description
        loyalty_data[
            "reward_activated_notification_screen"
        ] = reward_unlocked_notification_data.screens
        # loyalty_data[
        #     "loyalty_visibility"
        # ] = reward_unlocked_notification_data.visibility
        # loyalty_data[
        #     "is_car_wash"
        # ] = reward_unlocked_notification_data.is_car_wash
        if is_update:
            loyalty_data[
                "reward_activated_notification_type_of_notification"
            ] = "In App Notification-on" if (
                reward_unlocked_notification_data.inapp_notification == 'true'
            ) else (
                "Push Notification-on" if (
                    reward_unlocked_notification_data.push_notification == 'true'
                ) else "Push Notification-off"
            )
        else: 
            loyalty_data[
                "reward_activated_notification_type_of_notification"
            ] = "In-App Notification" if (
                reward_unlocked_notification_data.inapp_notification == 'true'
            ) else "Push Notification"
        if reward_unlocked_notification_data.get_push_notification_image() != config("DJANGO_APP_CDN_BASE_URL"):
            loyalty_data["reward_activated_notification_image"] = (
                reward_unlocked_notification_data.get_push_notification_image()
            )
        else:
            loyalty_data["reward_activated_notification_image"]= config("DJANGO_APP_CDN_BASE_URL").split("media/")[0] + "static/images/notification-logo.png"
        loyalty_data[
            "reward_expiration_notification_title"
        ] = reward_expiration_notification_data.subject
        loyalty_data[
            "reward_expiration_notification_description"
        ] = reward_expiration_notification_data.description
        loyalty_data[
            "reward_expiration_notification_screen"
        ] = reward_expiration_notification_data.screens
        if is_update:
            loyalty_data[
                "reward_expiration_notification_type_of_notification"
            ] = "In App Notification-on" if (
                reward_expiration_notification_data.inapp_notification == 'true'
            ) else (
                "Push Notification-on" if (
                    reward_expiration_notification_data.push_notification == 'true'
                ) else "Push Notification-off"
            )
        else: 
            loyalty_data[
                "reward_expiration_notification_type_of_notification"
            ] = "In-App Notification" if (
                reward_expiration_notification_data.inapp_notification == 'true'
            ) else "Push Notification"
        if reward_expiration_notification_data.get_push_notification_image() != config("DJANGO_APP_CDN_BASE_URL"):
            loyalty_data["reward_expiration_notification_image"] = (
                reward_expiration_notification_data.get_push_notification_image()
            )
        else:
            loyalty_data["reward_expiration_notification_image"]= config("DJANGO_APP_CDN_BASE_URL").split("media/")[0] + "static/images/notification-logo.png"
    return loyalty_data


def return_services_from_configurations():
    """this function returns shops from configurations"""
    return ServiceConfiguration.objects.filter().values(
        "id", "service_name", "image_path", "service_type"
    )


def return_shops_from_configurations():
    """this function returns shops from configurations"""
    return ServiceConfiguration.objects.filter(
        ~Q(service_type="Amenity")
    ).values("id", "service_name", "image_path", "service_type")


def return_amenities_from_configurations():
    """this function returns amenities from configurations"""
    return ServiceConfiguration.objects.filter(service_type="Amenity").values(
        "id", "service_name", "image_path", "service_type"
    )


def return_loyalty_list():
    """this function returns list of loyalties"""
    if "cache_loyalties" in cache:
        # get results from cache
        loyalties = cache.get("cache_loyalties")
    else:
        loyalties = (
            Loyalty.objects.filter(deleted=NO)
            .order_by("-updated_date")
            .values()
        )
        cache.set("cache_loyalties", loyalties, timeout=CACHE_TTL)
    return loyalties


def remove_loyalties_cached_data():
    """this function is used to remove cached data of loyalties views"""
    cache.expire("cache_loyalties", timeout=0)
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


def return_loyalty_category_list():
    """This function return categories of loyalties"""
    return ["Valet", "Costa", "EV", "Other"]


def return_offer_type_list():
    """This function returns list of offer types"""
    return [
        "Generic Offers",
        "Loyalty Offers",
    ]


def return_bar_code_std_list():
    """this function returns the list of loyalty bar code stds"""
    return ["EAN8", "EAN13"]


def export_loyalty_data(filtered_data):
    """this function exports loyalty data"""

    loyalty_ids = [
        loyalty["id"] for loyalty in filtered_data["filtered_table_for_export"]
    ]
    loyaltys_to_export = Loyalty.objects.filter(id__in=loyalty_ids).values(
        "id",
        "loyalty_title",
        "loyalty_type",
        "valid_from_date",
        "valid_to_date",
        "number_of_paid_purchases",
        "qr_refresh_time",
        "bar_code_std",
        "status",
        "category",
        "offer_details",
        "terms_and_conditions",
        "redeem_product_code",
        "redeem_product",
        "cycle_duration",
        "redeem_type",
        "number_of_total_issuances",
        "visibility",
        "is_car_wash",
        "display_on_charging_screen",
    )
    loyalty_products = (
        LoyaltyProducts.objects.prefetch_related("loyalty_id")
        .only("product_plu", "desc", "loyalty_id_id")
        .filter(
            loyalty_id_id__in=loyalty_ids,
            product_plu__isnull=False,
            desc__isnull=False,
        )
        .values("id", "product_plu", "desc", "loyalty_id_id")
    )
    loyalty_products = [
        {
            loyalty[
                "loyalty_id_id"
            ]: f"{loyalty['product_plu']},{loyalty['desc']}"
        }
        for loyalty in loyalty_products
        if loyalty["id"]
    ]
    loyalty_dict = {}
    for item in loyalty_products:
        key, value = next(iter(item.items()))
        loyalty_dict.setdefault(key, []).append(value)

    loyalty_products = [
        {key: " | ".join(list(set(values)))}
        for key, values in loyalty_dict.items()
    ]
    loyalty_products = dict(
        itertools.chain.from_iterable(
            item.items() for item in loyalty_products
        )
    )
    for loyalty in loyaltys_to_export:
        loyalty["loyalty_products"] = (
            loyalty_products[loyalty["id"]]
            if loyalty["id"] in loyalty_products
            else ""
        )
        loyalty["valid_from_date"] = loyalty["valid_from_date"].date()
        loyalty["valid_to_date"] = (
            loyalty["valid_to_date"].date()
            if loyalty["valid_to_date"] else ""
        )
        loyalty["loyalty_reward"] = ""
        if loyalty["redeem_product_code"] and loyalty["redeem_product"]:
            loyalty["loyalty_reward"] = (
                loyalty["redeem_product_code"]
                + ","
                + loyalty["redeem_product"]
            )
    response = export_data_function_multi_tabs(
        [loyaltys_to_export],
        [
            [
                "ID",
                "Loyalty Title",
                "Loyalty Type",
                "Loyalty Reward",
                "Category",
                "Bar Code Std",
                "From Date",
                "To Date",
                "Number of Paid Purchases / Voucher Issuance Trigger Value",
                "QR Code Expiry (In Mins.)",
                "Status(Active/Inactive)",
                "Offer Details",
                "Terms and Conditions",
                "Loyalty Products",
                "Redeem Type",
                "Total Number of Issuances",
                "User Cycle Duration (In days)",
                "Visibility",
                "Is Car Wash",
                "Display on Charging Screen"
            ]
        ],
        [
            [
                "id",
                "loyalty_title",
                "loyalty_type",
                "loyalty_reward",
                "category",
                "bar_code_std",
                "valid_from_date",
                "valid_to_date",
                "number_of_paid_purchases",
                "qr_refresh_time",
                "status",
                "offer_details",
                "terms_and_conditions",
                "loyalty_products",
                "redeem_type",
                "number_of_total_issuances",
                "cycle_duration",
                "visibility",
                "is_car_wash",
                "display_on_charging_screen",
            ]
        ],
        ["Loyalties"],
    )
    return response


def return_stations_master_data_for_loyalties_and_promotions():
    """this function return the stations master data for admin loyalties and promotions"""

    # station_data_for_admin_loyalties_and_promotions = redis_connection.get(
    #     "station_data_for_admin_loyalties_and_promotions"
    # )
    # if (
    #     station_data_for_admin_loyalties_and_promotions is not None
    #     or station_data_for_admin_loyalties_and_promotions != ""
    # ):
    #     return station_data_for_admin_loyalties_and_promotions.decode("utf-8")
    stations = {}
    db_stations = Stations.objects.filter(deleted=NO).only(
        "id",
        "station_id",
        "operation_region",
        "region",
        "area",
    )
    db_station_services = StationServices.objects.filter(
        # ~Q(service_id__service_type='Amenity'),
        deleted=NO,
    ).values(
        "station_id_id",
        "service_id__service_name",
        "service_id__service_type",
    )
    for station in db_stations:
      if station.operation_region and station.region and station.area:
          stations[station.id] = {
              "id": station.id,
              "station_id": station.station_id,
              "operation_region": station.operation_region,
              "region": station.region,
              "area": station.area,
          }
    for service in db_station_services:
        if service["station_id_id"] in stations:
            if service["service_id__service_type"] == "Amenity":
                if "amenities" in stations[service["station_id_id"]]:
                    stations[service["station_id_id"]]["amenities"].append(
                        service["service_id__service_name"]
                    )
                else:
                    stations[service["station_id_id"]]["amenities"] = [
                        service["service_id__service_name"]
                    ]

            if service["service_id__service_type"] != "Amenity":
                if "shops" in stations[service["station_id_id"]]:
                    stations[service["station_id_id"]]["shops"].append(
                        service["service_id__service_name"]
                    )
                else:
                    stations[service["station_id_id"]]["shops"] = [
                        service["service_id__service_name"]
                    ]
    redis_connection.set(
        "station_data_for_admin_loyalties_and_promotions",
        json.dumps(list(stations.values())),
    )
    return json.dumps(list(stations.values()))
