"""Configurations views"""
# Date - 28/06/2021
# File details-
#   Author      - Manish Pawar
#   Description - This file is mainly focused on APIs and views related
#                   to configrutions data.
#   Name        - Configurations APIs
#   Modified by - Vismay Raul

# These are all the imports that we are exporting from different
# module's from project or library.

import base64
import json
import threading
import concurrent.futures
from urllib import response
from cryptography.fernet import Fernet
from decouple import config

from django.http.response import JsonResponse
from django.shortcuts import render, redirect
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
from sharedServices.decorators import allowed_users, authenticated_user
from sharedServices.common import (
    array_to_string_converter,
    filter_url,
    image_converter,
    redis_connection,
    randon_string_generator,
    remove_all_cache,
    string_to_array_converter,
    hasher,
)
from sharedServices.email_common_functions import (
    email_sender,
)
from sharedServices.common_audit_trail_functions import (
    audit_data_formatter,
    add_audit_data,
)
from sharedServices.constants import (
    AZURE_BLOB_STORAGE_URL,
    CONFIGURATION_CONST,
    CONNECTOR_ERROR,
    GET_METHOD_ALLOWED,
    POST_METHOD_ALLOWED,
    SOMETHING_WRONG,
    SORT_POSTIVIE_ERROR,
    SUCCESS_UPDATE,
    CONNECTORS_CONST,
    SERVICES_CONST,
    AUDIT_ADD_CONSTANT,
    AUDIT_UPDATE_CONSTANT,
    AUDIT_DELETE_CONSTANT,
    COMMON_ERRORS,
    ERROR_TEMPLATE_URL,
    JSON_ERROR_OBJECT,
    YES,
)

from sharedServices.model_files.vehicle_models import ElectricVehicleDatabase
from sharedServices.model_files.station_models import (
    StationConnector,
    StationServices,
)
from sharedServices.model_files.config_models import BaseConfigurations
from sharedServices.shared_station_serializer import (
    caching_station_finder_data,
)
from sharedServices.model_files.app_user_models import MFGUserEV, Profile
from .forms import (
    ConnectorRegistrationForm,
    ServiceRegistrationForm,
    ShopRegistrationForm,
)
from .forms import (
    ConnectorConfiguration,
    ServiceConfiguration,
)

from .app_level_constants import PRE_DOWN_TIME, POST_DOWN_TIME

CACHE_TTL = getattr(settings, "CACHE_TTL", DEFAULT_TIMEOUT)


def remove_configurations_cached_data():
    """this function is used to remove cached data of promotions views"""
    cache.expire("cache_connectors_list", timeout=0)
    cache.expire("cache_amenities_list", timeout=0)
    cache.expire("cache_shops_list", timeout=0)
    cache.expire("cache_ev_indicators_list", timeout=0)
    redis_connection.delete("pre_auth_expiry")
    redis_connection.delete("contactless_tolerance_amount")
    redis_connection.delete("contactless_tolerance_time_in_minutes")
    start_caching_configuration_data = threading.Thread(
        target=caching_station_finder_data,
        daemon=True
    )
    start_caching_configuration_data.start()
    start_removing_config_cached_data = threading.Thread(
        target=remove_all_cache,
        daemon=True
    )
    start_removing_config_cached_data.start()


def get_connectors_list_from_ev_vehicles_db():
    """this function returns list of connector types,
    these types are fetched from
    'ElectricVehicleDatabase' database
    """
    connector_list = []
    conf_connector_list = redis_connection.get("conf_connector_list")
    # if conf_connector_list:
    if conf_connector_list and conf_connector_list.decode("utf-8") != "null":
        connector_list = string_to_array_converter(
            conf_connector_list.decode("utf-8")
        )
    else:
        # filtering station on the basis of promotion availability
        ev_data = ElectricVehicleDatabase.objects.filter().values()
        charge_plugs = [
            row["charge_plug"] for row in ev_data if row["charge_plug"]
        ]
        fastcharge_plugs = [
            row["fastcharge_plug"] for row in ev_data if row["fastcharge_plug"]
        ]
        connector_list = charge_plugs + fastcharge_plugs
        connector_list = list(set(connector_list))
        redis_connection.set(
            "conf_connector_list",
            array_to_string_converter(list(connector_list)),
        )
    # else:
    #     ev_data = ElectricVehicleDatabase.objects.filter().values()
    #     charge_plugs = [
    #         row["charge_plug"] for row in ev_data if row["charge_plug"]
    #     ]
    #     fastcharge_plugs = [
    #         row["fastcharge_plug"] for row in ev_data if row["fastcharge_plug"]
    #     ]
    #     connector_list = charge_plugs + fastcharge_plugs
    #     connector_list = list(set(connector_list))
    #     redis_connection.set(
    #         "conf_connector_list",
    #         array_to_string_converter(list(connector_list)),
    #     )
    return connector_list


