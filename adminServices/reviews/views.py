"""reviews views"""
# Date - 23/06/2021


# File details-
#   Author      - Shubham Dhumal
#   Description - This file is contain logic and api for reviews dashboard.
#   Name        - Rewviews View
#   Modified by - Manish Pawar


# These are all the imports that we are exporting from different
# module's from project or library.

import threading
import json

from datetime import datetime, timedelta
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.cache.backends.base import DEFAULT_TIMEOUT

# pylint:disable=import-error
from sharedServices.common import (
    pagination_and_filter_func,
    filter_url,
    date_formater_for_frontend_date,
    date_difference_function,
    search_validator,
)
from sharedServices.common_audit_trail_functions import (
    audit_data_formatter,
    add_audit_data,
)
from sharedServices.model_files.review_models import Reviews

from sharedServices.decorators import (
    allowed_users,
    authenticated_user,
)

from sharedServices.shared_station_serializer import (
    caching_station_finder_data,
)
from sharedServices.constants import (
    UPLOAD_UPDATE_SUCCESS,
    YES,
    NO,
    FLAG_TRUE,
    GET_METHOD_ALLOWED,
    POST_METHOD_ALLOWED,
    COMMON_ERRORS,
    ERROR_TEMPLATE_URL,
    SOMETHING_WRONG,
    REVIEW_CONST,
    AUDIT_UPDATE_CONSTANT,
)
from .app_level_const import REVIEW_FILTER

CACHE_TTL = getattr(settings, "CACHE_TTL", DEFAULT_TIMEOUT)


def remove_review_cached_data():
    """this function is used to remove cached data of reviews views"""
    start_caching_reviews_data = threading.Thread(
        target=caching_station_finder_data,
        daemon=True
    )
    start_caching_reviews_data.start()


# This Method is used to render page and filtering table of reviews


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section="Reviews")
def reviews(request):
    """reviews view"""
    try:
        page_num = request.GET.get("page", 1)
        status = request.GET.get("status", "pending")
        s_type = request.GET.get("station_type", None)
        flagged = request.GET.get("flag", None)
        search = request.GET.get("search", None)
        search = search_validator(search)
        from_date = request.GET.get("from_date", None)
        to_date = request.GET.get("to_date", None)
        date_difference = 0
        url = ""
        # request  contain start to end date in single string new
        # to seprate by using split
        updated_url = ""
        review_data = Reviews.objects.all().order_by("-post_date")
        if to_date:
            formatted_to_date = date_formater_for_frontend_date(to_date)
            date_difference = date_difference_function(from_date,formatted_to_date)
       
            review_data = review_data.filter(
                post_date__lte=formatted_to_date + timedelta(days=1)
            )
            updated_url += f"&to_date={to_date}"

        if from_date:
            review_data = review_data.filter(
                post_date__gte=date_formater_for_frontend_date(from_date)
            )
            updated_url += f"&from_date={from_date}"
        if from_date is None:
            from_date = ""
        if to_date is None:
            to_date = ""
        flagged_status = None
        if flagged and flagged != "All":
            flagged_status = YES if flagged == FLAG_TRUE else NO
        filtered_data = pagination_and_filter_func(
            page_num,
            review_data,
            [
                {"flag__exact": flagged_status, "flag": flagged},
                {"status__exact": status, "status": status},
                {
                    "search": search,
                    "search_array": [
                        "station_id__station_id__contains",
                        "station_id__station_name__contains",
                    ],
                },
            ],
        )
        # to handel None error we store empty string
        if search is None:
            search = ""
        # to handel None error we store empty string array for stat or end date
        filtered_data["url"] = (
            filtered_data["url"] + "&status=All"
            if status and status == "All"
            else filtered_data["url"]
        )
        url = filtered_data["url"] + updated_url

        context = {
            "to_date_difference_from_current_date": date_difference,
            "reviews_data": filtered_data["filtered_table"],
            "data_count": filtered_data["data_count"],
            "first_data_number": filtered_data["first_record_number"],
            "last_data_number": filtered_data["last_record_number"],
            "prev_date_from": from_date,
            "prev_date_to": to_date,
            "prev_search": search,
            "prev_status": status,
            "prev_s_type": s_type,
            "prev_flag": flagged,
            "update_url_param": url,
            "pagination_num_list": filtered_data["number_list"],
            "current_page": int(page_num),
            "prev": filtered_data["prev_page"],
            "next": filtered_data["next_page"],
            "data": filter_url(
                request.user.role_id.access_content.all(), "Reviews"
            ),
        }
        return render(request, "reviews/reviews.html", context)
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


