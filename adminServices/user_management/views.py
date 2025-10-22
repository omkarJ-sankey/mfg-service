"""user management view"""
# Date - 02/06/2021


# File details-
#   Author      - Shubham Dhumal
#   Description - This file is mainly focused on
#                   creating and updating Dashboard users .
#   Name        - User Management View
#   Modified by - Shubham Dhumal

# These are all the imports that we are exporting from different
# module's from project or library.
import json
import base64
from types import SimpleNamespace
from passlib.hash import django_pbkdf2_sha256 as handler
from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.views.decorators.http import require_http_methods
from django.conf import settings

# pylint:disable=import-error
from sharedServices.decorators import allowed_users, authenticated_user
from sharedServices.model_files.admin_user_models import (
    AdminAuthorization,
    AdminUser,
    LoginRecords,
    RoleAccessTypes,
)
from sharedServices.common import (
    export_data_function,
    filter_url,
    image_converter,
    order_by_function,
    pagination_and_filter_func,
    randon_string_generator,
    search_validator,
)
from sharedServices.email_common_functions import (
    send_email_function
)
from sharedServices.common_audit_trail_functions import (
    audit_data_formatter,
    add_audit_data,
)
from sharedServices.constants import (
    AZURE_BLOB_STORAGE_URL,
    METHOD_MISMATCH,
    NEW_LOGGED_IN_USER,
    YES,
    EXPORT_TRUE,
    GET_METHOD_ALLOWED,
    POST_METHOD_ALLOWED,
    USER_MANAGEMENT_CONST,
    AUDIT_ADD_CONSTANT,
    AUDIT_UPDATE_CONSTANT,
    COMMON_ERRORS,
    ERROR_TEMPLATE_URL,
    JSON_ERROR_OBJECT
)

from .app_level_const import (
    ALEADY_ERROR_MSG,
    ERROR_MSG,
    FAIL_STATUS,
    SUCCESS_STATUS,
    UPDATE_SUCCESS,
    USER_SUCCESS,
)


CACHE_TTL = getattr(settings, "CACHE_TTL", DEFAULT_TIMEOUT)

# This Method is used to render page and filtering table of user management


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=USER_MANAGEMENT_CONST)
def user_management(request):
    """admin user list"""
    try:
        # Get filter parameters and pagination page number
        page_num = request.GET.get("page", 1)
        status = request.GET.get("loginrecords", None)
        role = request.GET.get("role_id", None)
        search = request.GET.get("search", "")
        search = search_validator(search, "search and email accepted")
        # Sorting parameters
        order_by_name = request.GET.get("order_by_name", None)
        order_by_role = request.GET.get("order_by_role", None)
        order_by_status = request.GET.get("order_by_status", None)
        order_by_email = request.GET.get("order_by_email", None)
        do_export = request.GET.get("export", None)
        # Admin_user_details which is list all user except current login user
        admin_user_details = AdminUser.objects.filter().values(
            "adminauthorization__otp_type",
            "loginrecords__current_status",
            "loginrecords__updated_date",
            "full_name",
            "user_name",
            "email",
            "role_id__role_name",
            "phone",
            "id",
            "profile_picture",
            "created_date",
        )

        page_num = int(page_num)
        # Filter_user_management its array  what filters depends
        # on selected by loged in
        # user and also form url with query of filter
        filter_user_management = [
            {"role_id__role_name__exact": role, "role": role},
            {"loginrecords__current_status__exact": status, "status": status},
            {
                "search": search,
                "search_array": [
                    "full_name__icontains",
                    "user_name__icontains",
                    "email__icontains",
                ],
            },
        ]
        roles = RoleAccessTypes.objects.all()
        ordered_user = order_by_function(
            admin_user_details,
            [
                {"email": ["order_by_email", order_by_email]},
                {"full_name": ["order_by_name", order_by_name]},
                {"role_id__role_name": ["order_by_role", order_by_role]},
                {"user_name": ["order_by_status", order_by_status]},
            ],
        )
        admin_user_details = ordered_user["ordered_table"]
        # filtered_data store array wich containe all
        # user info wich is paginated and
        # filtered depends on Filter_user_management
        filtered_data = pagination_and_filter_func(
            page_num, admin_user_details, filter_user_management
        )
        # context pass to page to all data to render
        context = {
            "blob_root": AZURE_BLOB_STORAGE_URL,
            "roles": roles,
            "user_data": filtered_data["filtered_table"],
            "data_count": filtered_data["data_count"],
            "order_by_name": order_by_name,
            "order_by_email": order_by_email,
            "order_by_role": order_by_role,
            "users_available": bool(len(filtered_data["filtered_table"])!=0),
            "update_url_param": filtered_data["url"] + ordered_user["url"],
            "pagination_num_list": filtered_data["number_list"],
            "current_page": int(page_num),
            "prev": filtered_data["prev_page"],
            "prev_search": search,
            "prev_status": status,
            "prev_role": role,
            "next": filtered_data["next_page"],
            "first_data_number": filtered_data["first_record_number"],
            "last_data_number": filtered_data["last_record_number"],
            "usr_count": "user_count",
            "data": filter_url(
                request.user.role_id.access_content.all(),
                USER_MANAGEMENT_CONST,
            ),
        }
        if do_export == YES:
            for user in filtered_data["filtered_table_for_export"]:
                if user["loginrecords__current_status"] == "Active":
                    user["loginrecords__current_status"] = "Activated"
                else:
                    user["loginrecords__current_status"] = "Deactivated"
            response = export_data_function(
                filtered_data["filtered_table_for_export"],
                [
                    "User ID",
                    "Name",
                    "Email",
                    "Username",
                    "Role",
                    "Last login",
                    "Status",
                    "Created date",
                ],
                [
                    "id",
                    "full_name",
                    "email",
                    "user_name",
                    "role_id__role_name",
                    "loginrecords__updated_date",
                    "loginrecords__current_status",
                    "created_date",
                ],
                "UserRecords",
            )
            if response:
                response.set_cookie(
                    "exported_data_cookie_condition", EXPORT_TRUE, max_age=8
                )
                return response
        return render(request, "user_management/userManagement.html", context)
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