def order_by_function_for_shops(
    unique_identifier,
    json_shops_list,
    sorting_key="service_unique_identifier",
    url_key="unique_identifier",
):
    """this function is used to sort shops list"""
    if unique_identifier != "Ascending":
        json_shops_list = sorted(json_shops_list, key=lambda x: x[sorting_key])
    else:
        json_shops_list = sorted(
            json_shops_list, key=lambda x: x[sorting_key], reverse=True
        )
    ordered_shops_list_url = f"?{url_key}={unique_identifier}"
    return [json_shops_list, ordered_shops_list_url]


# This Method is used to render page and filtering table of user management
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=CONFIGURATION_CONST)
def connectors(request):
    """connector list view"""
    try:
        if request.method == "POST":
            data = json.loads(request.body)
            if len(data["url"]) > 0 and len(data["altUrl"]) > 0 and len(data["type"]) > 2:
                image_data = image_converter(data["url"])
                image = ContentFile(
                    base64.b64decode(image_data[0]),
                    name=f"{data['type']}_\
                                    {randon_string_generator()}"
                    + "."
                    + image_data[1],
                )
                image_alt_data = image_converter(data["altUrl"])
                alt_image = ContentFile(
                    base64.b64decode(image_alt_data[0]),
                    name=f"alt_{data['type']}_\
                                    {randon_string_generator()}"
                    + "."
                    + image_alt_data[1],
                )
                previos_connectors_list = [
                    connector.connector_plug_type
                    for connector in ConnectorConfiguration.objects.all() 
                    if connector.for_app_version == int(data["app_version"])
                ]
                if data["type"].strip() in previos_connectors_list:
                    messages.warning(
                        request,
                        "Connector type with provided type already "+
                        f"added for the app version {data['app_version']}."
                    )
                else:
                    try:
                        data["sorting_order"] = int(data["sorting_order"])
                        if data["sorting_order"] <= 0:
                            raise ValueError(SORT_POSTIVIE_ERROR)
                    except ValueError:
                        messages.warning(request, SORT_POSTIVIE_ERROR)
                        return JsonResponse(
                            {
                                "status": 0,
                                "message": SORT_POSTIVIE_ERROR,
                            }
                        )
                    connector = ConnectorConfiguration.objects.filter(
                        sorting_order=data["sorting_order"],
                        for_app_version=int(data["app_version"])
                    )
                    if connector.first() is not None:
                        messages.warning(
                            request,
                            "Entered sorting order number is added for another connector for "+
                            f"the app version {data['app_version']}."
                        )
                        return JsonResponse(
                            {
                                "status": 0,
                                "message": "Entered sorting order is \
                                    added for another connector.",
                            }
                        )
                    connector = ConnectorConfiguration.objects.create(
                        connector_plug_type=data["type"].strip(),
                        connector_plug_type_name=data["type"].strip(),
                        sorting_order=int(data["sorting_order"]),
                        for_app_version=int(data["app_version"]),
                        image_path=image,
                        alternate_image_path=alt_image,
                        created_date=timezone.localtime(timezone.now()),
                        updated_date=timezone.localtime(timezone.now()),
                        updated_by=request.user.full_name,
                    )
                    new_data = audit_data_formatter(
                        CONNECTORS_CONST, connector.id
                    )
                    add_audit_data(
                        request.user,
                        f'{data["type"].strip()}',
                        f"{CONNECTORS_CONST}-{connector.id}",
                        AUDIT_ADD_CONSTANT,
                        CONNECTORS_CONST,
                        new_data,
                        None,
                    )
                remove_configurations_cached_data()
                return JsonResponse({"status": 1, "message": SUCCESS_UPDATE})
            messages.warning(request, CONNECTOR_ERROR)
        conn = ConnectorRegistrationForm()

        sorting_order = request.GET.get("sorting_order", None)
        if "cache_connectors_list" in cache:
            # get results from cache
            connectors_list = cache.get("cache_connectors_list")
        else:
            connectors_list = [
                {
                    "id": connector.id,
                    "connector_plug_type": connector.connector_plug_type,
                    "connector_plug_type_name": (
                        connector.connector_plug_type_name
                    ),
                    "sorting_order": connector.sorting_order,
                    "app_version": connector.for_app_version,
                    "get_image_path": connector.get_image_path(),
                    "get_alt_image_path": connector.get_alt_image_path(),
                }
                for connector in ConnectorConfiguration.objects.all()
            ]

            cache.set(
                "cache_connectors_list", connectors_list, timeout=CACHE_TTL
            )

        (
            connectors_list,
            ordered_connectors_list_url,
        ) = order_by_function_for_shops(
            sorting_order,
            connectors_list,
            sorting_key="sorting_order",
            url_key="sorting_order",
        )
        url_data = filter_url(
            request.user.role_id.access_content.all(), CONFIGURATION_CONST
        )
        ev_connector_list = get_connectors_list_from_ev_vehicles_db()

        context = {
            "conn_form": conn,
            "connectors_list": connectors_list,
            "json_data": json.dumps(connectors_list),
            "pagination_count": BaseConfigurations.objects.filter(
                base_configuration_key="Pagination_page_rows"
            )
            .first()
            .base_configuration_value
            if BaseConfigurations.objects.filter(
                base_configuration_key="Pagination_page_rows"
            ).first()
            else 10,
            "data": url_data,
            "data_count": len(connectors_list),
            "connectors_name_list": ev_connector_list,
            "prev_sorting_order": sorting_order,
            "update_url_param": ordered_connectors_list_url,
        }
        return render(request, "configurations/configurations.html", context)
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


