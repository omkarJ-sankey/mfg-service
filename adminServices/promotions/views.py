"""promotions views"""

# Date - 26/06/2021

# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on views(backend logic)
#                      related to promotions.
#   Name            - Promotions Views
#   Modified by     - Manish Pawar
#   Modified date   - 26/06/2021

# imports required to create views
import sys
import re
import json
from datetime import timedelta
from types import SimpleNamespace
from io import StringIO
from passlib.hash import django_pbkdf2_sha256 as handler

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.db import DataError, DatabaseError
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.utils import timezone
from django.urls import reverse
from django.conf import settings

# pylint:disable=import-error
from sharedServices.model_files.promotions_models import (
    Promotions,
    PromotionsAvailableOn,
)
from sharedServices.model_files.station_models import (
    ServiceConfiguration,
    StationServices,
    Stations,
)
from sharedServices.model_files.bulk_models import (
    BulkUploadErrorMessages,
    BulkUploadProgress,
)
from sharedServices.model_files.audit_models import AuditTrail
from sharedServices.decorators import allowed_users, authenticated_user
from sharedServices.common import (
    date_formater_for_frontend_date,
    end_date_formater_for_frontend_date,
    export_data_function_multi_tabs,
    filter_url,
    image_converter,
    order_by_function,
    pagination_and_filter_func,
    randon_string_generator,
    string_to_array_converter,
    filter_function_for_base_configuration,
    date_difference_function,
    search_validator,
)
from sharedServices.common_audit_trail_functions import (
    add_audit_data,
    audit_data_formatter,
)
from sharedServices.image_optimization_funcs import optimize_image
from sharedServices.constants import (
    PROMOTIONS_CONST,
    UNQUIE_RETAILBAR_CODE,
    YES,
    NO,
    EXPORT_TRUE,
    GET_METHOD_ALLOWED,
    POST_METHOD_ALLOWED,
    PROMOTION_IMAGE,
    IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN,
    AUDIT_DELETE_CONSTANT,
    AUDIT_UPDATE_CONSTANT,
    COMMON_ERRORS,
    ERROR_TEMPLATE_URL,
    JSON_ERROR_OBJECT,
    API_ERROR_OBJECT,
    ACTIVE,
    DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET,
)
from adminServices.loyalty.loyalty_helper_functions import (
    return_stations_master_data_for_loyalties_and_promotions,
)

from ..dashboard.app_level_constants import (
    DASHBOARD_DATA_DAYS_LIMIT,
    DEFAULT_DASHBOARD_DATA_DAYS_LIMIT,
)
from .db_operators import add_single_promotion, update_single_promotion
from .promotions_helper_functions import (
    remove_promotions_cached_data,
    all_stations_qs,
    return_available_for_values,
    return_offer_type_values,
    return_ops_regions,
    return_status_list,
    export_promotion_data,
)
from .app_level_constants import FILETERED_PROMOTIONS, FILETERED_DATA, URL_DATA

