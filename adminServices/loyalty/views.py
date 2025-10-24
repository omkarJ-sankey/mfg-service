"""loyalty views"""
# Date - 03/01/2021

# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on views(backend logic)
#                       related to loyalty.
#   Name            - Loyalty Views
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 04/19/2025

# imports required to create views
import json
from types import SimpleNamespace
from io import StringIO
from datetime import timedelta
import traceback

from django.db import DataError, DatabaseError
from django.db.models import Q
from django.shortcuts import redirect, render
from django.http import HttpResponse, JsonResponse
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from adminServices.loyalty.serializers import AddLoyaltyRequestSerializer, EditLoyaltyRequestSerializer
from adminServices.loyalty.services import add_loyalty_service, update_single_loyalty_service
from adminServices.stations.stations_helper_functions import remove_stations_cached_data
# pylint:disable=import-error
from sharedServices.decorators import allowed_users, authenticated_user
from sharedServices.common import (
    api_response,
    date_formater_for_frontend_date,
    end_date_formater_for_frontend_date,
    filter_url,
    order_by_function,
    pagination_and_filter_func,
    filter_function_for_base_configuration,
    date_difference_function,
    search_validator,
)
from sharedServices.common_audit_trail_functions import (
    add_audit_data,
    audit_data_formatter,
)
from sharedServices.constants import (
    LOYALTY_CONST,
    YES,
    EXPORT_TRUE,
    AUDIT_UPDATE_CONSTANT,
    AUDIT_DELETE_CONSTANT,
    COMMON_ERRORS,
    ERROR_TEMPLATE_URL,
    JSON_ERROR_OBJECT,
    DEFAULT_NOTIFICATION_IMAGE,
    PURCHASED,
    BURNED,
    COSTA_COFFEE,
    ACTIVE,
    NO,
    ConstantMessage
)

from sharedServices.models import (
    Loyalty,
    LoyaltyAvailableOn,
    PushNotifications,
    AuditTrail,
    UserLoyaltyTransactions,
)
from adminServices.promotions.promotions_helper_functions import (
    all_stations_qs,
    return_ops_regions,
    return_status_list,
    return_available_for_values,
)
from .loyalty_helper_functions import (
    remove_loyalties_cached_data,
    return_bar_code_std_list,
    return_loyalty_category_list,
    return_offer_type_list,
    export_loyalty_data,
    return_loyalty_list,
    return_services_from_configurations,
    return_shops_from_configurations,
    return_amenities_from_configurations,
    return_loyalty_data,
    return_stations_master_data_for_loyalties_and_promotions,
)

from ..dashboard.app_level_constants import (
    DASHBOARD_DATA_DAYS_LIMIT,
    DEFAULT_DASHBOARD_DATA_DAYS_LIMIT,
)
from .db_operators import create_single_loyalty, update_single_loyalty
from rest_framework import status
from rest_framework.views import APIView  

# pylint:enable=import-error
CACHE_TTL = getattr(settings, "CACHE_TTL", DEFAULT_TIMEOUT)