def update_station_connector_on_connector_change(connector_id, plug_type):
    """this function updates station connectors
    with updated station connector details"""

    connector = ConnectorConfiguration.objects.filter(id=connector_id)
    if connector.first():
        StationConnector.objects.filter(
            plug_type_name=connector.first().connector_plug_type_name
        ).update(plug_type_name=plug_type)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def check_connector_sorting_order_availability(request):
    """deactivate user"""
    try:
        if request.method == "POST":
            data = json.loads(request.body)
            try:
                data["unique_identifier"] = int(data["unique_identifier"])
                if data["unique_identifier"] <= 0:
                    raise ValueError(SORT_POSTIVIE_ERROR)
            except ValueError:
                return JsonResponse(
                    status=400,
                    data={
                        "status": "true",
                        "messages": SORT_POSTIVIE_ERROR,
                    },
                )
            try:
                connector = ConnectorConfiguration.objects.filter(
                    sorting_order=data["unique_identifier"]
                )
                if data["update_query"]:
                    connector = connector.filter(~Q(id=int(data["column_id"])))
                if connector.first() is None:
                    return JsonResponse(
                        status=200,
                        data={
                            "status": "true",
                            "messages": "Sorting order number available",
                        },
                    )
                return JsonResponse(
                    status=400,
                    data={
                        "status": "true",
                        "messages": (
                            "Entered sorting order number is added "
                            + "for another connector"
                        ),
                    },
                )
            except (NotImplementedError, ValueError, AttributeError):
                return JsonResponse(
                    status=400,
                    data={"status": "false", "messages": SOMETHING_WRONG},
                )
        return JsonResponse(
            status=400,
            data={"status": "false", "messages": SOMETHING_WRONG},
        )
    except COMMON_ERRORS:
        return JSON_ERROR_OBJECT


