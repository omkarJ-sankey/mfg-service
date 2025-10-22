"""Audit trail views"""
# Date - 14/04/2022
# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on views(backend logic)
#                       related to audit trail.
#   Name            - Audit trail Views
#   Modified by     - Manish Pawar
#   Modified date   - 14/04/2022

# imports required to create views
import json

from datetime import timedelta 
from types import SimpleNamespace
from django.utils import timezone
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import traceback

# pylint:disable=import-error
from sharedServices.model_files.audit_models import AuditTrail
from sharedServices.model_files.admin_user_models import RoleAccessTypes
from sharedServices.decorators import allowed_users, authenticated_user
from sharedServices.common import (
    filter_url,
    order_by_function,
    pagination_and_filter_func,
    date_formater_for_frontend_date,
    string_to_array_converter,
    date_difference_function,
)
from sharedServices.constants import (
    AUDIT_TRAIL_CONST,
    GET_METHOD_ALLOWED,
    POST_METHOD_ALLOWED,
    YES,
    AZURE_BLOB_STORAGE_URL,
    COMMON_ERRORS,
    ERROR_TEMPLATE_URL,
    JSON_ERROR_OBJECT,
)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=AUDIT_TRAIL_CONST)
def audit_list_view(request):
    """list audit trail data"""
    try:
        query_params_str = ""
        for q_param in request.GET:
            if len(query_params_str) == 0:
                query_params_str = f"?{q_param}={request.GET.get(q_param)}"
            else:
                query_params_str += f"&{q_param}={request.GET.get(q_param)}"
        page_num = request.GET.get("page", 1)
        search = request.GET.get("search", "")
        user_role = request.GET.get("user_role", None)
        review_status = request.GET.get("review_status", None)
        module = request.GET.get("module", None)
        action = request.GET.get("action", None)
        from_date = request.GET.get("from_date", "")
        to_date = request.GET.get("to_date", "")
        date_difference = 0
        # ordering parameters
        order_by_id = request.GET.get("order_by_id", None)
        order_by_date = request.GET.get("order_by_date", None)
        # ordering of stations
        updated_url = ""
        audit_trail_data = AuditTrail.objects.all()
        ordered_audit_trail_data = order_by_function(
            audit_trail_data,
            [
                {"id": ["order_by_id", order_by_id]},
                {"created_date": ["order_by_date", order_by_date]},
            ],
        )
        audit_trail_data = ordered_audit_trail_data["ordered_table"]
        if from_date:
            audit_trail_data = audit_trail_data.filter(
                created_date__gte=date_formater_for_frontend_date(from_date)
            )
            updated_url += f"&from_date={from_date}"
        if to_date:
            formatted_to_date = date_formater_for_frontend_date(to_date)
            date_difference = date_difference_function(from_date,formatted_to_date)
            audit_trail_data = audit_trail_data.filter(
                created_date__lte=formatted_to_date + timedelta(days=1)
            )
            updated_url += f"&to_date={to_date}"
            
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
        # Here pagination_and_filter_func() is the common function to provide
        # filteration and pagination.
        filtered_data_audit_trail_data = pagination_and_filter_func(
            page_num,
            audit_trail_data,
            [
                {
                    "search": search,
                    "search_array": [
                        "module_id__contains",
                        "user_name__icontains",
                    ],
                },
                {"user_role__exact": user_role},
                {"module__exact": module},
                {"action__exact": action},
                {"review_status__exact": review_status},
            ],
        )
        # Here filter_url() function is used to filter
        # navbar elements so that we can  render only those navbar tabs
        # to which logged in user have access.
        url_data = filter_url(
            request.user.role_id.access_content.all(), AUDIT_TRAIL_CONST
        )
        context = {
            "to_date_difference_from_current_date": date_difference,
            "audit_data": filtered_data_audit_trail_data["filtered_table"],
            "data_count": filtered_data_audit_trail_data["data_count"],
            "first_data_number": filtered_data_audit_trail_data[
                "first_record_number"
            ],
            "last_data_number": filtered_data_audit_trail_data[
                "last_record_number"
            ],
            "status_list": ["Active", "Inactive", "Coming soon"],
            "prev_search": search,
            "prev_id_order": order_by_id,
            "prev_date_order": order_by_date,
            "prev_user_role": user_role,
            "prev_review_status": review_status,
            "prev_module": module,
            "prev_action": action,
            "prev_from_date": from_date,
            "prev_to_date": to_date,
            "time_difference":time_difference,
            "review_status_list": ["Yes", "No"],
            "user_role_list": [
                roles.role_name for roles in RoleAccessTypes.objects.all()
            ],
            "module_list": [
                module["module"]
                for module in AuditTrail.objects.all()
                .values("module")
                .distinct()
            ],
            "action_list": [
                module["action"]
                for module in AuditTrail.objects.all()
                .values("action")
                .distinct()
            ],
            "update_url_param": (
                filtered_data_audit_trail_data["url"]
                + updated_url
                + ordered_audit_trail_data["url"]
            ),
            "pagination_num_list": filtered_data_audit_trail_data[
                "number_list"
            ],
            "current_page": int(page_num),
            "prev": filtered_data_audit_trail_data["prev_page"],
            "next": filtered_data_audit_trail_data["next_page"],
            "data": url_data,
            "query_params_str": query_params_str,
        }
        return render(
            request,
            "audit_trail/audit_list.html",
            context=context,
        )
    except COMMON_ERRORS:
        traceback.print_exc()
        return render(request, ERROR_TEMPLATE_URL)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=AUDIT_TRAIL_CONST)
def audit_detail_view(request, detail_row_id):
    """detail audit trail data"""
    try:
        query_params_str = ""
        for q_param in request.GET:
            if len(query_params_str) == 0:
                query_params_str = f"?{q_param}={request.GET.get(q_param)}"
            else:
                query_params_str += f"&{q_param}={request.GET.get(q_param)}"
        # Dumping data in JSON so that we can handle that in frontend.
        audit_entry = AuditTrail.objects.filter(id=detail_row_id).first()
        if audit_entry is None:
            return redirect("audit_list")
        audit_data = json.dumps(
            {
                "new_data": (
                    string_to_array_converter(audit_entry.new_data)
                    if audit_entry.new_data
                    else {}
                ),
                "old_data": (
                    string_to_array_converter(audit_entry.previous_data)
                    if audit_entry.previous_data
                    else {}
                ),
            }
        )
        prev_data_available = None
        next_data_available = None
        # prev_rows = AuditTrail.objects.filter(
        #     id__lt=detail_row_id, data_db_id=audit_entry.data_db_id
        # ).last()
        prev_rows = AuditTrail.objects.filter(
            id__lt=detail_row_id
        ).last()
        if prev_rows:
            prev_data_available = prev_rows.id
        # next_rows = AuditTrail.objects.filter(
        #     id__gt=detail_row_id, data_db_id=audit_entry.data_db_id
        # ).first()
        next_rows = AuditTrail.objects.filter(
            id__gt=detail_row_id
        ).first()
        if next_rows:
            next_data_available = next_rows.id
        return render(
            request,
            "audit_trail/audit_details.html",
            {
                "data": filter_url(
                    request.user.role_id.access_content.all(),
                    AUDIT_TRAIL_CONST,
                ),
                "audit_data": audit_data,
                "prev_data_available": prev_data_available,
                "next_data_available": next_data_available,
                "audit_entry": audit_entry,
                "query_params_str": query_params_str,
                "blob_url": AZURE_BLOB_STORAGE_URL,
            },
        )
    except COMMON_ERRORS:
        traceback.print_exc()
        return render(request, ERROR_TEMPLATE_URL)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def mark_as_reviewed(request):
    """mark audit data as reviewed view"""
    # Post request to make database queries securely.
    try:
        if request.method == "POST":
            # Decoding JSON data from frontend
            post_data_from_front_end = json.loads(
                request.POST["getdata"],
                object_hook=lambda d: SimpleNamespace(**d),
            )
            # Status update operation.
            AuditTrail.objects.filter(
                id__exact=int(post_data_from_front_end.audit_id)
            ).update(
                review_status=YES,
                reviewd_by=request.user.full_name,
                review_date=timezone.localtime(timezone.now()),
                updated_date=timezone.localtime(timezone.now()),
            )
        return JsonResponse({"status": 1, "message": "ok"})
    except COMMON_ERRORS:
        return JSON_ERROR_OBJECT