# This API is used to create new user
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=USER_MANAGEMENT_CONST)
def add_new_user(request):
    """add new user"""
    try:
        if request.method == "POST":
            try:
                data = dict(request.POST)["data"][0]
                data = json.loads(data)
                already_email = AdminUser.objects.filter(email=data["email"])
                already_user_name = AdminUser.objects.filter(
                    user_name=data["user_name"]
                )
                var_error_msg = []
                if len(already_email) > 0:
                    var_error_msg.append("Email")
                if len(already_user_name) > 0:
                    var_error_msg.append("User name")
                if len(already_email) > 0 or len(already_user_name) > 0:
                    return JsonResponse(
                        status=FAIL_STATUS,
                        data={
                            "status": "false",
                            "messages": " and ".join(map(str, var_error_msg))
                            + ALEADY_ERROR_MSG,
                        },
                    )
                # role store object of specific to role type
                role = RoleAccessTypes.objects.get(role_name=data["role"])
                # create new user object with data provoided by
                # user and store in temp variable new_user
                if len(data["image"]) > 3:
                    image_data = image_converter(data["image"])
                    image = ContentFile(
                        base64.b64decode(image_data[0]),
                        name=f"{data['full_name']}\
                            _{randon_string_generator()}"
                        + "."
                        + image_data[1],
                    )
                    new_user = AdminUser(
                        role_id=role,
                        full_name=data["full_name"],
                        user_name=data["user_name"],
                        email=data["email"],
                        profile_picture=image,
                        updated_by=request.user.user_name,
                    )
                    # Commiting changes to Data base it will
                    # create new entry to table
                    new_user.save()
                else:
                    new_user = AdminUser(
                        role_id=role,
                        full_name=data["full_name"],
                        user_name=data["user_name"],
                        email=data["email"],
                        updated_by=request.user.user_name,
                    )
                    # Commiting changes to Data base it will
                    # create new entry to table
                    new_user.save()
                admin_user = AdminUser.objects.filter(
                    user_name=data["user_name"]
                ).first()
                # Hashing password to store in db.
                password = handler.hash(data["password"])
                auth_user = AdminAuthorization(
                    user_id=AdminUser.objects.get(email=data["email"]),
                    password=password,
                )
                login_rec = LoginRecords(
                    user_id=AdminUser.objects.get(email=data["email"]),
                    current_status="Active",
                )
                auth_user.save()
                login_rec.save()
                new_data = audit_data_formatter(
                    USER_MANAGEMENT_CONST, admin_user.id
                )
                add_audit_data(
                    request.user,
                    f"{admin_user.user_name}",
                    f"{USER_MANAGEMENT_CONST}-{admin_user.id}",
                    AUDIT_ADD_CONSTANT,
                    USER_MANAGEMENT_CONST,
                    new_data,
                    None,
                )
                send_email_function(
                    data["email"],
                    NEW_LOGGED_IN_USER,
                    data["full_name"],
                    data["password"],
                )
                return JsonResponse(
                    status=SUCCESS_STATUS,
                    data={"status": "true", "messages": USER_SUCCESS},
                )
            except (NotImplementedError, ValueError, AttributeError) as error:
                print(f'While adding new user error occured as-> {str(error)}')
                return JsonResponse(
                    status=FAIL_STATUS,
                    data={"status": "false", "messages": "Error occured while adding new user"},
                )
        return JsonResponse(METHOD_MISMATCH)
    except COMMON_ERRORS:
        return JSON_ERROR_OBJECT


def get_user_old_data(user_id):
    """this function returns old data of user"""
    return audit_data_formatter(USER_MANAGEMENT_CONST, user_id)


def add_user_audit_data(user_id, old_data, user):
    """this function adds audit data of user"""
    admin_user = AdminUser.objects.filter(id=user_id).first()
    new_data = audit_data_formatter(USER_MANAGEMENT_CONST, user_id)
    if old_data != new_data:
        add_audit_data(
            user,
            f"{admin_user.user_name}",
            f"{USER_MANAGEMENT_CONST}-{user_id}",
            AUDIT_UPDATE_CONSTANT,
            USER_MANAGEMENT_CONST,
            new_data,
            old_data,
        )


# This API is used to deactivate user
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=USER_MANAGEMENT_CONST)
def deactivate_user(request):
    """deactivate user"""
    try:
        if request.method == "POST":
            data = request.POST.get("data", False)
            data = json.loads(data)
            try:
                old_data = get_user_old_data(int(data))
                user = LoginRecords.objects.filter(
                    user_id=AdminUser.objects.get(id=data)
                )
                # Updaning user status Inactive
                user.update(current_status="Inactive")
                AdminUser.objects.filter(id=data).update(
                    updated_by=request.user.user_name
                )
                add_user_audit_data(int(data), old_data, request.user)
                return JsonResponse(
                    status=SUCCESS_STATUS,
                    data={"status": "true", "messages": UPDATE_SUCCESS},
                )
            except (NotImplementedError, ValueError, AttributeError):
                return JsonResponse(
                    status=FAIL_STATUS,
                    data={"status": "false", "messages": ERROR_MSG},
                )
        return JsonResponse(METHOD_MISMATCH)
    except COMMON_ERRORS:
        return JSON_ERROR_OBJECT


# This API is used to activate user
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=USER_MANAGEMENT_CONST)
def activate_user(request):
    """activate user"""
    try:
        if request.method == "POST":
            data = request.POST.get("data", False)
            data = json.loads(data)
            try:
                old_data = get_user_old_data(int(data))
                user = LoginRecords.objects.filter(
                    user_id=AdminUser.objects.get(id=data)
                )
                # Updaning user status Inactive
                if user.first():
                    user.update(current_status="Active")
                    AdminUser.objects.filter(id=data).update(
                        updated_by=request.user.user_name
                    )
                else:
                    LoginRecords.objects.create(
                        user_id=AdminUser.objects.get(id=data),
                        current_status="Active",
                    )
                    AdminUser.objects.filter(id=data).update(
                        updated_by=request.user.user_name
                    )
                add_user_audit_data(int(data), old_data, request.user)
                return JsonResponse(
                    status=SUCCESS_STATUS,
                    data={"status": "true", "messages": UPDATE_SUCCESS},
                )
            except (NotImplementedError, ValueError, AttributeError):
                return JsonResponse(
                    status=FAIL_STATUS,
                    data={"status": "false", "messages": ERROR_MSG},
                )
        return JsonResponse(METHOD_MISMATCH)
    except COMMON_ERRORS:
        return JSON_ERROR_OBJECT


# This API is used to updateing user
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=USER_MANAGEMENT_CONST)
def update_user(request):
    """update user"""
    try:
        if request.method == "POST":
            try:
                data = json.loads(request.body.decode("utf-8"))
                old_data = get_user_old_data(int(data["id"]))
                user = AdminUser.objects.filter(id=int(data["id"]))
                role = RoleAccessTypes.objects.get(role_name=data["role"])
                image_data = data["image"]
                image = None

                split = image_data.split(AZURE_BLOB_STORAGE_URL)
                if len(split) < 2:
                    if image_data and image_data != AZURE_BLOB_STORAGE_URL:
                        image_data = image_converter(data["image"])
                        image = ContentFile(
                            base64.b64decode(image_data[0]),
                            name=f"{request.user.full_name}_\
                                {randon_string_generator()}"
                            + "."
                            + image_data[1],
                        )
                        user_data = get_object_or_404(
                            AdminUser, id=user.first().id
                        )
                        user_data.profile_picture = image
                        user_data.save()
                    else:
                        user.first().profile_picture.delete()
                        user.update(profile_picture=None)
                if request.user.id != user.first().id:
                    user.update(
                        role_id=role,
                        full_name=data["full_name"],
                        user_name=data["user_name"],
                        email=data["email"],
                        updated_by=request.user.user_name,
                    )
                else:
                    user.update(
                        full_name=data["full_name"],
                        user_name=data["user_name"],
                        email=data["email"],
                        updated_by=request.user.user_name,
                    )

                add_user_audit_data(int(data["id"]), old_data, request.user)
                return JsonResponse(
                    status=SUCCESS_STATUS,
                    data={"status": "true", "messages": USER_SUCCESS},
                )
            except (NotImplementedError, ValueError, AttributeError) as error:
                if "duplicate" in str(error):
                    user = AdminUser.objects.filter(id=data["id"])
                    already_email = AdminUser.objects.filter(
                        email=data["email"]
                    )
                    already_user_name = AdminUser.objects.filter(
                        user_name=data["user_name"]
                    )
                    var_error_msg = []
                    if len(already_email) > 0:
                        if already_email[0].id != user[0].id:
                            var_error_msg.append("Email")
                    if len(already_user_name) > 0:
                        if already_user_name[0].id != user[0].id:
                            var_error_msg.append("User name")
                    if len(var_error_msg) > 0:
                        return JsonResponse(
                            status=FAIL_STATUS,
                            data={
                                "status": "false",
                                "messages": " and ".join(
                                    map(str, var_error_msg)
                                )
                                + ALEADY_ERROR_MSG,
                            },
                        )
                print(f'While updating user error occured as-> {str(error)}')
                return JsonResponse(
                    status=FAIL_STATUS,
                    data={"status": "false", "messages": "Error occured while updating user"},
                )
        return JsonResponse(METHOD_MISMATCH)
    except COMMON_ERRORS:
        return JSON_ERROR_OBJECT


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def change_profile_picture(request):
    """change profile picture"""
    try:
        if request.method == "POST":
            # Decoding JSON data from frontend
            post_data_from_front_end = json.loads(
                request.POST["getdata"],
                object_hook=lambda d: SimpleNamespace(**d),
            )
            image = post_data_from_front_end.image

            try:
                split = image.split(AZURE_BLOB_STORAGE_URL)
                if len(split) < 2:
                    if image and image != AZURE_BLOB_STORAGE_URL:
                        image_data = image_converter(image)
                        image = ContentFile(
                            base64.b64decode(image_data[0]),
                            name=f"{request.user.full_name}\
                                _{randon_string_generator()}"
                            + "."
                            + image_data[1],
                        )
                        imageupload = get_object_or_404(
                            AdminUser, id=request.user.id
                        )
                        imageupload.profile_picture = image
                        imageupload.save()
                    else:
                        user = AdminUser.objects.filter(id=request.user.id)
                        user.first().profile_picture.delete()
                        user.update(profile_picture=None)
                return JsonResponse(
                    status=SUCCESS_STATUS,
                    data={"status": "true", "messages": USER_SUCCESS},
                )
            except (NotImplementedError, ValueError, AttributeError):
                return JsonResponse(
                    status=FAIL_STATUS,
                    data={"status": "false", "messages": ERROR_MSG},
                )
        return JsonResponse(METHOD_MISMATCH)
    except COMMON_ERRORS:
        return JSON_ERROR_OBJECT


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=USER_MANAGEMENT_CONST)
def check_email_exist(request):
    """check email exist"""
    try:
        if request.method == "POST":
            data = request.POST.get("data")
            user = AdminUser.objects.filter(email=data)
            if len(user) > 0:
                return JsonResponse(
                    status=FAIL_STATUS,
                    data={
                        "status": "false",
                        "messages": "Email Already Exist",
                    },
                )
            return JsonResponse(
                status=SUCCESS_STATUS, data={"status": "true", "messages": ""}
            )
        return JsonResponse(METHOD_MISMATCH)
    except COMMON_ERRORS:
        return JSON_ERROR_OBJECT


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=USER_MANAGEMENT_CONST)
def check_username_exist(request):
    """check username exists"""
    try:
        if request.method == "POST":
            data = request.POST.get("data")
            user = AdminUser.objects.filter(user_name=data)
            if len(user) > 0:
                return JsonResponse(
                    status=FAIL_STATUS,
                    data={
                        "status": "false",
                        "messages": "Email Already Exist",
                    },
                )
            return JsonResponse(
                status=SUCCESS_STATUS,
                data={"status": "true", "messages": ""},
            )
        return JsonResponse("Request method mismatch")
    except COMMON_ERRORS:
        return JSON_ERROR_OBJECT