# This API  update Connector information
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=CONFIGURATION_CONST)
def update_connector(request):
    """Update connector view"""
    try:
        data = json.loads(request.body)
        if (
            len(data["url"]) > 0
            and len(data["altUrl"]) > 0
            and len(data["type"]) > 2
            and data["type"] != "null"
        ):
            split = data["url"].split(AZURE_BLOB_STORAGE_URL)
            alt_img_split = data["altUrl"].split(AZURE_BLOB_STORAGE_URL)
            update_data = get_object_or_404(
                ConnectorConfiguration, id=data["id"]
            )
            old_data = audit_data_formatter(CONNECTORS_CONST, int(data["id"]))
            try:
                data["sorting_order"] = int(data["sorting_order"])
                if data["sorting_order"] <= 0:
                    raise ValueError(SORT_POSTIVIE_ERROR)
            except ValueError:
                messages.warning(request, SORT_POSTIVIE_ERROR)
                return JsonResponse(
                    {
                        "status": 0,
                        "message": SORT_POSTIVIE_ERROR,
                    }
                )
            previos_connectors = ConnectorConfiguration.objects.filter(
                ~Q(id=int(data["id"]))
            )
            previos_connectors_list = [
                connector.connector_plug_type
                for connector in previos_connectors
                if connector.for_app_version == int(data["app_version"])
            ]
            if data["type"].strip() in previos_connectors_list:
                text_op = (
                    "Connector type with provided type already added for "+
                    f"the app version {data['app_version']}."
                )
                messages.warning(request, text_op)
                return JsonResponse({"status": 0, "message": text_op})
            if (
                previos_connectors.filter(
                    sorting_order=data["sorting_order"],
                    for_app_version=int(data["app_version"])
                ).first()
                is not None
            ):
                messages.warning(
                    request,
                    "Entered sorting order number is added for another connector for "+
                    f"the app version {data['app_version']}."
                )
                return JsonResponse(response)
            if len(split) != 2:
                image_data = image_converter(data["url"])
                image = ContentFile(
                    base64.b64decode(image_data[0]),
                    name=f"{data['type']}_{randon_string_generator()}"
                    + "."
                    + image_data[1],
                )
                update_data.image_path = image
            if len(alt_img_split) != 2:
                image_alt_data = image_converter(data["altUrl"])
                alt_image = ContentFile(
                    base64.b64decode(image_alt_data[0]),
                    name=f"alt_{data['type']}_{randon_string_generator()}"
                    + "."
                    + image_alt_data[1],
                )
                update_data.alternate_image_path = alt_image
            update_data.connector_plug_type = data["type"].strip()
            update_data.connector_plug_type_name = data["type"].strip()
            update_data.sorting_order = int(data["sorting_order"])
            update_data.for_app_version = int(data["app_version"])
            update_data.updated_date = timezone.localtime(timezone.now())
            update_data.updated_by = request.user.full_name
            update_data.save()
            update_station_connector_on_connector_change(
                int(data["id"]), data["type"].strip()
            )
            new_data = audit_data_formatter(CONNECTORS_CONST, int(data["id"]))
            if old_data != new_data:
                add_audit_data(
                    request.user,
                    f'{data["type"].strip()}',
                    f'{CONNECTORS_CONST}-{int(data["id"])}',
                    AUDIT_UPDATE_CONSTANT,
                    CONNECTORS_CONST,
                    new_data,
                    old_data,
                )
            remove_configurations_cached_data()
            return JsonResponse({"status": 1, "message": SUCCESS_UPDATE})
        messages.warning(request, CONNECTOR_ERROR)
        return JsonResponse(
            {
                "status": 0,
                "message": CONNECTOR_ERROR,
            }
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


# This API  delete Connector information
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=CONFIGURATION_CONST)
def delete_connector(request, connector_id):
    """delete connector view"""
    try:
        old_data = audit_data_formatter(CONNECTORS_CONST, int(connector_id))
        connector = ConnectorConfiguration.objects.get(pk=connector_id)

        add_audit_data(
            request.user,
            f"{connector.connector_plug_type}",
            f"{CONNECTORS_CONST}-{int(connector_id)}",
            AUDIT_DELETE_CONSTANT,
            CONNECTORS_CONST,
            None,
            old_data,
        )
        update_station_connector_on_connector_change(int(connector_id), "")
        connector.delete()
        remove_configurations_cached_data()
        return redirect("connectors")
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