def get_reviews_data_list_for_audit(reviews_ids):
    """this function returns reviews lis data for audit trail"""
    reviews = Reviews.objects.filter(id__in=reviews_ids)
    return [
        audit_data_formatter(REVIEW_CONST, review.id) for review in reviews
    ]


def add_review_audit_data(
    old_reviews_data, new_reviews_data, review_ids, user
):
    """this function is used to add reviews audit data"""
    for i in range(len(review_ids)):
        add_audit_data(
            user,
            f"{review_ids[i]}",
            f"{REVIEW_CONST}-{review_ids[i]}",
            AUDIT_UPDATE_CONSTANT,
            REVIEW_CONST,
            new_reviews_data[i],
            old_reviews_data[i],
        )


# This api used approve api to display on station review
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section="Reviews")
def approve(request):
    """approve filter"""
    try:
        body = json.loads(request.body.decode("utf-8"))
        data = body["data"]
        filtered_reviews = body["filter"]
        try:
            # this if block contain logic if user want approve all
            if (len(data) == 0) or "All" in data:
                filtered_table = Reviews.objects.filter(status="pending")
                for key, value in filtered_reviews.items():
                    if value and value != "All":
                        fil = {REVIEW_FILTER[key]: value}
                        filtered_table = filtered_table.filter(**fil)
                reviews_ids = [review.id for review in filtered_table]
                old_reviews_data = get_reviews_data_list_for_audit(reviews_ids)
                filtered_table.update(status="Approved")
                new_reviews_data = get_reviews_data_list_for_audit(reviews_ids)
                add_review_audit_data(
                    old_reviews_data,
                    new_reviews_data,
                    reviews_ids,
                    request.user,
                )
                return HttpResponse(UPLOAD_UPDATE_SUCCESS)

            reviews_ids = [
                review.id
                for review in Reviews.objects.filter(
                    id__in=[int(data_id) for data_id in data]
                )
            ]
            old_reviews_data = get_reviews_data_list_for_audit(reviews_ids)
            # this  block contain logic if user want approve selected rows
            for i in data:
                Reviews.objects.filter(id=int(i)).update(
                    status="Approved", update_by=request.user.user_name
                )

            new_reviews_data = get_reviews_data_list_for_audit(reviews_ids)
            add_review_audit_data(
                old_reviews_data, new_reviews_data, reviews_ids, request.user
            )
            remove_review_cached_data()
            return HttpResponse(UPLOAD_UPDATE_SUCCESS)
        except (NotImplementedError, ValueError, AttributeError):
            return HttpResponse("Something went wrong")
    except COMMON_ERRORS:
        return HttpResponse(SOMETHING_WRONG)


# This api used disapprove api to display on station review
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section="Reviews")
def disapprove(request):
    """disapprove review"""
    try:
        body = json.loads(request.body.decode("utf-8"))
        data = body["data"]
        filtered_reviews = body["filter"]
        try:
            # this if block contain logic if user want disapprove all

            if (len(data) == 0) or "All" in data:
                filtered_table = Reviews.objects.filter(status="pending")
                for key, value in filtered_reviews.items():
                    if value and value != "All":
                        fil = {REVIEW_FILTER[key]: value}
                        filtered_table = filtered_table.filter(**fil)
                reviews_ids = [review.id for review in filtered_table]
                old_reviews_data = get_reviews_data_list_for_audit(reviews_ids)
                filtered_table.update(status="Disapproved")
                new_reviews_data = get_reviews_data_list_for_audit(reviews_ids)
                add_review_audit_data(
                    old_reviews_data,
                    new_reviews_data,
                    reviews_ids,
                    request.user,
                )
                return HttpResponse(UPLOAD_UPDATE_SUCCESS)

            reviews_ids = [
                review.id
                for review in Reviews.objects.filter(
                    id__in=[int(data_id) for data_id in data]
                )
            ]
            old_reviews_data = get_reviews_data_list_for_audit(reviews_ids)
            # this  block contain logic if user want sisapprove selected rows
            for i in data:
                Reviews.objects.filter(id=int(i)).update(
                    status="Disapproved", update_by=request.user.user_name
                )

            new_reviews_data = get_reviews_data_list_for_audit(reviews_ids)
            add_review_audit_data(
                old_reviews_data, new_reviews_data, reviews_ids, request.user
            )
            return HttpResponse(UPLOAD_UPDATE_SUCCESS)
        except (NotImplementedError, ValueError, AttributeError):
            return HttpResponse("Something gose wrong")
    except COMMON_ERRORS:
        return HttpResponse(SOMETHING_WRONG)
