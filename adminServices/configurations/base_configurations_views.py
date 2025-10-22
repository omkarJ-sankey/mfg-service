"""Base Configurations (Map indicators, Base
    configurations and Default images) views"""
# Date - 22/03/2022
# File details-
#   Author      - Manish Pawar
#   Description - This file is mainly focused on APIs and views related
#                   to base configrutions data.
#   Name        - Base Configurations APIs
#   Modified by - Shubham Dhumal

# These are all the imports that we are exporting from different
# module's from project or library.

import base64
import json
import threading
from django.http.response import JsonResponse
from django.shortcuts import render
from django.contrib import messages
from django.db.models import Q
from django.core.files.base import ContentFile
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.core.cache import cache
from django.conf import settings

# pylint:disable=import-error
from sharedServices.decorators import authenticated_user
from sharedServices.common import (
    array_to_string_converter,
    redis_connection,
    filter_url,
    image_converter,
    randon_string_generator,
    check_integer,
)
from sharedServices.common_audit_trail_functions import (
    audit_data_formatter,
    add_audit_data,
)
from sharedServices.image_optimization_funcs import optimize_image
from sharedServices.constants import (
    AZURE_BLOB_STORAGE_URL,
    CONFIGURATION_CONST,
    GET_METHOD_ALLOWED,
    POST_METHOD_ALLOWED,
    SUCCESS_UPDATE,
    MFG_RAPID,
    MFG_NORMAL,
    OTHER_RAPID,
    OTHER_NORMAL,
    LOADING,
    AVAILABLE,
    OCCUPIED,
    UNKNOWN,
    EV_POWER_EXTENSION_FOR_DEFAULT_IMAGES,
    MFG_BRANDS,
    IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN,
    STATION_INFO_IMAGE,
    MAP_MARKERS_CONST,
    BASE_CONFIG_CONST,
    AUDIT_ADD_CONSTANT,
    AUDIT_UPDATE_CONSTANT,
    COMMON_ERRORS,
    ERROR_TEMPLATE_URL,
    JSON_ERROR_OBJECT,
    YES,
    NO,
    APP_VERSION_FOUR,
    MAP_MARKER_SMALL_IMAGE_SIZE
)

from sharedServices.model_files.config_models import (
    MapMarkerConfigurations,
    BaseConfigurations,
)
from .views import remove_configurations_cached_data
from .app_level_constants import (
    ADD_MARKER_TEMPLATE,
    BASE_CONF_UPDATED_SUCCESSFULLY,
    BASE_CONFIRATIONS_TEMPLATE,
    BRAND_INDICATOR_TYPE,
    DEFAULT_IMAGES_TEMPLATE,
    EV_INDICATOR_TYPE,
    INDICATOR_ADDED_SUCCESSFULLY,
    INDICATOR_ADD_ERROR,
    BASE_CONF_ADDED_SUCCESSFULLY,
    BASE_CONF_ADD_ERROR,
    DEFAULT_IMAGE_ADDED_SUCCESSFULLY,
    DEFAULT_IMAGE_UPDATED_SUCCESSFULLY,
    DEFAULT_IMAGE_ADD_ERROR,
    UNDER_MAINTENANCE_STATUS_KEY,
    UNDER_MAINTENANCE_MESSAGE_KEY,
    UNDER_MAINTENANCE_KEYS
)

CACHE_TTL = getattr(settings, "CACHE_TTL", DEFAULT_TIMEOUT)


def return_already_added_ev_indictors(return_brands_list=False):
    """this function returns added ev indicators"""
    if "cache_ev_indicators_list" in cache:
        # get results from cache
        ev_indicators_list = cache.get("cache_ev_indicators_list")
    else:
        charging_speed_list = [
            MFG_RAPID,
            MFG_NORMAL,
            OTHER_RAPID,
            OTHER_NORMAL,
        ]
        charging_status_list = [
            LOADING,
            AVAILABLE,
            OCCUPIED,
            UNKNOWN,
        ]
        charging_speed_status_list = [
            f"{charging_speed}-{charging_status}"
            for charging_speed in charging_speed_list
            for charging_status in charging_status_list
        ]
        ev_indicators_list = charging_speed_list + charging_speed_status_list
        cache.set(
            "cache_ev_indicators_list", ev_indicators_list, timeout=CACHE_TTL
        )
    if return_brands_list:
        return [
            map_marker.map_marker_key
            for map_marker in MapMarkerConfigurations.objects.filter(
                ~Q(map_marker_key__in=ev_indicators_list)
            )
        ]
    return [
        ev_indicators_list,
        [
            map_marker.map_marker_key
            for map_marker in MapMarkerConfigurations.objects.filter(
                map_marker_key__in=ev_indicators_list
            )
        ],
    ]


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def map_markers_view(request):
    """add marker view"""
    try:
        map_markers = MapMarkerConfigurations.objects.filter()
        (
            ev_indicators_list,
            already_added_ev_indicators,
        ) = return_already_added_ev_indictors()
        map_markers = [
            {
                "id": map_marker.id,
                "map_marker_key": map_marker.map_marker_key,
                "get_image_path": map_marker.get_image_path(),
                "indicator_type": EV_INDICATOR_TYPE
                if map_marker.map_marker_key in ev_indicators_list
                else BRAND_INDICATOR_TYPE,
            }
            for map_marker in map_markers
        ]
        if request.method == "POST":
            data = json.loads(request.body)
            if len(data["url"]) > 0 and len(data["indicator_type"]) > 2:
                image_data = image_converter(data["url"])
                image = ContentFile(
                    base64.b64decode(image_data[0]),
                    name=f"{data['indicator_type']}_\
                                    {randon_string_generator()}"
                    + "."
                    + image_data[1],
                )
                can_be_added = True
                if (
                    data["type"] == EV_INDICATOR_TYPE
                    and data["indicator_type"].strip()
                    in already_added_ev_indicators
                ):
                    can_be_added = False
                    messages.warning(
                        request,
                        "Indicator with provided name already added.",
                    )
                if (
                    data["type"] == BRAND_INDICATOR_TYPE
                    and MapMarkerConfigurations.objects.filter(
                        map_marker_key=data["indicator_type"].strip()
                    ).first()
                ):
                    can_be_added = False
                    messages.warning(
                        request,
                        "Brand with provided name already exists.",
                    )
                if (
                    data["type"] == BRAND_INDICATOR_TYPE
                    and data["indicator_type"].strip()
                    in already_added_ev_indicators
                ):
                    can_be_added = False
                    messages.warning(
                        request,
                        "EV indicators can't be "+
                        "added from brand indicator form.",
                    )
                if can_be_added:
                    small_image =  (
                        optimize_image(
                            image_data[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
                            f"{data['indicator_type']}_small_image_{randon_string_generator()}"
                            + "."
                            + image_data[1],
                            MAP_MARKER_SMALL_IMAGE_SIZE,
                            only_resize=True,
                            image_format="PNG"
                        )
                    )
                    map_marker = MapMarkerConfigurations.objects.create(
                        map_marker_key=data["indicator_type"].strip(),
                        map_marker_image=image,
                        small_map_marker_image=small_image,
                        created_date=timezone.localtime(timezone.now()),
                        updated_date=timezone.localtime(timezone.now()),
                        updated_by=request.user.full_name,
                    )
                    new_data = audit_data_formatter(
                        MAP_MARKERS_CONST, map_marker.id
                    )
                    add_audit_data(
                        request.user,
                        f'{data["indicator_type"].strip()}',
                        f"{MAP_MARKERS_CONST}-{map_marker.id}",
                        AUDIT_ADD_CONSTANT,
                        MAP_MARKERS_CONST,
                        new_data,
                        None,
                    )
                    remove_configurations_cached_data()
                return JsonResponse(
                    {"status": 1, "message": INDICATOR_ADDED_SUCCESSFULLY}
                )
            messages.warning(request, INDICATOR_ADD_ERROR)
        return render(
            request,
            ADD_MARKER_TEMPLATE,
            {
                "ev_indicators_list": ev_indicators_list,
                "already_added_ev_indicators": already_added_ev_indicators,
                "map_markers": map_markers,
                "json_data": json.dumps(map_markers),
                "pagination_count": BaseConfigurations.objects.filter(
                    base_configuration_key="Pagination_page_rows"
                )
                .first()
                .base_configuration_value
                if BaseConfigurations.objects.filter(
                    base_configuration_key="Pagination_page_rows"
                ).first()
                else 10,
                "data_count": len(map_markers),
                "data": filter_url(
                    request.user.role_id.access_content.all(),
                    CONFIGURATION_CONST,
                ),
            },
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def update_marker_view(request):
    """update marker view"""
    try:
        data = json.loads(request.body)
        _, already_added_ev_indicators = (
            return_already_added_ev_indictors()
        )
        if len(data["url"]) > 0 and len(data["indicator_type"]) > 0:
            split = data["url"].split(AZURE_BLOB_STORAGE_URL)
            map_marker = MapMarkerConfigurations.objects.filter(
                id=int(data["id"])
            )
            old_data = audit_data_formatter(MAP_MARKERS_CONST, int(data["id"]))
            if (
                map_marker.first()
                and map_marker.first().map_marker_key
                in already_added_ev_indicators
            ):
                already_added_ev_indicators.remove(
                    map_marker.first().map_marker_key
                )
            can_be_added = True
            if (
                data["type"] == EV_INDICATOR_TYPE
                and data["indicator_type"].strip()
                in already_added_ev_indicators
            ):
                can_be_added = False
                messages.warning(
                    request,
                    "Indicator with provided name already added.",
                )
            if (
                data["type"] == BRAND_INDICATOR_TYPE
                and MapMarkerConfigurations.objects.filter(
                    ~Q(id=data["id"]),
                    map_marker_key=data["indicator_type"].strip(),
                ).first()
            ):
                can_be_added = False
                messages.warning(
                    request,
                    "Brand with provided name already exists.",
                )
            if (
                data["type"] == BRAND_INDICATOR_TYPE
                and data["indicator_type"].strip()
                in already_added_ev_indicators
            ):
                can_be_added = False
                messages.warning(
                    request,
                    "EV indicators can't be edited from brand indicator form.",
                )
            if can_be_added:
                update_data = get_object_or_404(
                    MapMarkerConfigurations, id=data["id"]
                )
                if len(split) != 2:
                    image_data = image_converter(data["url"])
                    image = ContentFile(
                        base64.b64decode(image_data[0]),
                        name=(
                            f"{data['indicator_type']}"
                            + "_"
                            + str(randon_string_generator())
                            + "."
                            + image_data[1]
                        ),
                    )
                    small_image = (
                        optimize_image(
                            image_data[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
                            f"{data['indicator_type']}_small_image_{randon_string_generator()}"
                            + "."
                            + image_data[1],
                            MAP_MARKER_SMALL_IMAGE_SIZE,
                            only_resize=True,
                            image_format="PNG"
                        )
                    )
                    update_data.map_marker_image = image
                    update_data.small_map_marker_image = small_image
                update_data.map_marker_key = data["indicator_type"].strip()
                update_data.updated_date = timezone.localtime(timezone.now())
                update_data.updated_by = request.user.full_name
                update_data.save()

                new_data = audit_data_formatter(
                    MAP_MARKERS_CONST, int(data["id"])
                )
                if old_data != new_data:
                    add_audit_data(
                        request.user,
                        f'{data["indicator_type"].strip()}',
                        f'{MAP_MARKERS_CONST}-{int(data["id"])}',
                        AUDIT_UPDATE_CONSTANT,
                        MAP_MARKERS_CONST,
                        new_data,
                        old_data,
                    )
                remove_configurations_cached_data()
            return JsonResponse({"status": 1, "message": SUCCESS_UPDATE})
        messages.warning(
            request, "Indicator type and image are required fields."
        )
        return JsonResponse(
            {
                "status": 0,
                "message": "Indicator type and image are required fields",
            }
        )
    except COMMON_ERRORS:
        return JSON_ERROR_OBJECT


def return_brand_list():
    """this function returns brand list"""
    stations_brands = return_already_added_ev_indictors(True)
    return [station_brand for station_brand in stations_brands] + [
        f"{station_brand} {EV_POWER_EXTENSION_FOR_DEFAULT_IMAGES}"
        for station_brand in stations_brands
        if station_brand not in MFG_BRANDS
    ]


def return_default_images_list():
    """this function returns base configurations list"""
    return [
        ("_".join(brand.split(" ")) + "_default_image")
        for brand in return_brand_list()
    ]


def return_base_configurations():
    """this function returns base configurations list"""
    return [
        {
            "id": base_config.id,
            "base_configuration_name": base_config.base_configuration_name,
            "base_configuration_key": base_config.base_configuration_key,
            "base_configuration_value": base_config.base_configuration_value,
            "description": base_config.description,
            "add_to_cache": bool(base_config.add_to_cache == YES),
            "frequently_used": bool(base_config.frequently_used == YES),
        }
        for base_config in BaseConfigurations.objects.filter(
            ~Q(base_configuration_key__in=return_default_images_list())
        )
    ]


def return_default_images():
    """this function returns default images list"""
    return [
        {
            "id": base_config.id,
            "base_configuration_name": base_config.base_configuration_name,
            "app_version": base_config.for_app_version,
            "get_image": base_config.get_image(),
        }
        for base_config in BaseConfigurations.objects.filter(
            base_configuration_key__in=return_default_images_list()
        )
    ]


def cache_maintenance_config_keys():
    """this function caches maintenace status and message keys"""
    under_maintenance_status = BaseConfigurations.objects.filter(
        base_configuration_key=UNDER_MAINTENANCE_STATUS_KEY
    ).first()
    under_maintenance_message = BaseConfigurations.objects.filter(
        base_configuration_key=UNDER_MAINTENANCE_MESSAGE_KEY
    ).first()
    redis_connection.set(
        "maintenance_configurations",
        array_to_string_converter(
            [
                {
                    "status": (
                        True
                        if (
                            under_maintenance_status
                            and under_maintenance_status.\
                                base_configuration_value
                            == "Yes"
                        )
                        else False
                    ),
                    "message": (
                        under_maintenance_message.base_configuration_value
                        if (
                            under_maintenance_message
                            and len(
                                under_maintenance_message.\
                                    base_configuration_value
                            )
                        )
                        else ""
                    ),
                }
            ]
        ),
    )


def add_to_cache_base_configurations(key, value, add_operation=True):
    """this function is used to add base config to cache"""
    if add_operation:
        redis_connection.set(key, value)
    elif redis_connection.get(key):
        redis_connection.delete(key)


def add_frequently_used_base_configurations():
    """this function is used to add frequently used base config to cache"""
    redis_connection.set(
        "frequently_used_configurations",
        array_to_string_converter([{
            f'{frequently_used_conf.base_configuration_key}': (
                f'{frequently_used_conf.base_configuration_value}'
                if frequently_used_conf.base_configuration_value not in [YES, NO]
                else bool(frequently_used_conf.base_configuration_value == YES)
            )
            for frequently_used_conf in BaseConfigurations.objects.filter(
                frequently_used=YES
            ) if (
                frequently_used_conf.base_configuration_value and
                frequently_used_conf.base_configuration_key
            )
        }])
    )


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def base_configurations_view(request):
    """list and add base configuration view"""
    try:
        base_configurations = return_base_configurations()
        if request.method == "POST":
            data = json.loads(request.body)
            if (
                len(data["db_var_name"]) > 0
                and len(data["var_name"]) > 0
                and (
                    float(data["var_value"]) > 0
                    if check_integer(data["var_value"])
                    else len(data["var_value"]) > 0
                )
                and len(data["desc"]) > 0
            ):
                can_be_added = True
                if BaseConfigurations.objects.filter(
                    base_configuration_key=data["var_name"]
                ).first():
                    can_be_added = False
                    messages.warning(
                        request,
                        "Base configuration with provided "
                        + "database variable name already exists.",
                    )
                if can_be_added:
                    base_conf = BaseConfigurations.objects.create(
                        base_configuration_key=data["var_name"],
                        base_configuration_name=data["db_var_name"],
                        base_configuration_value=data["var_value"],
                        description=data["desc"],
                        add_to_cache=(
                            YES
                            if (
                                "add_to_cache" in data and
                                data["add_to_cache"]
                            )
                            else NO
                        ),
                        frequently_used=(
                            YES
                            if (
                                "frequently_used" in data and
                                data["frequently_used"]
                            )
                            else NO
                        ),
                        created_date=timezone.localtime(timezone.now()),
                        updated_date=timezone.localtime(timezone.now()),
                        updated_by=request.user.full_name,
                    )
                    new_data = audit_data_formatter(
                        BASE_CONFIG_CONST, base_conf.id
                    )
                    add_audit_data(
                        request.user,
                        f'{data["var_name"].strip()}',
                        f"{BASE_CONFIG_CONST}-{base_conf.id}",
                        AUDIT_ADD_CONSTANT,
                        BASE_CONFIG_CONST,
                        new_data,
                        None,
                    )
                    remove_configurations_cached_data()
                    if (
                        "frequently_used" in data
                    ):
                        cached_frequently_used_vars = threading.Thread(
                            target=add_frequently_used_base_configurations,
                            daemon=True
                        )
                        cached_frequently_used_vars.start()
                    if (
                        "add_to_cache" in data and
                        data["add_to_cache"]
                    ):
                        add_to_cache_base_configurations(
                            data["var_name"],
                            data["var_value"]
                        )
                    if data["var_name"] in UNDER_MAINTENANCE_KEYS:
                        cache_maintenance_config_keys()
                return JsonResponse(
                    {"status": 1, "message": BASE_CONF_ADDED_SUCCESSFULLY}
                )
            messages.warning(request, BASE_CONF_ADD_ERROR)
        return render(
            request,
            BASE_CONFIRATIONS_TEMPLATE,
            {
                "base_configurations": base_configurations,
                "json_data": json.dumps(base_configurations),
                "pagination_count": BaseConfigurations.objects.filter(
                    base_configuration_key="Pagination_page_rows"
                )
                .first()
                .base_configuration_value
                if BaseConfigurations.objects.filter(
                    base_configuration_key="Pagination_page_rows"
                ).first()
                else 10,
                "data_count": len(base_configurations),
                "data": filter_url(
                    request.user.role_id.access_content.all(),
                    CONFIGURATION_CONST,
                ),
            },
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def update_base_configuration_view(request):
    """update base configuration view"""
    try:
        data = json.loads(request.body)
        if (
            len(data["db_var_name"]) > 0
            and len(data["var_name"]) > 0
            and len(data["var_value"]) > 0
            and len(data["desc"]) > 0
        ):
            can_be_added = True
            if BaseConfigurations.objects.filter(
                ~Q(id=data["id"]), base_configuration_key=data["var_name"]
            ).first():
                can_be_added = False
                messages.warning(
                    request,
                    "Base configuration with provided "
                    + "database variable name already exists.",
                )
            old_data = audit_data_formatter(BASE_CONFIG_CONST, int(data["id"]))
            if can_be_added:
                BaseConfigurations.objects.filter(id=data["id"]).update(
                    base_configuration_key=data["var_name"],
                    base_configuration_name=data["db_var_name"],
                    base_configuration_value=data["var_value"],
                    description=data["desc"],
                    add_to_cache=(
                        YES
                        if (
                            "add_to_cache" in data and
                            data["add_to_cache"]
                        )
                        else NO
                    ),
                    frequently_used=(
                        YES
                        if (
                            "frequently_used" in data and
                            data["frequently_used"]
                        )
                        else NO
                    ),
                    updated_date=timezone.localtime(timezone.now()),
                    updated_by=request.user.full_name,
                )
                new_data = audit_data_formatter(
                    BASE_CONFIG_CONST, int(data["id"])
                )
                if old_data != new_data:
                    add_audit_data(
                        request.user,
                        f'{data["var_name"].strip()}',
                        f'{BASE_CONFIG_CONST}-{int(data["id"])}',
                        AUDIT_UPDATE_CONSTANT,
                        BASE_CONFIG_CONST,
                        new_data,
                        old_data,
                    )
                remove_configurations_cached_data()
                if (
                    "frequently_used" in data
                ):
                    cached_frequently_used_vars = threading.Thread(
                        target=add_frequently_used_base_configurations,
                        daemon=True
                    )
                    cached_frequently_used_vars.start()
                if (
                    "add_to_cache" in data
                ):
                    add_to_cache_base_configurations(
                        data["var_name"],
                        data["var_value"],
                        add_operation=data["add_to_cache"]
                    )
                if data["var_name"] in UNDER_MAINTENANCE_KEYS:
                    cache_maintenance_config_keys()
            return JsonResponse(
                {"status": 1, "message": BASE_CONF_UPDATED_SUCCESSFULLY}
            )
        messages.warning(request, BASE_CONF_ADD_ERROR)
        return JsonResponse(
            {
                "status": 0,
                "message": BASE_CONF_ADD_ERROR,
            }
        )
    except COMMON_ERRORS:
        return JSON_ERROR_OBJECT


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def default_images_view(request):
    """list and add default images view"""
    try:
        base_configurations = return_default_images()
        if request.method == "POST":
            data = json.loads(request.body)
            if len(data["url"]) > 0 and len(data["brand"]) > 0:
                image_data = image_converter(data["url"])
                image = (
                    optimize_image(
                        image_data[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
                        f"{data['brand']}_{randon_string_generator()}"
                        + "."
                        + image_data[1],
                        STATION_INFO_IMAGE,
                    ) if int(data["app_version"]) != APP_VERSION_FOUR else
                    ContentFile(
                        base64.b64decode(image_data[0]),
                        name=f"{data['brand']}_\
                                        {randon_string_generator()}"
                        + "."
                        + image_data[1],
                    )
                )
                can_be_added = True
                if BaseConfigurations.objects.filter(
                    base_configuration_name=data["brand"],
                    for_app_version=data["app_version"]
                ).first():
                    can_be_added = False
                    messages.warning(
                        request,
                        "Default image for provided brand already "+
                        f"exists for app version {data['app_version']}.",
                    )
                if can_be_added:
                    default_image = BaseConfigurations.objects.create(
                        base_configuration_key=(
                            "_".join(data["brand"].lower().split(" "))
                            + "_default_image"
                        ),
                        base_configuration_name=data["brand"],
                        base_configuration_image=image,
                        for_app_version=data["app_version"],
                        created_date=timezone.localtime(timezone.now()),
                        updated_date=timezone.localtime(timezone.now()),
                        updated_by=request.user.full_name,
                    )
                    new_data = audit_data_formatter(
                        BASE_CONFIG_CONST, default_image.id
                    )
                    add_audit_data(
                        request.user,
                        f'{data["brand"].strip()}',
                        f"{BASE_CONFIG_CONST}-{default_image.id}",
                        AUDIT_ADD_CONSTANT,
                        BASE_CONFIG_CONST,
                        new_data,
                        None,
                    )
                    remove_configurations_cached_data()
                return JsonResponse(
                    {"status": 1, "message": DEFAULT_IMAGE_ADDED_SUCCESSFULLY}
                )
            messages.warning(request, DEFAULT_IMAGE_ADD_ERROR)
        return render(
            request,
            DEFAULT_IMAGES_TEMPLATE,
            {
                "base_configurations": base_configurations,
                "json_data": json.dumps(base_configurations),
                "pagination_count": BaseConfigurations.objects.filter(
                    base_configuration_key="Pagination_page_rows"
                )
                .first()
                .base_configuration_value
                if BaseConfigurations.objects.filter(
                    base_configuration_key="Pagination_page_rows"
                ).first()
                else 10,
                "brands": return_brand_list(),
                "data_count": len(base_configurations),
                "data": filter_url(
                    request.user.role_id.access_content.all(),
                    CONFIGURATION_CONST,
                ),
            },
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def update_default_images_view(request):
    """update default images view"""
    try:
        data = json.loads(request.body)
        if len(data["url"]) > 0 and len(data["brand"]) > 0:
            split = data["url"].split(AZURE_BLOB_STORAGE_URL)
            can_be_updated = True
            if BaseConfigurations.objects.filter(
                ~Q(id=data["id"]),
                base_configuration_name=data["brand"],
                for_app_version=data["app_version"]
            ).first():
                can_be_updated = False
                messages.warning(
                    request,
                    "Default image for provided brand already "+
                    f"exists for app version {data['app_version']}.",
                )
            old_data = audit_data_formatter(BASE_CONFIG_CONST, int(data["id"]))
            if can_be_updated:
                update_data = get_object_or_404(
                    BaseConfigurations, id=data["id"]
                )
                if len(split) != 2:
                    image_data = image_converter(data["url"])
                    image = (
                        optimize_image(
                            image_data[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
                            f"{data['brand']}_{randon_string_generator()}"
                            + "."
                            + image_data[1],
                            STATION_INFO_IMAGE,
                        ) if int(data["app_version"]) != APP_VERSION_FOUR else
                        ContentFile(
                            base64.b64decode(image_data[0]),
                            name=f"{data['brand']}_\
                                            {randon_string_generator()}"
                            + "."
                            + image_data[1],
                        )
                    )
                    update_data.base_configuration_image = image
                update_data.base_configuration_key = (
                    "_".join(data["brand"].lower().split(" "))
                    + "_default_image"
                )
                update_data.base_configuration_name = data["brand"].strip()
                update_data.for_app_version = data["app_version"]
                update_data.updated_date = timezone.localtime(timezone.now())
                update_data.updated_by = request.user.full_name
                update_data.save()
                new_data = audit_data_formatter(
                    BASE_CONFIG_CONST, int(data["id"])
                )
                if old_data != new_data:
                    add_audit_data(
                        request.user,
                        f'{data["brand"].strip()}',
                        f'{BASE_CONFIG_CONST}-{int(data["id"])}',
                        AUDIT_UPDATE_CONSTANT,
                        BASE_CONFIG_CONST,
                        new_data,
                        old_data,
                    )
                remove_configurations_cached_data()
            return JsonResponse(
                {"status": 1, "message": DEFAULT_IMAGE_UPDATED_SUCCESSFULLY}
            )
        messages.warning(request, DEFAULT_IMAGE_ADD_ERROR)
    except COMMON_ERRORS:
        return JSON_ERROR_OBJECT