CACHE_TTL = getattr(settings, "CACHE_TTL", DEFAULT_TIMEOUT)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=PROMOTIONS_CONST)
def add_promotions(request):
    """add promotion view"""
    try:
        # Database call to fetch all services from configurations.
        query_params_str = ""
        for q_param in request.GET:
            if len(query_params_str) == 0:
                query_params_str = f"?{q_param}={request.GET.get(q_param)}"
            else:
                query_params_str += f"&{q_param}={request.GET.get(q_param)}"
        shops_from_configurations = ServiceConfiguration.objects.filter(
            ~Q(service_type="Amenity")
        ).values("id", "service_name", "image_path", "service_type")

        shops_list = [
            [i["id"], i["service_name"]] for i in shops_from_configurations
        ]
        shops_list.sort(key=lambda shop: shop[1].lower())

        # This condition makes sure that the request is
        # POST so that we can safely
        # insert data in tables.
        if request.method == "POST":
            try:
                # Decoding post data (the data is in form of JSON)
                post_data_from_front_end = json.loads(
                    request.POST["getdata"],
                    object_hook=lambda d: SimpleNamespace(**d),
                )

                add_single_promotion(
                    post_data_from_front_end,
                    request.user,
                    shops_from_configurations,
                )

                # sending response to the request
                remove_promotions_cached_data()
                # Dumping data so that we can handle data in javascript
                return JsonResponse(
                    {
                        "status": 1,
                        "message": "ok",
                        "url": reverse("promotions_list"),
                    }
                )
            except (NotImplementedError, ValueError, AttributeError) as error:
                (
                    exception_type_add,
                    exception_object_add,
                    exception_traceback_add,
                ) = sys.exc_info()
                filename_add = (
                    exception_traceback_add.tb_frame.f_code.co_filename
                )
                line_number_update = exception_traceback_add.tb_lineno
                print(exception_object_add, "**exception object")
                print("Exception type: ", exception_type_add)
                print("File name: ", filename_add)
                print("Line number: ", line_number_update)
                print("Error", str(error))
                print(f"Error time {timezone.localtime(timezone.now())}")
                return JsonResponse(
                    {
                        "status": 0,
                        # "message": str(error),
                        "message": "Error occured while adding promotion",
                        "url": reverse("promotions_list"),
                    }
                )

        url_data = filter_url(
            request.user.role_id.access_content.all(), PROMOTIONS_CONST
        )
        return render(
            request,
            "promotions/add_promotions.html",
            context={
                "edit_page": "No",
                "available_for_list": return_available_for_values(),
                "status_list": return_status_list(),
                "offer_types": return_offer_type_values(),
                "shops": shops_list,
                # "ops_regions": return_ops_regions(),
                "data": url_data,
                "query_params_str": query_params_str,
                # "all_stations_from_backend": all_stations_qs(),
                "stations_master_data": return_stations_master_data_for_loyalties_and_promotions(),
            },
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


def check_station_have_shop_or_not(
    station,
    shops,
):
    """this function returns true if station have shop"""
    if "All" in shops:
        return True
    for service in station["services"]:
        if service["service_id__service_name"] in shops:
            return True
    return False


def post_data_op(stations, iteration_data, key, value):
    """checkboxes to select stations"""
    data_to_send = []
    if value[2]:
        stations = [
            station
            for station in stations
            if len(station["services"]) > 0
            and check_station_have_shop_or_not(
                station,
                value[2],
            )
        ]
    if value[0] and ("All" in value[0]) and value[1] and ("All" in value[1]):
        for i in stations:
            if (
                len(i[iteration_data[0]]) > 0
                and i[iteration_data[0]] not in data_to_send
            ):
                data_to_send.append(
                    [i["id"], i[iteration_data[0]]]
                    if iteration_data[0] == "station_id"
                    else i[iteration_data[0]]
                )

    if (
        value[0]
        and ("All" in value[0])
        and value[1]
        and ("All" not in value[1])
    ):
        for i in stations:
            if (
                len(i[iteration_data[0]]) > 0
                and i[iteration_data[1]] in value[1]
                and i[iteration_data[0]] not in data_to_send
            ):
                data_to_send.append(
                    [i["id"], i[iteration_data[0]]]
                    if iteration_data[0] == "station_id"
                    else i[iteration_data[0]]
                )

    if value[0] and ("All" in value[0]) and not value[1]:
        for i in stations:
            if (
                len(i[iteration_data[0]]) > 0
                and i[iteration_data[0]] not in data_to_send
            ):
                data_to_send.append(
                    [i["id"], i[iteration_data[0]]]
                    if iteration_data[0] == "station_id"
                    else i[iteration_data[0]]
                )

    if value[0] and ("All" not in value[0]):
        for i in stations:
            if (
                i[key] in value[0]
                and len(i[iteration_data[0]]) > 0
                and i[iteration_data[0]] not in data_to_send
            ):
                data_to_send.append(
                    [i["id"], i[iteration_data[0]]]
                    if iteration_data[0] == "station_id"
                    else i[iteration_data[0]]
                )
    if not value[0] and key == "shops":
        for i in stations:
            if (
                i["operation_region"] not in data_to_send
                and len(i[iteration_data[0]]) > 0
            ):
                data_to_send.append(
                    [i["id"], i[iteration_data[0]]]
                    if iteration_data[0] == "station_id"
                    else i[iteration_data[0]]
                )

    natural_sort_rejex_pattern = re.compile("([0-9]+)")

    def natural_sort_key(data_string):
        if isinstance(data_string, list):
            return [
                int(text) if text.isdigit() else text.lower()
                for text in re.split(
                    natural_sort_rejex_pattern, data_string[1]
                )
            ]
        return [
            int(text) if text.isdigit() else text.lower()
            for text in re.split(natural_sort_rejex_pattern, data_string)
        ]

    def data_len(data_string):
        if isinstance(data_string, list):
            return len(data_string[1])
        return len(data_string)

    data_to_send.sort(key=natural_sort_key)
    if data_to_send and isinstance(data_to_send[0], list):
        data_to_send.sort(key=data_len)
    return data_to_send


# This view is used to dynamically render the checkboxes on
# add promotion/ edit promotion pages.


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
def checkbox_data_for_add_promotions(request):
    """checkboxes to select stations"""
    if "checkbox_for_assign_promotions" in cache:
        # get results from cache
        stations = cache.get("checkbox_for_assign_promotions")
    else:
        stations = Stations.objects.filter(deleted=NO).values()
        for station in stations:
            station_services = StationServices.objects.filter(
                station_id_id=station["id"],
                deleted=NO,
            ).values("service_id__service_name")
            station["services"] = station_services
        cache.set(
            "checkbox_for_assign_promotions", stations, timeout=(60 * 60 * 12)
        )
    data_to_send = []
    post_data = json.loads(request.POST["getdata"])
    iteration_data = json.loads(request.POST["data_to_fetch"])
    for key, value in post_data.items():
        data_to_send += post_data_op(stations, iteration_data, key, value)
    return JsonResponse({"status": 1, "message": "ok", "data": data_to_send})


def response_return(filtered_data):
    """response print"""
    response_op_promotion = export_promotion_data(
        filtered_data["filtered_table_for_export"]
    )
    if response_op_promotion:
        response_op_promotion.set_cookie(
            "exported_data_cookie_condition", EXPORT_TRUE, max_age=8
        )
    return response_op_promotion


def response_error_return():
    """response error print"""
    promotions_error_records = BulkUploadErrorMessages.objects.filter(
        uploaded_for="promotions", ready_to_export=YES
    )

    if promotions_error_records.first():
        errors = string_to_array_converter(
            promotions_error_records.first().errors
        )
        promotions_errors = errors[0]["errors"]
        promotiont_assign_errors = errors[1]["errors"]
        error_response_promotions = export_data_function_multi_tabs(
            [promotions_errors, promotiont_assign_errors],
            [
                [UNQUIE_RETAILBAR_CODE, "Error"],
                [UNQUIE_RETAILBAR_CODE, "Error"],
            ],
            [
                [UNQUIE_RETAILBAR_CODE, "Error"],
                [UNQUIE_RETAILBAR_CODE, "Error"],
            ],
            ["Promotions Tab", "Promotion Assign Tab"],
        )
        promotions_error_records.update(ready_to_export=NO)
        if error_response_promotions:
            error_response_promotions.set_cookie(
                "exported_data_cookie_condition", EXPORT_TRUE, max_age=8
            )
            return error_response_promotions
    return None


def bulk_upload_progress_percentage():
    """bulk percentage"""
    promotion_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="promotions", uploading_status="uploading"
    )
    bulk_upload_running = False
    percentage = 0
    if promotion_bulk_upload_progress.first():
        bulk_upload_running = True
        percentage = (
            int(promotion_bulk_upload_progress.first().total_rows_count)
            * int(promotion_bulk_upload_progress.first().uploaded_rows_count)
            / 100
        )
        if percentage > 100:
            percentage = 85
    return [bulk_upload_running, percentage]