# Too Add and Show Aminities
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=CONFIGURATION_CONST)
def aminities(request):
    """Amenity list view"""
    try:
        if request.method == "POST":
            data = json.loads(request.body)
            if (
                len(data["url_w_o_text"]) > 0
                and len(data["url_w_text"]) > 0
                and len(data["service_name"]) > 2
            ):
                image_data = image_converter(data["url_w_o_text"])
                image = ContentFile(
                    base64.b64decode(image_data[0]),
                    name=f"{data['service_name']}_{randon_string_generator()}"
                    + "."
                    + image_data[1],
                )
                w_text_image_data = image_converter(data["url_w_text"])
                w_text_image = ContentFile(
                    base64.b64decode(w_text_image_data[0]),
                    name=f"{data['service_name']}_{randon_string_generator()}"
                    + "."
                    + w_text_image_data[1],
                )
                try:
                    data["unique_identifier"] = int(data["unique_identifier"])
                    if data["unique_identifier"] <= 0:
                        raise ValueError(SORT_POSTIVIE_ERROR)
                except (ValueError,):
                    messages.warning(
                        request, "Sorting order must be a number."
                    )
                    return JsonResponse(
                        {"status": 0, "message": SOMETHING_WRONG}
                    )
                service = ServiceConfiguration.objects.filter(
                    service_unique_identifier=data["unique_identifier"]
                )
                if service.first() is not None:
                    messages.warning(
                        request,
                        "Entered sorting order number is added \
                            for another service.",
                    )
                    return JsonResponse(
                        {
                            "status": 0,
                            "message": "Entered sorting order number is added \
                                        for another service.",
                        }
                    )
                amenity = ServiceConfiguration.objects.create(
                    service_name=data["service_name"].strip(),
                    service_type="Amenity",
                    image_path=image,
                    image_path_with_text=w_text_image,
                    service_unique_identifier=int(data["unique_identifier"]),
                    created_date=timezone.localtime(timezone.now()),
                    updated_date=timezone.localtime(timezone.now()),
                    updated_by=request.user.full_name,
                )
                new_data = audit_data_formatter(SERVICES_CONST, amenity.id)
                add_audit_data(
                    request.user,
                    f'{data["service_name"].strip()}',
                    f"{SERVICES_CONST}-{amenity.id}",
                    AUDIT_ADD_CONSTANT,
                    SERVICES_CONST,
                    new_data,
                    None,
                )
                remove_configurations_cached_data()
                return JsonResponse({"status": 1, "message": SUCCESS_UPDATE})
            messages.warning(
                request,
                "Amenity name and image with "
                + "and without text are required fields.",
            )
        unique_identifier = request.GET.get("unique_identifier", None)
        amenity = ServiceRegistrationForm()
        if (
            "cache_amenities_list" in cache
            and "cache_json_amenities_list" in cache
        ):  # get results from cache
            amenities_list = cache.get("cache_amenities_list")
            json_amenity_list = cache.get("cache_json_amenities_list")
        else:
            amenities_list = ServiceConfiguration.objects.filter(
                service_type="Amenity"
            )
            json_amenity_list = [
                {
                    "id": amenity.id,
                    "service_name": amenity.service_name,
                    "get_image_path": amenity.get_image_path(),
                    "get_image_path_with_text": (
                        amenity.get_image_path_with_text()
                    ),
                    "service_unique_identifier": (
                        amenity.service_unique_identifier
                    ),
                }
                for amenity in amenities_list
            ]
            cache.set(
                "cache_amenities_list", amenities_list, timeout=CACHE_TTL
            )
            cache.set(
                "cache_json_amenities_list",
                json_amenity_list,
                timeout=CACHE_TTL,
            )

        (
            json_amenity_list,
            ordered_shops_list_url,
        ) = order_by_function_for_shops(unique_identifier, json_amenity_list)
        url_data = filter_url(
            request.user.role_id.access_content.all(), CONFIGURATION_CONST
        )
        context = {
            "amen_form": amenity,
            "amenities_list": amenities_list,
            "json_data": json.dumps(json_amenity_list),
            "pagination_count": BaseConfigurations.objects.filter(
                base_configuration_key="Pagination_page_rows"
            )
            .first()
            .base_configuration_value
            if BaseConfigurations.objects.filter(
                base_configuration_key="Pagination_page_rows"
            ).first()
            else 10,
            "data_count": amenities_list.count(),
            "prev_unique_identifier": unique_identifier,
            "data": url_data,
            "update_url_param": ordered_shops_list_url,
        }
        return render(request, "configurations/aminities.html", context)
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def check_service_id_availability(request):
    """deactivate user"""
    try:
        if request.method == "POST":
            data = json.loads(request.body)
            try:
                data["unique_identifier"] = int(data["unique_identifier"])
                if data["unique_identifier"] <= 0:
                    raise ValueError(SORT_POSTIVIE_ERROR)
            except ValueError:
                return JsonResponse(
                    status=400,
                    data={
                        "status": "true",
                        "messages": SORT_POSTIVIE_ERROR,
                    },
                )
            try:
                service = ServiceConfiguration.objects.filter(
                    service_unique_identifier=data["unique_identifier"]
                )
                if data["update_query"]:
                    service = service.filter(~Q(id=int(data["column_id"])))
                if service.first() is None:
                    return JsonResponse(
                        status=200,
                        data={
                            "status": "true",
                            "messages": "Sorting order number available",
                        },
                    )
                # Updaning user status Inactive
                return JsonResponse(
                    status=400,
                    data={
                        "status": "true",
                        "messages": (
                            "Entered sorting order numberis added "
                            + "for another service"
                        ),
                    },
                )
            except (NotImplementedError, ValueError, AttributeError):
                return JsonResponse(
                    status=400,
                    data={"status": "false", "messages": SOMETHING_WRONG},
                )
        return JsonResponse(
            status=400,
            data={"status": "false", "messages": SOMETHING_WRONG},
        )
    except COMMON_ERRORS:
        return JSON_ERROR_OBJECT