@authenticated_user
@allowed_users(section=LOYALTY_CONST)
def loyalties(request):
    """loyalty listing view"""
    try:
        query_params_str = ""
        for q_param in request.GET:
            if len(query_params_str) == 0:
                query_params_str = f"?{q_param}={request.GET.get(q_param)}"
            else:
                query_params_str += f"&{q_param}={request.GET.get(q_param)}"

        dashboard_data_days_limit = int(
            filter_function_for_base_configuration(
                DASHBOARD_DATA_DAYS_LIMIT, DEFAULT_DASHBOARD_DATA_DAYS_LIMIT
            )
        )

        from_date = request.GET.get("from_date", "")
        date_difference = 0
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

        # Declaration of all query params that helps in
        # filtering data and pagination.
        page_num = request.GET.get("page", 1)
        status = request.GET.get("status", None)
        search = request.GET.get("search", "")
        search = search_validator(search)
        order_by_start_date = request.GET.get("order_by_start_date", None)
        order_by_end_date = request.GET.get("order_by_end_date", None)
        do_export = request.GET.get("export", None)
        loyalties_available = True
        # Here pagination_and_filter_func() is the common function to provide
        # filteration and pagination.

        # Database call to loyalties.
        loyalty_list = return_loyalty_list()
        updated_url = ""

        ordered_loyalties = order_by_function(
            loyalty_list,
            [
                {
                    "valid_from_date": [
                        "order_by_start_date",
                        order_by_start_date,
                    ]
                },
                {"valid_to_date": ["order_by_end_date", order_by_end_date]},
            ],
        )
        loyalty_list = ordered_loyalties["ordered_table"]
        if from_date:
            loyalty_list = loyalty_list.filter(
                valid_from_date__gte=date_formater_for_frontend_date(from_date)
            )
            updated_url += f"&from_date={from_date}"
        if to_date:
            formatted_to_date = date_formater_for_frontend_date(to_date)
            loyalty_list = loyalty_list.filter(
                valid_from_date__lte=formatted_to_date
            )
            updated_url += "&to_date=" if to_date>from_date else f"&to_date={to_date}"
            if from_date:
                date_difference = date_difference_function(
                    from_date, formatted_to_date
                )
        filtered_data = pagination_and_filter_func(
            page_num,
            loyalty_list,
            [
                {
                    "search": search,
                    "search_array": [
                        "loyalty_title__icontains",
                    ],
                },
                {"status__exact": status},
            ],
            "loyalty",
        )
        filtered_loyalties = filtered_data["filtered_table"]
        if len(filtered_loyalties) == 0:
            loyalties_available = False
        if not search:
            search = ""
        if not from_date:
            from_date = ""
        if not to_date:
            to_date = ""
        url_data = filter_url(
            request.user.role_id.access_content.all(), LOYALTY_CONST
        )

        if do_export == YES:
            response = export_loyalty_data(filtered_data)
            if response:
                response.set_cookie(
                    "exported_data_cookie_condition", EXPORT_TRUE,
                )
                return response

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
            "loyalty/loyalty_list.html",
            context={
                "to_date_difference_from_current_date": date_difference,
                "loyalties_available": loyalties_available,
                "loyalties": filtered_loyalties,
                "data_count": filtered_data["data_count"],
                "first_data_number": filtered_data["first_record_number"],
                "last_data_number": filtered_data["last_record_number"],
                "status_list": ["Active", "All", "Inactive"],
                "prev_start_date": order_by_start_date,
                "prev_end_date": order_by_end_date,
                "prev_from_date": from_date,
                "prev_to_date": to_date,
                "prev_search": search,
                "prev_status": status,
                "update_url_param": filtered_data["url"]
                + updated_url
                + ordered_loyalties["url"],
                "pagination_num_list": filtered_data["number_list"],
                "current_page": int(page_num),
                "prev": filtered_data["prev_page"],
                "next": filtered_data["next_page"],
                "data": url_data,
                "query_params_str": query_params_str,
                "maximum_to_date": maximum_to_date,
                "time_difference": time_difference,
                "dashboard_data_days_limit": dashboard_data_days_limit,
            },
        )
    except COMMON_ERRORS:
        traceback.print_exc()
        return render(request, ERROR_TEMPLATE_URL)


def return_redeem_types():
    """this function returns reedem types"""
    return ["Count", "Amount", "kWh"]


def return_cycle_durations():
    """this function returns cycle duration for loyalty"""
    return ["3", "6"]


# This view is used to change the status of the loyalty
# (eg., from Active -> Inactive).