# This view returns the list of promotions.
def cache_check_promotions():
    """promotion cache view"""
    if "cache_promotions" in cache:
        # get results from cache
        promotions = cache.get("cache_promotions")
    else:
        promotions = (
            Promotions.objects.filter(deleted=NO)
            .order_by("-updated_date")
            .values()
        )
        cache.set("cache_promotions", promotions, timeout=CACHE_TTL)
    return promotions


def filter_fun(*args):
    """promotion filter"""
    (
        request,
        page_num,
        promotions,
        search,
        status,
        do_export,
        do_errors_export,
    ) = args
    filtered_data = pagination_and_filter_func(
        page_num,
        promotions,
        [
            {
                "search": search,
                "search_array": [
                    "product__icontains",
                    "promotion_title__icontains",
                ],
            },
            {"status__exact": status},
        ],
        "promotion",
    )
    filtered_promotions = filtered_data["filtered_table"]
    if do_export == YES:
        return response_return(filtered_data)
    if do_errors_export == YES:
        response = response_error_return()
        return response

    url_data = filter_url(
        request.user.role_id.access_content.all(), PROMOTIONS_CONST
    )
    return [filtered_promotions, filtered_data, url_data]


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=PROMOTIONS_CONST)
def promotions_list(request):
    """promotion listing view"""
    try:
        query_params_str = ""
        for q_param in request.GET:
            if len(query_params_str) == 0:
                query_params_str = f"?{q_param}={request.GET.get(q_param)}"
            else:
                query_params_str += f"&{q_param}={request.GET.get(q_param)}"

        # Database call to promotions.
        promotions = cache_check_promotions()

        dashboard_data_days_limit = int(
            filter_function_for_base_configuration(
                DASHBOARD_DATA_DAYS_LIMIT, DEFAULT_DASHBOARD_DATA_DAYS_LIMIT
            )
        )
        from_date = request.GET.get("from_date", "")
        to_date = request.GET.get("to_date", "")

        if (
            to_date != ""
            and (
                date_formater_for_frontend_date(to_date)
                - (
                    date_formater_for_frontend_date(from_date)
                    if date_formater_for_frontend_date(from_date)
                    else date_formater_for_frontend_date(to_date)
                    - timedelta(days=dashboard_data_days_limit)
                )
            ).days
            < 0
        ):
            to_date = ""
        current_and_from_date_difference = 0
        if from_date:
            current_and_from_date_difference = (
                timezone.now() - date_formater_for_frontend_date(from_date)
            ).days

        maximum_to_date = 0

        to_date_and_from_date_diffrence = (
            current_and_from_date_difference
            if to_date == ""
            else (
                date_formater_for_frontend_date(to_date)
                - (
                    date_formater_for_frontend_date(from_date)
                    if date_formater_for_frontend_date(from_date)
                    else date_formater_for_frontend_date(to_date)
                    - timedelta(days=dashboard_data_days_limit)
                )
            ).days
        )
        if to_date_and_from_date_diffrence > dashboard_data_days_limit:
            to_date = (
                date_formater_for_frontend_date(from_date)
                + timedelta(days=dashboard_data_days_limit)
            ).strftime("%d/%m/%Y")
            maximum_to_date = (
                abs(
                    (
                        timezone.now()
                        - date_formater_for_frontend_date(from_date)
                    ).days
                )
                - dashboard_data_days_limit
            )
        elif (
            to_date != ""
            and current_and_from_date_difference > dashboard_data_days_limit
        ):
            maximum_to_date = (
                abs(
                    (
                        timezone.now()
                        - date_formater_for_frontend_date(from_date)
                    ).days
                )
                - dashboard_data_days_limit
            )

        # Declaration of all query params that helps in filtering
        # data and pagination.
        page_num = request.GET.get("page", 1)
        status = request.GET.get("status", None)
        search = request.GET.get("search", "")
        date_difference = 0
        # from_date = request.GET.get("from_date", "")
        # to_date = request.GET.get("to_date", "")
        order_by_retail_barcode = request.GET.get(
            "order_by_retail_barcode", None
        )
        order_by_start_date = request.GET.get("order_by_start_date", None)
        order_by_end_date = request.GET.get("order_by_end_date", None)
        do_export = request.GET.get("export", None)
        do_errors_export = request.GET.get("export_errors", None)
        updated_url = ""
        ordered_promotions = order_by_function(
            promotions,
            [
                {
                    "retail_barcode": [
                        "order_by_retail_barcode",
                        order_by_retail_barcode,
                    ]
                },
                {"start_date": ["order_by_start_date", order_by_start_date]},
                {"end_date": ["order_by_end_date", order_by_end_date]},
            ],
        )
        promotions = ordered_promotions["ordered_table"]
        if from_date:
            promotions = promotions.filter(
                start_date__gte=date_formater_for_frontend_date(from_date)
            )
            updated_url += f"&from_date={from_date}"
        if to_date:
            formatted_to_date = date_formater_for_frontend_date(to_date)
            if from_date:
                date_difference = date_difference_function(
                    from_date, formatted_to_date
                )
            promotions = promotions.filter(
                start_date__lte=formatted_to_date + timedelta(days=1)
            )
            updated_url += f"&to_date=" if to_date>from_date else f"&to_date={to_date}"

        search = search_validator(search)
        # Here pagination_and_filter_func() is the common function to provide
        # filteration and pagination.
        filtered_response = filter_fun(
            request,
            page_num,
            promotions,
            search,
            status,
            do_export,
            do_errors_export,
        )
        if not isinstance(filtered_response, list):
            return filtered_response

        (bulk_upload_running, percentage) = bulk_upload_progress_percentage()

        errors_export_ready_list = False
        promotions_error_records_list = BulkUploadErrorMessages.objects.filter(
            uploaded_for="promotions",
            ready_to_export=YES,
        )
        if promotions_error_records_list.first():
            errors = string_to_array_converter(
                promotions_error_records_list.first().errors
            )
            if len(errors[0]["errors"]) > 0 or len(errors[1]["errors"]) > 0:
                errors_export_ready_list = True

        time_difference = 0
        if from_date:
            time_difference = (
                abs(
                    (
                        date_formater_for_frontend_date(from_date)
                        - timezone.now()
                    ).days
                )
                - 1
            )
        # Response to the request
        return render(
            request,
            "promotions/promotions_list.html",
            context={
                "to_date_difference_from_current_date": date_difference,
                "promotions_available": bool(
                    len(filtered_response[FILETERED_PROMOTIONS]) != 0
                ),
                "promotions": filtered_response[FILETERED_PROMOTIONS],
                "bulk_upload_running": bulk_upload_running,
                "errors_export_ready": errors_export_ready_list,
                "percentage": percentage,
                "data_count": filtered_response[FILETERED_DATA]["data_count"],
                "first_data_number": filtered_response[FILETERED_DATA][
                    "first_record_number"
                ],
                "last_data_number": filtered_response[FILETERED_DATA][
                    "last_record_number"
                ],
                "status_list": ["Active", "All", "Inactive"],
                "prev_start_date": order_by_start_date,
                "prev_end_date": order_by_end_date,
                "prev_retail_barcode": order_by_retail_barcode,
                "prev_from_date": from_date,
                "prev_to_date": to_date,
                "prev_search": search,
                "prev_status": status,
                "update_url_param": filtered_response[FILETERED_DATA]["url"]
                + updated_url
                + ordered_promotions["url"],
                "pagination_num_list": filtered_response[FILETERED_DATA][
                    "number_list"
                ],
                "current_page": int(page_num),
                "prev": filtered_response[FILETERED_DATA]["prev_page"],
                "next": filtered_response[FILETERED_DATA]["next_page"],
                "data": filtered_response[URL_DATA],
                "maximum_to_date": maximum_to_date,
                "time_difference": time_difference,
                "query_params_str": query_params_str,
                "dashboard_data_days_limit": dashboard_data_days_limit,
            },
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


# This view is used to change the status of the promotion
# (eg., from Active -> Inactive).
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def change_status_view(request):
    """change promotion status view"""
    try:
        # Post request to make database queries securely.
        if request.method == "POST":
            # Decoding JSON data from frontend
            post_data_from_front_end = json.loads(
                request.POST["getdata"],
                object_hook=lambda d: SimpleNamespace(**d),
            )
            old_data = audit_data_formatter(
                PROMOTIONS_CONST, post_data_from_front_end.promotion_id
            )
            promotion = Promotions.objects.filter(
                id=post_data_from_front_end.promotion_id
            ).first()
            # Status update operation.
            Promotions.objects.filter(
                id__exact=int(post_data_from_front_end.promotion_id)
            ).update(
                status=post_data_from_front_end.status,
                updated_date=timezone.localtime(timezone.now()),
            )
            new_data = audit_data_formatter(
                PROMOTIONS_CONST, post_data_from_front_end.promotion_id
            )
            if old_data != new_data:
                add_audit_data(
                    request.user,
                    (promotion.unique_code + ", " + promotion.promotion_title),
                    (
                        PROMOTIONS_CONST
                        + "-"
                        + str(post_data_from_front_end.promotion_id)
                    ),
                    AUDIT_UPDATE_CONSTANT,
                    PROMOTIONS_CONST,
                    new_data,
                    old_data,
                )
            remove_promotions_cached_data()
        return JsonResponse({"status": 1, "message": "ok"})
    except COMMON_ERRORS:
        return JSON_ERROR_OBJECT


# This view helps to return details about particular promotion.
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=PROMOTIONS_CONST)
def view_promotions(request, promotion_pk):
    """view promotion details view"""
    try:
        query_params_str_promotions = ""
        for q_param in request.GET:
            if len(query_params_str_promotions) == 0:
                query_params_str_promotions = (
                    f"?{q_param}={request.GET.get(q_param)}"
                )
            else:
                query_params_str_promotions += (
                    f"&{q_param}={request.GET.get(q_param)}"
                )
        # Database call to fetch all services from configurations.
        shops_from_configurations = ServiceConfiguration.objects.filter(
            ~Q(service_type="Amenity")
        ).values("id", "service_name", "image_path", "service_type")

        # Fetching the particular promotion from database
        promotions = Promotions.objects.filter(id__exact=promotion_pk).values()
        promotion = promotions.first()

        ops_regions = list(
            set(
                PromotionsAvailableOn.objects.filter(
                    promotion_id_id=promotion["id"], deleted=NO
                ).values_list("operation_region", flat=True)
            )
        )
        regions = list(
            set(
                PromotionsAvailableOn.objects.filter(
                    promotion_id_id=promotion["id"], deleted=NO
                ).values_list("region", flat=True)
            )
        )
        area = list(
            set(
                PromotionsAvailableOn.objects.filter(
                    promotion_id_id=promotion["id"], deleted=NO
                ).values_list("area", flat=True)
            )
        )
        stations = list(
            set(
                PromotionsAvailableOn.objects.filter(
                    promotion_id_id=promotion["id"], deleted=NO
                ).values_list("station_id__station_id", flat=True)
            )
        )
        shops = []
        # Converting string into an array
        if promotion["shop_ids"]:
            decoder = StringIO(promotion["shop_ids"])
            shop_ids = json.load(decoder)

            for shop in shops_from_configurations:
                if (
                    str(shop["service_name"]) in shop_ids
                    or str(shop["id"]) in shop_ids
                ):
                    shops.append(shop["service_name"])
        promotion["stations"] = stations
        promotion["operation_regions"] = ops_regions
        promotion["regions"] = regions
        promotion["area"] = area
        promotion["shops"] = shops
        if Promotions.objects.filter(id__exact=promotion_pk).first().image:
            promotion["images"] = [
                Promotions.objects.filter(id__exact=promotion_pk)
                .first()
                .get_promotion_image()
            ]
        else:
            promotion["images"] = []
        url_data = filter_url(
            request.user.role_id.access_content.all(), PROMOTIONS_CONST
        )
        # response to request
        return render(
            request,
            "promotions/view_promotions.html",
            context={
                "promotion": promotion,
                "data": url_data,
                "query_params_str": query_params_str_promotions,
            },
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


def edit_database_update(
    request, shops_from_configurations, promotion, promotion_pk
):
    """edit database update"""
    if request.method == "POST":
        try:
            old_data = audit_data_formatter(PROMOTIONS_CONST, promotion_pk)
            # Fetching and decoding JSON data from frontend
            post_data_from_front_end = json.loads(
                request.POST["getdata"],
                object_hook=lambda d: SimpleNamespace(**d),
            )

            # Converting array into string to store into the database.
            string_converter = StringIO()
            shops_array = []
            if "All" in post_data_from_front_end.shop:
                for shop in shops_from_configurations:
                    shops_array.append(shop["service_name"])
                json.dump(shops_array, string_converter)
            else:
                json.dump(post_data_from_front_end.shop, string_converter)
            shops_edit = string_converter.getvalue()

            start_date_edit = date_formater_for_frontend_date(
                post_data_from_front_end.start_date
            )

            end_date_edit = end_date_formater_for_frontend_date(
                post_data_from_front_end.end_date
            )
            image_data_promotions = None
            if len(post_data_from_front_end.images) > 0:
                if post_data_from_front_end.images[0] in promotion["images"]:
                    if len(post_data_from_front_end.images) > 1:
                        image_data_promotions = image_converter(
                            post_data_from_front_end.images[1]
                        )
                else:
                    image_data_promotions = image_converter(
                        post_data_from_front_end.images[0]
                    )
            else:
                if Promotions.objects.filter(id=promotion_pk).first().image:
                    Promotions.objects.filter(
                        id=promotion_pk
                    ).first().image.delete()
                    Promotions.objects.filter(id=promotion_pk).update(
                        image=None
                    )
            if image_data_promotions:
                if Promotions.objects.filter(id=promotion_pk).first().image:
                    Promotions.objects.filter(
                        id=promotion_pk
                    ).first().image.delete()
                if not (
                    image_data_promotions[2] > 700
                    or image_data_promotions[3] > 1400
                    or image_data_promotions[2] < 400
                    or image_data_promotions[3] < 700
                ):
                    return JsonResponse(
                        {
                            "status": False,
                            "message": "Image with improper size is provided.",
                            "url": reverse("station_list"),
                        }
                    )
                image_update = optimize_image(
                    image_data_promotions[
                        IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN
                    ],
                    post_data_from_front_end.promotion_title
                    + randon_string_generator()
                    + "."
                    + image_data_promotions[1],
                    PROMOTION_IMAGE,
                )
                promotion_data = get_object_or_404(Promotions, id=promotion_pk)
                promotion_data.image = image_update
                promotion_data.save()
            # Update  promotion details.
            update_single_promotion(
                post_data_from_front_end,
                request.user,
                promotion["station_ids"],
                promotion_pk,
                start_date_edit,
                end_date_edit,
                shops_edit,
                old_data,
            )
            remove_promotions_cached_data()
            return JsonResponse(
                {
                    "status": 1,
                    "message": "ok",
                    "url": reverse("promotions_list"),
                }
            )
        except (KeyError, AttributeError, DatabaseError, DataError) as error:
            (
                exception_type_update,
                exception_object_update,
                exception_traceback_update,
            ) = sys.exc_info()
            filename_update = (
                exception_traceback_update.tb_frame.f_code.co_filename
            )
            line_number_update = exception_traceback_update.tb_lineno
            print(exception_object_update, "**exception_object")
            print("Exception type: ", exception_type_update)
            print("File name: ", filename_update)
            print("Line number: ", line_number_update)
            print("Error ->", str(error))
            print(f"Error time {timezone.localtime(timezone.now())}")
            return JsonResponse(
                {
                    "status": 0,
                    # "message": str(error),
                    "message": "Error occured while updating database",
                    "url": reverse("promotions_list"),
                }
            )
    return None


# This view helps to edit the particular promotion.
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=PROMOTIONS_CONST)
def edit_promotions(request, promotion_pk):
    """edit promotion view"""
    try:
        query_params_edit_promotions = ""
        for q_param in request.GET:
            if len(query_params_edit_promotions) == 0:
                query_params_edit_promotions = (
                    f"?{q_param}={request.GET.get(q_param)}"
                )
            else:
                query_params_edit_promotions += (
                    f"&{q_param}={request.GET.get(q_param)}"
                )

        # Database call to fetch all services from configurations.
        shops_from_configurations = ServiceConfiguration.objects.filter(
            ~Q(service_type="Amenity")
        ).values("id", "service_name", "image_path", "service_type")

        # Fetching particular promotion for updation.
        promotions = Promotions.objects.filter(id__exact=promotion_pk).values(
            "id",
            "unique_code",
            "retail_barcode",
            "product",
            "promotion_title",
            "m_code",
            "status",
            "available_for",
            "offer_type",
            "start_date",
            "end_date",
            "price",
            "quantity",
            "londis_code",
            "budgen_code",
            "shop_ids",
            "offer_details",
            "terms_and_conditions",
        )
        promotion = promotions.first()
        ops_regions = list(
            set(
                PromotionsAvailableOn.objects.filter(
                    promotion_id_id=promotion["id"], deleted=NO
                ).values_list("operation_region", flat=True)
            )
        )
        regions = list(
            set(
                PromotionsAvailableOn.objects.filter(
                    promotion_id_id=promotion["id"], deleted=NO
                ).values_list("region", flat=True)
            )
        )
        area = list(
            set(
                PromotionsAvailableOn.objects.filter(
                    promotion_id_id=promotion["id"], deleted=NO
                ).values_list("area", flat=True)
            )
        )
        stations = list(
            set(
                PromotionsAvailableOn.objects.filter(
                    promotion_id_id=promotion["id"], deleted=NO
                ).values_list("station_id_id", flat=True)
            )
        )
        station_ids = list(
            set(
                PromotionsAvailableOn.objects.filter(
                    promotion_id_id=promotion["id"], deleted=NO
                ).values_list("station_id__station_id", flat=True)
            )
        )
        shops = []
        start_date = promotion["start_date"]
        end_date = promotion["end_date"]
        promotion["start_date"] = (
            start_date.strftime("%d")
            + "/"
            + start_date.strftime("%m")
            + "/"
            + start_date.strftime("%Y")
        )
        promotion["end_date"] = (
            end_date.strftime("%d")
            + "/"
            + end_date.strftime("%m")
            + "/"
            + end_date.strftime("%Y")
        )

        # Converting string into an array.
        input_output = StringIO(promotion["shop_ids"])
        shop_ids = json.load(input_output) if promotion["shop_ids"] else []
        for shop in shops_from_configurations:
            if (
                str(shop["service_name"]) in shop_ids
                or str(shop["id"]) in shop_ids
            ):
                shops.append(shop["service_name"])

        promotion["stations"] = stations
        promotion["station_ids"] = station_ids
        promotion["operation_regions"] = ops_regions
        promotion["regions"] = regions
        promotion["area"] = area
        promotion["shop"] = shops
        if Promotions.objects.filter(id__exact=promotion_pk).first().image:
            promotion["images"] = [
                Promotions.objects.filter(id__exact=promotion_pk)
                .first()
                .get_promotion_image()
            ]
        else:
            promotion["images"] = []

        shops_list = []
        for i in shops_from_configurations:
            shops_list.append([i["id"], i["service_name"]])
        shops_list.sort(key=lambda shop: shop[1].lower())
        # Dumping data so that we can handle data in javascript
        json_string = json.dumps(promotion)

        promotion_edit_response = edit_database_update(
            request, shops_from_configurations, promotion, promotion_pk
        )
        if promotion_edit_response:
            return promotion_edit_response
        url_data = filter_url(
            request.user.role_id.access_content.all(), PROMOTIONS_CONST
        )
        # Post request to make database operation securely

        # Get response
        return render(
            request,
            "promotions/add_promotions.html",
            context={
                "edit_page": "Yes",
                "available_for_list": return_available_for_values(),
                "status_list": return_status_list(),
                "promotion": promotion,
                "shops": shops_list,
                "offer_types": return_offer_type_values(),
                "ops_regions": return_ops_regions(),
                "tsjson": json_string,
                "data": url_data,
                "query_params_str": query_params_edit_promotions,
                "all_stations_from_backend": all_stations_qs(),
                "stations_master_data": return_stations_master_data_for_loyalties_and_promotions(),
            },
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


# This view will delete particular promotion
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=PROMOTIONS_CONST)
def delete_promotions(request, promotion_pk):
    """delete promotion view"""
    try:
        # we have used soft delete technique to delete the records
        # fetching the promotion with the help of
        # 'promotion_pk' for deletion of promotion
        promotion = Promotions.objects.filter(id=promotion_pk).first()
        Promotions.objects.filter(id=promotion_pk).update(
            deleted=YES,
            updated_date=timezone.localtime(timezone.now()),
            updated_by=request.user.full_name,
        )

        # deleting dependencies
        PromotionsAvailableOn.objects.filter(
            promotion_id_id=promotion_pk
        ).update(
            deleted=YES,
            updated_date=timezone.localtime(timezone.now()),
            updated_by=request.user.full_name,
        )
        prev_audit_data = AuditTrail.objects.filter(
            data_db_id=f"{PROMOTIONS_CONST}-{promotion_pk}"
        ).last()
        if prev_audit_data and prev_audit_data.new_data:
            prev_audit_data = prev_audit_data.new_data
            add_audit_data(
                request.user,
                (promotion.unique_code + ", " + promotion.promotion_title),
                f"{PROMOTIONS_CONST}-{promotion_pk}",
                AUDIT_DELETE_CONSTANT,
                PROMOTIONS_CONST,
                None,
                prev_audit_data,
            )

        remove_promotions_cached_data()
        # Redirecting user on successful deletion of record
        return redirect("promotions_list")
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


class RemoveCachedOnPromotionExpiry(APIView):
    """remove cache on promotion expiry"""

    @classmethod
    def post(cls, cron_job_request):
        try:
            secret_key_azure = cron_job_request.data.get("secret_key", None)
            if secret_key_azure is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Secret key not provided.",
                    }
                )
            if not handler.verify(
                secret_key_azure, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
            ):
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Secret key is not valid.",
                    }
                )
            expired_promotions = Promotions.objects.filter(
                deleted=NO,
                status=ACTIVE,
                end_date__lt=timezone.localtime(timezone.now()),
            )
            if expired_promotions.first():
                remove_promotions_cached_data()
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Cron job initiated.",
                }
            )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT
