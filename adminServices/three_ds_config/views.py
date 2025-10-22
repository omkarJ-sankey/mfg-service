"""3DS config views"""

# Date - 14/12/2024

# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on views(backend logic)
#                      related to 3ds.
#   Name            - 3DS config Views
#   Modified by     - Manish Pawar
#   Modified date   - 14/12/2024

# imports required to create views
import json
from datetime import timedelta

from django.utils import timezone
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib import messages


from cryptography.fernet import Fernet

# pylint:disable=import-error

from sharedServices.model_files.config_models import BaseConfigurations
from sharedServices.model_files.app_user_models import Profile
from sharedServices.model_files.charging_session_models import (
    ThreeDSCheckLogs
)
from sharedServices.decorators import allowed_users, authenticated_user
from sharedServices.common_audit_trail_functions import (
    audit_data_formatter,
    add_audit_data
)
from sharedServices.common import (
    filter_url,
    hasher,
    pagination_and_filter_func,
    date_formater_for_frontend_date,
    date_difference_function,
    filter_function_for_base_configuration,
    export_data_function_multi_tabs
)
from sharedServices.constants import (
    THREE_DS_CONFIG_CONST,
    GET_METHOD_ALLOWED,
    POST_METHOD_ALLOWED,
    COMMON_ERRORS,
    ERROR_TEMPLATE_URL,
    AUDIT_ADD_CONSTANT,
    AUDIT_DELETE_CONSTANT,
    AUDIT_UPDATE_CONSTANT,
    ON_CONST,
    THREE_DS_FOR_ALL_CONFIG_CONST,
    EXPORT_TRUE,
    YES,
    USER_DELETED,
)
import pytz


from ..promotions.promotions_helper_functions import return_status_list
from ..dashboard.app_level_constants import (
    DASHBOARD_DATA_DAYS_LIMIT,
    DEFAULT_DASHBOARD_DATA_DAYS_LIMIT,
)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=THREE_DS_CONFIG_CONST)
def three_ds_config_for_all_app_users(request):
    """3DS config for all app users"""
    try:
        three_ds_configurations = BaseConfigurations.objects.filter(
            base_configuration_key="3ds_configurations"
        )
        data = None
        if request.method == "POST":
            prev_data = json.loads(three_ds_configurations.first().base_configuration_value)
            request_data = request.POST.copy()
            del request_data["csrfmiddlewaretoken"]
            old_data = (
                audit_data_formatter(
                    THREE_DS_FOR_ALL_CONFIG_CONST
                )
            )
            if (
                "kwh_consumed__condition_checkbox" in prev_data
                and prev_data["kwh_consumed__condition_checkbox"]
            ) == (
                "kwh_consumed__condition_checkbox" in request_data
                and request_data["kwh_consumed__condition_checkbox"]
            ):
                request_data["kwh_consumed__last_updated_on_date"] = timezone.now().strftime("%d/%m/%Y %H:%M")
            if (
                "total_transactions__condition_checkbox" in prev_data
                and prev_data["total_transactions__condition_checkbox"]
            ) == (
                "total_transactions__condition_checkbox" in request_data
                and request_data["total_transactions__condition_checkbox"]
            ):
                request_data["total_transactions__last_updated_on_date"] = timezone.now().strftime("%d/%m/%Y %H:%M")
            if (
                "kwh_consumed_within__condition_checkbox" in prev_data
                and prev_data["kwh_consumed_within__condition_checkbox"]
            ) == (
                "kwh_consumed_within__condition_checkbox" in request_data
                and request_data["kwh_consumed_within__condition_checkbox"]
            ):
                request_data["kwh_consumed_within__last_updated_on_date"] = timezone.now().strftime("%d/%m/%Y %H:%M")
            if (
                "total_transactions_within__condition_checkbox" in prev_data
                and prev_data["total_transactions_within__condition_checkbox"]
            ) == (
                "total_transactions_within__condition_checkbox" in request_data
                and request_data["total_transactions_within__condition_checkbox"]
            ):
                request_data["total_transactions_within__last_updated_on_date"] =timezone.now().strftime("%d/%m/%Y %H:%M")
            data = json.dumps(request_data)
            if three_ds_configurations.first():
                three_ds_configurations.update(
                    base_configuration_value=data,
                    updated_date=timezone.localtime(timezone.now()),
                    updated_by=request.user.full_name,
                )
            else:
                BaseConfigurations.objects.create(
                    base_configuration_key="3ds_configurations",
                    base_configuration_name="3ds_configurations",
                    base_configuration_value=data,
                    created_date=timezone.localtime(timezone.now()),
                    updated_date=timezone.localtime(timezone.now()),
                    updated_by=request.user.full_name,
                )
            new_data = audit_data_formatter(
                THREE_DS_FOR_ALL_CONFIG_CONST
            )
            if old_data != new_data:
                add_audit_data(
                    request.user,
                    "3ds Configurations",
                    THREE_DS_FOR_ALL_CONFIG_CONST,
                    (
                        AUDIT_UPDATE_CONSTANT
                        if three_ds_configurations.first() else
                        AUDIT_ADD_CONSTANT
                    ),
                    THREE_DS_FOR_ALL_CONFIG_CONST,
                    new_data,
                    old_data,
                )
            messages.success(
                request,
                "Configurations added successfully!"
            )
        elif three_ds_configurations.first():
            data = three_ds_configurations.first().base_configuration_value
        url_data = filter_url(
            request.user.role_id.access_content.all(), THREE_DS_CONFIG_CONST
        )
        return render(
            request,
            "three_ds_config/config_for_all.html",
            context={
                "data": url_data,
                "active_tab": "3DS_for_all",
                "configurations_data": json.loads(data) if data else data
            },
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


def email_decrypter(user):
    """This function return decrypted email"""
    if user.key:
        decrypter = Fernet(user.key)
        return decrypter.decrypt(user.encrypted_email).decode()
    return USER_DELETED


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=THREE_DS_CONFIG_CONST)
def user_specific_3ds_config(request):
    """User specific 3Ds config"""
    try:
        three_ds_query_params = ""
        for q_param in request.GET:
            if len(three_ds_query_params) == 0:
                three_ds_query_params = (
                    f"?{q_param}={request.GET.get(q_param)}"
                )
            else:
                three_ds_query_params += (
                    f"&{q_param}={request.GET.get(q_param)}"
                )
        page_num = request.GET.get("page", 1)
        status = request.GET.get("status", None)
        search = request.GET.get("search", "")
        three_ds_enabled_users = Profile.objects.filter(
            user_specific_3ds_set_by_admin=True
        ).order_by('-user_specific_3ds_configurations_updated_at')

        updated_url = ""
        if status:
            three_ds_enabled_users = three_ds_enabled_users.filter(
                user_specific_3ds_configurations__icontains=f"\"status\": \"{status}\""
            )
            updated_url += f"&status={status}"
        if search:
            three_ds_enabled_users = three_ds_enabled_users.filter(
                user__user_email=hasher(search)
            ) | three_ds_enabled_users.filter(
                driivz_account_number=search
            )
            updated_url += f"&search={search}"
        filtered_data = pagination_and_filter_func(
            page_num,
            three_ds_enabled_users,
        )
        filtered_data["filtered_table"] = [
            {
                "id": user.id,
                "email": email_decrypter(user.user),
                "driivz_account_number": (
                    user.driivz_account_number
                    if user.driivz_account_number else
                    "Not available"
                ),
                "status": (
                    json.loads(user.user_specific_3ds_configurations)["status"]
                    if user.user_specific_3ds_configurations else
                    'Inactive'
                )
            }
            for user in filtered_data["filtered_table"]
        ]
        url_data = filter_url(
            request.user.role_id.access_content.all(), THREE_DS_CONFIG_CONST
        )
        return render(
            request,
            "three_ds_config/user_specific_3ds_config.html",
            context={
                "data": url_data,
                "active_tab": "User_specific_3DS",
                "three_ds_enabled_users": filtered_data["filtered_table"],
                "data_count": filtered_data["data_count"],
                "first_data_number": filtered_data["first_record_number"],
                "last_data_number": filtered_data["last_record_number"],
                "prev_search": search,
                "prev_status": status,
                "query_params_str": three_ds_query_params,
                "update_url_param": updated_url,
                "pagination_num_list": filtered_data["number_list"],
                "current_page": int(page_num),
                "prev": filtered_data["prev_page"],
                "next": filtered_data["next_page"],
                "status_list": return_status_list()
            },
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=THREE_DS_CONFIG_CONST)
def add_or_edit_user_specific_3ds_config(request, user_id):
    """Add or edit user specific 3Ds config"""
    try:
        edit_user_configurations = user_id != 'add_user'
        data = None
        if request.method == "POST":
            request_data = request.POST
            data = {
                "email": request_data.get('three_ds_user_email'),
                "user_specific_3ds_configurations": {
                    "status": request_data.get('three_ds_status'),
                    "triggered_3ds_for_all_transactions": request_data.get(
                        'trigger_three_ds_for_all_transactions'
                    ) == ON_CONST
                }
            }
            profile_data = Profile.objects.filter(
                id=int(user_id)
            ) if edit_user_configurations else Profile.objects.filter(
                user__user_email=hasher(request_data.get('three_ds_user_email'))
            )
            if profile_data.first() is None:
                messages.warning(
                    request,
                    "Account with provided email not found"
                )
            elif (
                edit_user_configurations is False and
                profile_data.first().user_specific_3ds_set_by_admin
            ):
                messages.warning(
                    request,
                    "3DS configurations are already added for the provided email"
                )
            else:
                old_data = (
                    audit_data_formatter(THREE_DS_CONFIG_CONST, profile_data.first().id)
                    if edit_user_configurations else None
                )
                profile_data.update(
                    user_specific_3ds_set_by_admin=True,
                    user_specific_3ds_configurations=json.dumps(
                        {
                            "status": request_data.get('three_ds_status'),
                            "triggered_3ds_for_all_transactions": request_data.get(
                                'trigger_three_ds_for_all_transactions'
                            ) == ON_CONST
                        }
                    ),
                    user_specific_3ds_configurations_updated_at=timezone.localtime(
                        timezone.now()
                    ),
                    is_3ds_check_active=(
                        request_data.get('three_ds_status') == "Active" and
                        request_data.get(
                            'trigger_three_ds_for_all_transactions'
                        ) == ON_CONST
                    )
                )
                new_data = audit_data_formatter(
                    THREE_DS_CONFIG_CONST,
                    profile_data.first().id
                )
                if old_data != new_data:
                    add_audit_data(
                        request.user,
                        profile_data.first().user.id,
                        f"{THREE_DS_CONFIG_CONST}-{profile_data.first().id}",
                        (
                            AUDIT_UPDATE_CONSTANT
                            if edit_user_configurations else
                            AUDIT_ADD_CONSTANT
                        ),
                        THREE_DS_CONFIG_CONST,
                        new_data,
                        old_data,
                    )
                return redirect('user_specific_3ds_config')
        elif edit_user_configurations:
            three_ds_configurations = Profile.objects.filter(id=int(user_id))
            if three_ds_configurations.first():
                decrypter = Fernet(three_ds_configurations.first().user.key)
                data = {
                    "email": decrypter.decrypt(
                        three_ds_configurations.first().user.encrypted_email
                    ).decode(),
                    "user_specific_3ds_configurations": json.loads(
                        three_ds_configurations.first().user_specific_3ds_configurations
                    ) if three_ds_configurations.first().user_specific_3ds_configurations else {}
                }
        url_data = filter_url(
            request.user.role_id.access_content.all(), THREE_DS_CONFIG_CONST
        )
        return render(
            request,
            "three_ds_config/add_or_edit_user_specific_3ds_config.html",
            context={
                "data": url_data,
                "active_tab": "User_specific_3DS",
                "user_specific_3ds_configurations": data,
                "edit_user_configurations": edit_user_configurations,
                "status_list": return_status_list()
            },
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=THREE_DS_CONFIG_CONST)
def remove_user_specific_3ds_config(request, user_id):
    """Remove user specific 3Ds config"""
    try:
        old_data = audit_data_formatter(THREE_DS_CONFIG_CONST, int(user_id))
        profile_data = Profile.objects.filter(
            id=int(user_id),
        )
        Profile.objects.filter(
            id=int(user_id),
            user_specific_3ds_set_by_admin=True,
        ).update(
            user_specific_3ds_set_by_admin=False,
            user_specific_3ds_configurations=None,
            is_3ds_check_active=False
        )
        if profile_data.first() is None:
            messages.warning(
                request,
                "Account not found"
            )
        else:
            new_data = audit_data_formatter(
                THREE_DS_CONFIG_CONST,
                int(user_id)
            )
            if old_data != new_data:
                add_audit_data(
                    request.user,
                    profile_data.first().user.id,
                    f"{THREE_DS_CONFIG_CONST}-{profile_data.first().id}",
                    AUDIT_DELETE_CONSTANT,
                    THREE_DS_CONFIG_CONST,
                    new_data,
                    old_data,
                )
        return redirect('user_specific_3ds_config')
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


def get_log_object(log):
    """this function returns required log object"""
    return {
        "id": log.id,
        "driivz_account_number": (
            log.three_ds_trigger_log_id.user_id.user_profile.driivz_account_number
        ),
        "session_id": (
            log.session_id.emp_session_id
            if log.session_id else
            "NA"
        ),
        "email": email_decrypter(
            log.three_ds_trigger_log_id.user_id
        ),
        "reason_for_3ds": (
            log.three_ds_trigger_log_id.reason_for_3ds
        ),
        "reason_for_3ds_kwh": (
            log.three_ds_trigger_log_id.reason_for_3ds_kwh
        ),
        "reason_for_3ds_days": (
            log.three_ds_trigger_log_id.reason_for_3ds_days
        ),
        "reason_for_3ds_transactions": (
            log.three_ds_trigger_log_id.reason_for_3ds_transactions
        ),
        "configuration_set_by_admin_for_3ds": (
            log.three_ds_trigger_log_id.configuration_set_by_admin_for_3ds
        ),
        "configuration_set_by_admin_for_3ds_kwh": (
            log.three_ds_trigger_log_id.configuration_set_by_admin_for_3ds_kwh
        ),
        "configuration_set_by_admin_for_3ds_days": (
            log.three_ds_trigger_log_id.configuration_set_by_admin_for_3ds_days
        ),
        "configuration_set_by_admin_for_3ds_transactions": (
            log.three_ds_trigger_log_id.configuration_set_by_admin_for_3ds_transactions
        ),
        "account_creation_date": log.three_ds_trigger_log_id.user_id.timestamp,
        "log_date": log.created_date,
        "status": log.status
    }


def export_3ds_logs_data(data):
    """this function is used to export 3Ds logs data"""
    return export_data_function_multi_tabs(
        [
            [
                get_log_object(log)
                for log in ThreeDSCheckLogs.objects.filter(
                    id__in=[log.id for log in data]
                )
            ]
        ],
        [
            [
                "ID",
                "DRIIVZ Account Number",
                "Session Id",
                "User Email",
                "Reason for 3DS",
                "Reason-kWh",
                "Reason-Days",
                "Reason-Transactions",
                "Configuration set by Admin for 3DS",
                "Configuration-kWh",
                "Configuration-Days",
                "Configuration-Transactions",
                "Account creation Date",
                "Status",
            ],
        ],
        [
            [
                "id",
                "driivz_account_number",
                "session_id",
                "email",
                "reason_for_3ds",
                "reason_for_3ds_kwh",
                "reason_for_3ds_days",
                "reason_for_3ds_transactions",
                "configuration_set_by_admin_for_3ds",
                "configuration_set_by_admin_for_3ds_kwh",
                "configuration_set_by_admin_for_3ds_days",
                "configuration_set_by_admin_for_3ds_transactions",
                "account_creation_date",
                "status",
            ],
        ],
        ["3DS Logs"],
    )


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=THREE_DS_CONFIG_CONST)
def three_ds_logs(request):
    """3DS logs"""
    try:
        three_ds_query_params = ""
        for q_param in request.GET:
            if len(three_ds_query_params) == 0:
                three_ds_query_params = (
                    f"?{q_param}={request.GET.get(q_param)}"
                )
            else:
                three_ds_query_params += (
                    f"&{q_param}={request.GET.get(q_param)}"
                )
        three_ds_check_logs = ThreeDSCheckLogs.objects.all().order_by('-created_date')
        page_num = request.GET.get("page", 1)
        status = request.GET.get("status", None)
        search = request.GET.get("search", None)
        if not search:
            search = None
        from_date = request.GET.get("from_date", "")
        to_date = request.GET.get("to_date", "")
        do_export = request.GET.get("export", None)
        updated_url = ""
        date_difference = 0
        maximum_to_date = 0
        dashboard_data_days_limit = int(
            filter_function_for_base_configuration(
                DASHBOARD_DATA_DAYS_LIMIT, DEFAULT_DASHBOARD_DATA_DAYS_LIMIT
            )
        )
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
        if from_date:
            three_ds_check_logs = three_ds_check_logs.filter(
                created_date__gte=date_formater_for_frontend_date(from_date)
            )
            updated_url += f"&from_date={from_date}"
        if to_date:
            formatted_to_date = date_formater_for_frontend_date(to_date)
            if from_date:
                date_difference = date_difference_function(
                    from_date, formatted_to_date
                )
            three_ds_check_logs = three_ds_check_logs.filter(
                created_date__lte=formatted_to_date + timedelta(days=1)
            )
            updated_url += "&to_date=" if to_date>from_date else f"&to_date={to_date}"
        filtered_data = pagination_and_filter_func(
            page_num,
            three_ds_check_logs,
            [
                {
                    "search": search,
                    "search_array": [
                        "session_id__emp_session_id__contains",
                        "session_id__user_account_number__icontains",
                    ],
                },
                {"status__exact": status},
            ],
        )
        if do_export == YES:
            response_three_ds_export = export_3ds_logs_data(
                filtered_data["filtered_table_for_export"]
            )
            if response_three_ds_export:
                response_three_ds_export.set_cookie(
                    "exported_data_cookie_condition",
                    EXPORT_TRUE,
                    max_age=8
                )
            return response_three_ds_export
        filtered_data["filtered_table"] = [
            get_log_object(log)
            for log in filtered_data["filtered_table"]
        ]
        url_data = filter_url(
            request.user.role_id.access_content.all(), THREE_DS_CONFIG_CONST
        )
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
        return render(
            request,
            "three_ds_config/3ds_logs.html",
            context={
                "data": url_data,
                "active_tab": "3Ds_logs",
                "three_ds_logs": filtered_data["filtered_table"],
                "data_count": filtered_data["data_count"],
                "first_data_number": filtered_data["first_record_number"],
                "last_data_number": filtered_data["last_record_number"],
                "prev_search": search if search else '',
                "prev_status": status,
                "prev_from_date": from_date,
                "prev_to_date": to_date,
                "query_params_str": three_ds_query_params,
                "update_url_param": (
                    filtered_data["url"]
                    + updated_url
                ),
                "pagination_num_list": filtered_data["number_list"],
                "current_page": int(page_num),
                "prev": filtered_data["prev_page"],
                "next": filtered_data["next_page"],
                "status_list": ["Successful", "Failed"],
                "to_date_difference_from_current_date": date_difference,
                "maximum_to_date": maximum_to_date,
                "time_difference": time_difference,
                "dashboard_data_days_limit": dashboard_data_days_limit,
                "logs_available": len(filtered_data["filtered_table"]) != 0
            },
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)