@authenticated_user
def change_loyalty_status_view(request):
    """change loyalty status view"""
    try:
        # Post request to make database queries securely.
        if request.method == "POST":
            # Decoding JSON data from frontend
            post_data_from_front_end = json.loads(
                request.POST["getdata"],
                object_hook=lambda d: SimpleNamespace(**d),
            )

            # Status update operation.
            old_data = audit_data_formatter(
                LOYALTY_CONST, int(post_data_from_front_end.loyalty_id)
            )
            loyalty = Loyalty.objects.filter(
                id=int(post_data_from_front_end.loyalty_id)
            ).first()
            costa_loyalty_exists = Loyalty.objects.filter(
                ~Q(id=int(post_data_from_front_end.loyalty_id)),
                loyalty_type=COSTA_COFFEE,
                status=ACTIVE,
                deleted=NO,
            ).first()
            if post_data_from_front_end.status != "Active" or loyalty.loyalty_type != COSTA_COFFEE or (
                loyalty.loyalty_type == COSTA_COFFEE
                and post_data_from_front_end.status == "Active"
                and costa_loyalty_exists is None
            ):
                Loyalty.objects.filter(
                    id__exact=int(post_data_from_front_end.loyalty_id)
                ).update(
                    status=post_data_from_front_end.status,
                    updated_date=timezone.localtime(timezone.now()),
                )
                new_data = audit_data_formatter(
                    LOYALTY_CONST, int(post_data_from_front_end.loyalty_id)
                )
                if old_data != new_data:
                    add_audit_data(
                        request.user,
                        (loyalty.unique_code + ", " + loyalty.loyalty_title),
                        (
                            LOYALTY_CONST
                            + "_"
                            + str(post_data_from_front_end.loyalty_id)
                        ),
                        AUDIT_UPDATE_CONSTANT,
                        LOYALTY_CONST,
                        new_data,
                        old_data,
                    )
                remove_loyalties_cached_data()
                response = {"status": 1, "message": "Succesfully updated status of loyalty!!"}
            else:
                response = {"status": 0, "message": "Another costa loyalty is already active!"}
        return HttpResponse(
            json.dumps(response), content_type="application/json"
        )
    except COMMON_ERRORS:
        return JSON_ERROR_OBJECT


def return_shop_and_amenity_list():
    """this function returns list of shops and amenities"""
    shops_list = [
        [i["id"], i["service_name"]]
        for i in return_shops_from_configurations()
    ]
    amenities_list = [
        [i["id"], i["service_name"]]
        for i in return_amenities_from_configurations()
    ]
    return [shops_list, amenities_list]


def return_loyalty_types():
    """loyalty list"""
    return ["Regular", "Costa Coffee", "Free"]


# This view is used to insert loyalties in database
@authenticated_user
@allowed_users(section=LOYALTY_CONST)
def add_loyalties(request):
    """add loyalty view"""
    try:
        # Database call to fetch all services from configurations.
        query_params_str = ""
        for q_param in request.GET:
            if len(query_params_str) == 0:
                query_params_str = f"?{q_param}={request.GET.get(q_param)}"
            else:
                query_params_str += f"&{q_param}={request.GET.get(q_param)}"

        # shops and services fetched in case if we need in future
        shops_list, amenities_list = return_shop_and_amenity_list()
        shops_list.sort(key=lambda shop: shop[1].lower())
        amenities_list.sort(key=lambda shop: shop[1].lower())
        # This condition makes sure that the request
        # is POST so that we can safely insert data in tables.
        if request.method == "POST":
            try:
                # Decoding post data (the data is in form of JSON)
                post_data_from_front_end = json.loads(
                    request.POST["getdata"],
                    object_hook=lambda d: SimpleNamespace(**d),
                )
                # This logic helps us to store array of shop ids as a
                # string in a database
                string_converter = StringIO()
                json.dump(post_data_from_front_end.shop, string_converter)
                shops = string_converter.getvalue()

                start_date = date_formater_for_frontend_date(
                    post_data_from_front_end.start_date
                )
                end_date = end_date_formater_for_frontend_date(
                    post_data_from_front_end.end_date
                )
                create_response = create_single_loyalty(
                    post_data_from_front_end,
                    shops,
                    start_date,
                    end_date,
                    request.user,
                )
                if create_response:
                    # Dumping data so that we can handle data in javascript
                    return create_response
                remove_loyalties_cached_data()

                # sending response to the request
                response = {
                    "status": 1,
                    "message": "ok",
                    "url": reverse("loyalties_list"),
                }
                # Dumping data so that we can handle data in javascript
                return JsonResponse(response)
            except COMMON_ERRORS as error:
                print(f'While adding loyalty error occured as-> {str(error)}')
                response = {
                    "status": 0,
                    # "message": str(error),
                    "message": "Issue faced while adding loyalty",
                    "url": reverse("loyalties_list"),
                }
                return JsonResponse(response)
        url_data = filter_url(
            request.user.role_id.access_content.all(), LOYALTY_CONST
        )
        remove_stations_cached_data()
        return render(
            request,
            "loyalty/add_loyalty.html",
            context={
                "edit_page": "No",
                "loyalty_category_list": return_loyalty_category_list(),
                "offer_type_list": return_offer_type_list(),
                "bar_code_std_list": return_bar_code_std_list(),
                "status_list": return_status_list(),
                "occurance_statuses": [YES, NO],
                "shops": shops_list,
                "amenities": amenities_list,
                "data": url_data,
                "query_params_str": query_params_str,
                "redeem_types": return_redeem_types(),
                "cycle_durations": return_cycle_durations(),
                "stations_master_data": return_stations_master_data_for_loyalties_and_promotions(),
                "loyalty_types": return_loyalty_types(),
                "notification_redirect_screens": ["Promotions", "Loyalty", "Loyalty Info"],
                "default_notification_image": DEFAULT_NOTIFICATION_IMAGE,
            },
        )
    except COMMON_ERRORS:
        traceback.print_exc()
        return render(request, ERROR_TEMPLATE_URL)