# This API  update amenity information
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=CONFIGURATION_CONST)
def update_amenity(request):
    "update amenity view"
    try:
        data = json.loads(request.body)
        if (
            len(data["url_w_o_text"]) > 0
            and len(data["url_w_text"]) > 0
            and len(data["name"]) > 2
        ):
            split = data["url_w_o_text"].split(AZURE_BLOB_STORAGE_URL)
            split_with_text = data["url_w_text"].split(AZURE_BLOB_STORAGE_URL)
            try:
                data["unique_identifier"] = int(data["unique_identifier"])
                if data["unique_identifier"] <= 0:
                    raise ValueError(SORT_POSTIVIE_ERROR)
            except ValueError:
                messages.warning(request, "Sorting order must be a number.")
                return JsonResponse({"status": 0, "message": SOMETHING_WRONG})
            old_data = audit_data_formatter(SERVICES_CONST, int(data["id"]))
            service = ServiceConfiguration.objects.filter(
                ~Q(id=data["id"]),
                service_unique_identifier=data["unique_identifier"],
            )
            if service.first() is not None:
                messages.warning(
                    request,
                    "Entered sorting order number is added for \
                        another service.",
                )
                return JsonResponse(response)
            update_data = get_object_or_404(
                ServiceConfiguration, id=data["id"]
            )
            if len(split) != 2:
                image_data = image_converter(data["url_w_o_text"])
                image = ContentFile(
                    base64.b64decode(image_data[0]),
                    name=f"{data['name']}_{randon_string_generator()}"
                    + "."
                    + image_data[1],
                )
                update_data.image_path = image
            if len(split_with_text) != 2:
                image_data_w_text = image_converter(data["url_w_text"])
                image_w_text = ContentFile(
                    base64.b64decode(image_data_w_text[0]),
                    name=f"{data['name']}_{randon_string_generator()}"
                    + "."
                    + image_data_w_text[1],
                )
                update_data.image_path_with_text = image_w_text
            update_data.service_name = data["name"].strip()
            update_data.service_unique_identifier = data["unique_identifier"]
            update_data.updated_date = timezone.localtime(timezone.now())
            update_data.updated_by = request.user.full_name
            update_data.save()
            new_data = audit_data_formatter(SERVICES_CONST, int(data["id"]))
            if old_data != new_data:
                add_audit_data(
                    request.user,
                    f'{data["name"].strip()}',
                    f'{SERVICES_CONST}-{int(data["id"])}',
                    AUDIT_UPDATE_CONSTANT,
                    SERVICES_CONST,
                    new_data,
                    old_data,
                )
            remove_configurations_cached_data()
            return JsonResponse({"status": 1, "message": SUCCESS_UPDATE})
        messages.warning(
            request,
            "Amenity name and image with "
            + "and without text are required fields.",
        )
        return JsonResponse(
            {
                "status": 0,
                "message": "Amenity name and image are required fields",
            }
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


# This API  delete amenity information


@authenticated_user
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@allowed_users(section=CONFIGURATION_CONST)
def delete_amenity(request, amenity_id):
    "delete amenity"
    try:
        old_data = audit_data_formatter(SERVICES_CONST, int(amenity_id))
        amenity = ServiceConfiguration.objects.get(pk=amenity_id)

        add_audit_data(
            request.user,
            f"{amenity.service_name}",
            f"{SERVICES_CONST}-{int(amenity_id)}",
            AUDIT_DELETE_CONSTANT,
            SERVICES_CONST,
            None,
            old_data,
        )
        StationServices.objects.filter(service_id=amenity).delete()
        amenity.delete()
        remove_configurations_cached_data()
        return redirect("amenities")
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


# This API  update amenity information
@authenticated_user
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@allowed_users(section=CONFIGURATION_CONST)
def shops(request):
    "shop list view"
    try:
        if request.method == "POST":
            data = json.loads(request.body)
            if (
                len(data["url"]) > 0
                and len(data["service_name"]) > 2
                and len(data["type"]) > 2
            ):
                image_data = image_converter(data["url"])
                image = ContentFile(
                    base64.b64decode(image_data[0]),
                    name=f"{data['service_name']}_{randon_string_generator()}"
                    + "."
                    + image_data[1],
                )
                try:
                    data["unique_identifier"] = int(data["unique_identifier"])
                    if data["unique_identifier"] <= 0:
                        raise ValueError(SORT_POSTIVIE_ERROR)
                except ValueError:
                    messages.warning(request, SORT_POSTIVIE_ERROR)
                    return JsonResponse(
                        {
                            "status": 0,
                            "message": SORT_POSTIVIE_ERROR,
                        }
                    )
                service = ServiceConfiguration.objects.filter(
                    service_unique_identifier=data["unique_identifier"]
                )
                if service.first() is not None:
                    messages.warning(
                        request,
                        "Entered sorting order is added for another service.",
                    )
                    return JsonResponse(
                        {
                            "status": 0,
                            "message": "Entered sorting order is \
                                added for another service.",
                        }
                    )
                shop = ServiceConfiguration.objects.create(
                    service_name=data["service_name"].strip(),
                    service_type=data["type"],
                    service_unique_identifier=data["unique_identifier"],
                    image_path=image,
                    created_date=timezone.localtime(timezone.now()),
                    updated_date=timezone.localtime(timezone.now()),
                    updated_by=request.user.full_name,
                )
                new_data = audit_data_formatter(SERVICES_CONST, shop.id)
                add_audit_data(
                    request.user,
                    f'{data["service_name"].strip()}',
                    f"{SERVICES_CONST}-{shop.id}",
                    AUDIT_ADD_CONSTANT,
                    SERVICES_CONST,
                    new_data,
                    None,
                )
                remove_configurations_cached_data()
                return JsonResponse({"status": 1, "message": SUCCESS_UPDATE})
            messages.warning(request, CONNECTOR_ERROR)
        add_shop_form = ShopRegistrationForm()
        if request.method == "GET":
            unique_identifier = request.GET.get("unique_identifier", None)
            type_of_shop = request.GET.get("type", None)

        if (
            "cache_shops_list" in cache and "cache_json_shops_list" in cache
        ):  # get results from cache
            shops_list = cache.get("cache_shops_list")
            json_shops_list = cache.get("cache_json_shops_list")
        else:
            shops_list = ServiceConfiguration.objects.filter(
                ~Q(service_type="Amenity")
            )
            json_shops_list = [
                {
                    "id": shop.id,
                    "service_name": shop.service_name,
                    "get_image_path": shop.get_image_path(),
                    "service_type": shop.service_type,
                    "service_unique_identifier": (
                        shop.service_unique_identifier
                    ),
                }
                for shop in shops_list
            ]
            cache.set("cache_shops_list", shops_list, timeout=CACHE_TTL)
            cache.set(
                "cache_json_shops_list", json_shops_list, timeout=CACHE_TTL
            )
        (
            json_shops_list,
            ordered_shops_list_url,
        ) = order_by_function_for_shops(unique_identifier, json_shops_list)
        url_for_shops = ""
        if type_of_shop and type_of_shop != "All":
            url_for_shops = f"&type={type_of_shop}"
            shops_list = shops_list.filter(service_type=type_of_shop)
            json_shops_list = [
                shop
                for shop in json_shops_list
                if shops_list.filter(id=shop["id"]).first()
            ]

        url_data = filter_url(
            request.user.role_id.access_content.all(), CONFIGURATION_CONST
        )
        context = {
            "shops_types": ["All", "Retail", "Food To Go"],
            "option": type_of_shop,
            "shop_form": add_shop_form,
            "shops_list": shops_list,
            "json_data": json.dumps(json_shops_list),
            "pagination_count": BaseConfigurations.objects.filter(
                base_configuration_key="Pagination_page_rows"
            )
            .first()
            .base_configuration_value
            if BaseConfigurations.objects.filter(
                base_configuration_key="Pagination_page_rows"
            ).first()
            else 10,
            "data_count": shops_list.count(),
            "prev_unique_identifier": unique_identifier,
            "data": url_data,
            "update_url_param": ordered_shops_list_url + url_for_shops,
        }
        return render(request, "configurations/shops.html", context)
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


# This API  update shop information


@authenticated_user
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
def update_shop(request):
    """Update shop view"""
    try:
        data = json.loads(request.body)
        if len(data["url"]) > 0 and len(data["name"]) > 2:
            split = data["url"].split(AZURE_BLOB_STORAGE_URL)
            update_data = get_object_or_404(
                ServiceConfiguration, id=data["id"]
            )
            old_data = audit_data_formatter(SERVICES_CONST, int(data["id"]))
            if len(split) != 2:
                image_data = image_converter(data["url"])
                image = ContentFile(
                    base64.b64decode(image_data[0]),
                    name=f"{data['name']}_{randon_string_generator()}"
                    + "."
                    + image_data[1],
                )
                update_data.image_path = image
            try:
                data["unique_identifier"] = int(data["unique_identifier"])
                if data["unique_identifier"] <= 0:
                    raise ValueError(SORT_POSTIVIE_ERROR)
            except ValueError:
                messages.warning(request, SORT_POSTIVIE_ERROR)
                return JsonResponse(
                    {
                        "status": 0,
                        "message": SORT_POSTIVIE_ERROR,
                    }
                )
            service = ServiceConfiguration.objects.filter(
                ~Q(id=data["id"]),
                service_unique_identifier=data["unique_identifier"],
            )
            if service.first() is not None:
                messages.warning(
                    request,
                    "Entered sorting order number is added for\
                        another service.",
                )
                return JsonResponse(response)
            update_data.service_type = data["type"]
            update_data.service_name = data["name"].strip()
            update_data.service_unique_identifier = data["unique_identifier"]
            update_data.updated_date = timezone.localtime(timezone.now())
            update_data.updated_by = request.user.full_name
            update_data.save()
            new_data = audit_data_formatter(SERVICES_CONST, int(data["id"]))
            if old_data != new_data:
                add_audit_data(
                    request.user,
                    f'{data["name"].strip()}',
                    f'{SERVICES_CONST}-{int(data["id"])}',
                    AUDIT_UPDATE_CONSTANT,
                    SERVICES_CONST,
                    new_data,
                    old_data,
                )
            remove_configurations_cached_data()
            return JsonResponse({"status": 1, "message": SUCCESS_UPDATE})
        messages.warning(request, "Shop name and image are required fields.")
        return JsonResponse(
            {
                "status": 0,
                "message": "Shop name and image are required fields.",
            }
        )
    except COMMON_ERRORS:
        return JSON_ERROR_OBJECT


# This API  update shop information
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def delete_shop(request, shop_id):
    """delete shop view"""
    try:
        old_data = audit_data_formatter(SERVICES_CONST, int(shop_id))
        shop = ServiceConfiguration.objects.get(pk=shop_id)

        add_audit_data(
            request.user,
            f"{shop.service_name}",
            f"{SERVICES_CONST}-{int(shop_id)}",
            AUDIT_DELETE_CONSTANT,
            SERVICES_CONST,
            None,
            old_data,
        )
        StationServices.objects.filter(service_id=shop).delete()
        shop.delete()
        remove_configurations_cached_data()
        return redirect("shops")
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


def send_downtime_updates_via_mail(email_type):
    """this function is used to send downtime updates to app users"""
    users = MFGUserEV.objects.filter(
        ~Q(
            user_email="",
        ),
        ~Q(user_profile__email_marketing_update_preference_status=False),
        ~Q(user_profile__email_news_letter_preference_status=False),
        ~Q(user_profile__email_promotion_preference_status=False),
        ~Q(user_profile__unsubscribed_from_emails=YES),
    )

    def send_email_notifications(user):
        """this function send downtime mail to users"""
        decrypter = Fernet(user.key)
        user_first_name = decrypter.decrypt(user.first_name).decode()
        user_email = decrypter.decrypt(user.encrypted_email).decode()

        to_emails = [
            (
                user_email,
                user_first_name,
            )
        ]
        template_id = config("DJANGO_APP_PRE_DOWN_TIME_TEMPLATE_ID")
        if email_type == POST_DOWN_TIME:
            template_id = config("DJANGO_APP_POST_DOWN_TIME_TEMPLATE_ID")
        email_sender(template_id, to_emails, {"user_name": user_first_name})

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        executor.map(
            send_email_notifications,
            list(users),
        )
    print("all mail sent")


# this apis is used to send downtime mails
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def email_notifications(request):
    """send downtime mail"""
    try:
        if request.user.role_id.role_name != "Super admin":
            return redirect("dashboard")
        if request.method == "POST":
            email_type = request.POST.get("email_type", None)
            if email_type and email_type in [PRE_DOWN_TIME, POST_DOWN_TIME]:
                start_time = threading.Thread(
                    target=send_downtime_updates_via_mail,
                    args=[email_type],
                    daemon=True
                )
                start_time.start()
                messages.success(request, "Email sending process started.")
            else:
                messages.warning(
                    request,
                    "Invalid email type provided. "
                    + "must be either pre_down_time or post_down_type.",
                )

        url_data = filter_url(
            request.user.role_id.access_content.all(), CONFIGURATION_CONST
        )
        context = {
            "data": url_data,
        }
        return render(
            request, "configurations/send_down_time_email.html", context
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def unsubscribe_user_from_emails(request, user_email):
    Profile.objects.filter(
        user_id__user_email=hasher(user_email)
    ).update(
        email_marketing_update_preference_status=False,
        email_news_letter_preference_status=False,
        email_promotion_preference_status=False,
        updated_by=request.user.full_name,
        unsubscribed_from_emails=YES,
    )
    return redirect("connectors")