# This view helps to return details about particular loyalty.
@authenticated_user
@allowed_users(section=LOYALTY_CONST)
def view_loyalties(request, loyalty_pk):
    """view loyalty details view"""
    try:
        query_params_str = ""
        for q_param in request.GET:
            if len(query_params_str) == 0:
                query_params_str = f"?{q_param}={request.GET.get(q_param)}"
            else:
                query_params_str += f"&{q_param}={request.GET.get(q_param)}"
        # Fetching the particular loyalty from database

        shops_list, amenities_list = return_shop_and_amenity_list()
        loyalty = Loyalty.objects.filter(id__exact=loyalty_pk).values().first()
        loyalty = return_loyalty_data(loyalty, loyalty_pk, False)
        shops = [shop[1] for shop in shops_list if shop[1] in loyalty["shop"]]
        amenities = [
            shop[1] for shop in amenities_list if shop[1] in loyalty["shop"]
        ]
        url_data = filter_url(
            request.user.role_id.access_content.all(), LOYALTY_CONST
        )
        # response to request
        return render(
            request,
            "loyalty/view_loyalty_details.html",
            context={
                "loyalty": loyalty,
                "shops": shops,
                "amenities": amenities,
                "data": url_data,
                "query_params_str": query_params_str,
            },
        )
    except COMMON_ERRORS:
        traceback.print_exc()
        return render(request, ERROR_TEMPLATE_URL)


# This view helps to edit the particular loyalty.
@authenticated_user
@allowed_users(section=LOYALTY_CONST)
def edit_loyalties(request, loyalty_pk):
    """edit loyalty view"""
    try:
        query_params_str = ""
        for q_param in request.GET:
            if len(query_params_str) == 0:
                query_params_str = f"?{q_param}={request.GET.get(q_param)}"
            else:
                query_params_str += f"&{q_param}={request.GET.get(q_param)}"

        # Database call to fetch all services from configurations.
        shops_from_configurations = return_services_from_configurations()

        # Fetching particular loyalty for updation.
        loyalty = (
            Loyalty.objects.filter(id__exact=loyalty_pk)
            .values(
                "id",
                "loyalty_title",
                "loyalty_type",
                "offer_type",
                "unique_code",
                "category",
                "bar_code_std",
                "redeem_type",
                "cycle_duration",
                "number_of_paid_purchases",
                "valid_from_date",
                "valid_to_date",
                "qr_refresh_time",
                "status",
                "offer_details",
                "terms_and_conditions",
                "redeem_product_code",
                "redeem_product",
                "redeem_product_promotional_code",
                "expiry_in_days",
                "shop_ids",
                "image",
                "reward_image",
                "number_of_total_issuances",
                "reward_unlocked_notification_id_id",
                "reward_expiration_notification_id_id",
                "reward_activated_notification_expiry",
                "reward_expiration_notification_expiry",
                "expire_reward_before_x_number_of_days",
                "reward_expiry_notification_trigger_time",
                "number_of_issued_vouchers",
                "loyalty_list_footer_message",
                "occurance_status",
                "steps_to_redeem",
                "visibility",
                "is_car_wash"
            )
            .first()
        )

        loyalty = return_loyalty_data(loyalty, loyalty_pk)
        shops_list, amenities_list = return_shop_and_amenity_list()
        shops_list.sort(key=lambda shop: shop[1].lower())
        amenities_list.sort(key=lambda shop: shop[1].lower())
        # Dumping data so that we can handle data in javascript
        json_string = json.dumps(loyalty)

        # Post request to make database operation securely
        if request.method == "POST":
            try:
                # Fetching and decoding JSON data from frontend
                post_data_from_front_end = json.loads(
                    request.POST["getdata"],
                    object_hook=lambda d: SimpleNamespace(**d),
                )

                # Converting array into string to store into the database.
                string_converter = StringIO()
                if "All" in post_data_from_front_end.shop:
                    json.dump(
                        [
                            shop["service_name"]
                            for shop in shops_from_configurations
                        ],
                        string_converter,
                    )
                else:
                    json.dump(post_data_from_front_end.shop, string_converter)
                shops = string_converter.getvalue()

                update_response = update_single_loyalty(
                    post_data_from_front_end,
                    loyalty,
                    loyalty_pk,
                    shops,
                    request.user,
                )
                if update_response:
                    return update_response

                # remove_loyalties_cached_data()
                # Response to request
                response = {
                    "status": 1,
                    "message": "ok",
                    "url": reverse("loyalties_list"),
                }
                # Post response
                return JsonResponse(response)
            except (
                AttributeError,
                IndexError,
                ValueError,
                DataError,
                DatabaseError,
            ) as error:
                print(f'While uploading loyalty error occured as-> {str(error)}')
                response = {
                    "status": 0,
                    # "message": str(error),
                    "message": "Loyalty update failed",
                    "url": reverse("loyalties_list"),
                }
                return JsonResponse(response)
        url_data = filter_url(
            request.user.role_id.access_content.all(), LOYALTY_CONST
        )
        remove_stations_cached_data()
        # Get response
        return render(
            request,
            "loyalty/add_loyalty.html",
            context={
                "edit_page": "Yes",
                "available_for_list": return_available_for_values(),
                "status_list": return_status_list(),
                "loyalty": loyalty,
                "loyalty_category_list": return_loyalty_category_list(),
                "offer_type_list": return_offer_type_list(),
                "bar_code_std_list": return_bar_code_std_list(),
                "occurance_statuses": [YES, NO],
                "shops": shops_list,
                "amenities": amenities_list,
                "ops_regions": return_ops_regions(),
                "tsjson": json_string,
                "data": url_data,
                "query_params_str": query_params_str,
                "all_stations_from_backend": all_stations_qs(),
                "redeem_types": return_redeem_types(),
                "cycle_durations": return_cycle_durations(),
                "stations_master_data": return_stations_master_data_for_loyalties_and_promotions(),
                "loyalty_types": return_loyalty_types(),
                "notification_redirect_screens": ["Promotions", "Loyalty", "Loyalty Info"],
                "default_notification_image": DEFAULT_NOTIFICATION_IMAGE,
                "visibility":loyalty["visibility"],
                "is_car_wash":loyalty["is_car_wash"],
            },
        )
    except COMMON_ERRORS:
        traceback.print_exc()
        return render(request, ERROR_TEMPLATE_URL)


# This view will delete particular loyalty
@authenticated_user
@allowed_users(section=LOYALTY_CONST)
def delete_loyalties(request, loyalty_pk):
    """delete loyalty view"""
    try:
        # we have used soft delete technique to delete the records
        # fetching the loyalty with the help of 'loyalty_pk' for
        # deletion of loyalty
        loyalty = Loyalty.objects.filter(id=loyalty_pk).first()
        Loyalty.objects.filter(id=loyalty_pk).update(
            deleted=YES,
            updated_date=timezone.localtime(timezone.now()),
            updated_by=request.user.full_name,
        )
        # deleting dependencies
        if loyalty.loyalty_type == COSTA_COFFEE:
            UserLoyaltyTransactions.objects.filter(
                Q(expired_on=None)
                | Q(expired_on__lte=timezone.localtime(timezone.now())),
                action_code=PURCHASED,
                loyalty_id=loyalty,
            ).update(
                action_code=BURNED,
                updated_date=timezone.localtime(timezone.now()),
            )
            PushNotifications.objects.filter(
                id__in=[
                    loyalty.reward_unlocked_notification_id.id,
                    loyalty.reward_expiration_notification_id.id,
                ]
            ).update(deleted=YES)
        LoyaltyAvailableOn.objects.filter(loyalty_id_id=loyalty_pk).update(
            deleted=YES,
            updated_date=timezone.localtime(timezone.now()),
            updated_by=request.user.full_name,
        )
        prev_audit_data = AuditTrail.objects.filter(
            data_db_id=f"{LOYALTY_CONST}-{loyalty_pk}"
        ).last()
        if prev_audit_data and prev_audit_data.new_data:
            prev_audit_data = prev_audit_data.new_data
            add_audit_data(
                request.user,
                (loyalty.unique_code + ", " + loyalty.loyalty_title),
                f"{LOYALTY_CONST}-{loyalty_pk}",
                AUDIT_DELETE_CONSTANT,
                LOYALTY_CONST,
                None,
                prev_audit_data,
            )
        remove_loyalties_cached_data()
        remove_stations_cached_data()
        # Redirecting user on successful deletion of record
        return redirect("loyalties_list")
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)



class AddLoyaltiesView(APIView):
    """API view to handle adding a new loyalty."""

    @authenticated_user
    @allowed_users(section=LOYALTY_CONST)
    def post(self, request):
        """Handle POST request to add loyalty."""
        try:
            # Step 1: Validate incoming data
            serializer = AddLoyaltyRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return api_response(
                    message=serializer.errors,
                    status=False,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error=serializer.errors,
                )

            validated_data = serializer.validated_data

            # Step 2: Call service layer
            service_response = add_loyalty_service(validated_data, request.user)

            # Step 3: Handle response from service
            if not service_response["status"]:
                return api_response(
                    message=service_response["message"],
                    status=False,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=service_response,
                )

            return api_response(
                status_code=status.HTTP_200_OK,
                message=ConstantMessage.LOYALTY_ADDED_SUCCESS,
                data=service_response["data"],
            )

        except Exception:
            return api_response(
                message=ConstantMessage.SOMETHING_WENT_WRONG,
                status=False,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error=traceback.format_exc(),
            )

    def put(self, request, loyalty_pk):
        """Handle PUT request to update loyalty."""
        try:

            serializer = EditLoyaltyRequestSerializer(
                data={**request.data, "loyalty_pk": loyalty_pk}
            )
            if not serializer.is_valid():
                return api_response(
                    message=serializer.errors,
                    status=False,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error=serializer.errors,
                )

            validated_data = serializer.validated_data

            service_response = update_single_loyalty_service(validated_data, request.user)


            return api_response(
                status_code=status.HTTP_200_OK,
                message=ConstantMessage.LOYALTY_UPDATED_SUCCESS,
                data=service_response["data"],
            )

        except Loyalty.DoesNotExist:
            return api_response(
                message=ConstantMessage.LOYALTY_NOT_FOUND,
                status=False,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        except Exception:
            return api_response(
                message=ConstantMessage.SOMETHING_WENT_WRONG,
                status=False,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error=traceback.format_exc(),
            )