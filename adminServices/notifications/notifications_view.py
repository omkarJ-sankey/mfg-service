"""notifications views"""
#  File details-
#   Author      - Ketan Ganvir
#   Description - This file is mainly focused on showing, handling and sending InApp and Push Notifications
#   Name        - Notification View
#   Modified by - Ketan Ganvir
#   last modified - 17/03/23

# These are all the imports that we are exporting from
# different module's from project or library.

# import firebase_admin
# from firebase_admin import credentials, messaging
#pylint:disable=import-error
import concurrent.futures
from decouple import config
import pytz
import ast
import threading
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.utils import timezone

from adminServices.configurations.app_level_constants import (
    ADD_NEW_PUSH_NOTIFICATION,
    UPDATE_PUSH_NOTIFICATION,
    VIEW_PUSH_NOTIFICATION,
    DELIVERED,
    SCHEDULED,
    DRAFT,
    FAILED,
    FCM_NOTIFICATION,
)

from sharedServices.common import (
    filter_url,
)
from sharedServices.model_files.app_user_models import Profile
from sharedServices.model_files.notifications_module_models import (
    PushNotifications,
)
from sharedServices.model_files.station_models import Stations

from sharedServices.decorators import allowed_users, authenticated_user

from sharedServices.image_optimization_funcs import optimize_image

from sharedServices.model_files.charging_session_models import (
    ChargingSession,
)
from sharedServices.constants import (
    NOTIFICATION_CONST,
    COMMON_ERRORS,
    ERROR_TEMPLATE_URL,
    YES,
    NO,
    IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN,
    EV_NOTIFICATION_IMAGE,
    GET_METHOD_ALLOWED,
    POST_METHOD_ALLOWED,
    SCREEN_NAME_FOR_PUSH_NOTIFICATION,
    AUDIT_DELETE_CONSTANT,
    INVALID_DATE_TIME,
    LIST_OF_ASSIGN_TO,
    LIST_OF_CATEGORY,
    PUSH_NOTIFICATION_CONST,
    AUDIT_ADD_CONSTANT,
    AUDIT_UPDATE_CONSTANT,
    DEFAULT_LIST_OF_CATEGORY,
    DEFAULT_LIST_OF_ASSIGN_TO,
    DEFAULT_LIST_OF_SCREENS,
    PUSH_NOTIFICATION_LOYALTY_TYPE,
)

from sharedServices.common import (
    filter_url,
    order_by_function,
    pagination_and_filter_func,
    array_to_string_converter,
    string_to_array_converter,
    image_converter,
    randon_string_generator,
    filter_function_for_base_configuration,
    send_push,
    search_validator,
)

from sharedServices.common_audit_trail_functions import (
    add_audit_data,
    audit_data_formatter,
)


# firebase_admin.initialize_app(cred)
baseURL = config("DJANGO_APP_BLOB_STORAGE_URL")


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=NOTIFICATION_CONST)
def notifications_list_func(request):
    """this functions creates list of notifications"""
    try:
        type_of_notifications = [
            "Push Notification",
            "In App Notification",
        ]
        status_of_notification = ["Sent", "Scheduled"]
        query_params_str = ""
        for q_param in request.GET:
            if len(query_params_str) == 0:
                query_params_str = f"?{q_param}={request.GET.get(q_param)}"
            else:
                query_params_str += f"&{q_param}={request.GET.get(q_param)}"

        # Database call to promotions.
        push_notifications = PushNotifications.objects.filter(
            ~Q(notification_for=PUSH_NOTIFICATION_LOYALTY_TYPE),
            deleted=NO,
        ).order_by("-id")
        page_num = request.GET.get("page", 1)
        status = request.GET.get("status", None)
        search = request.GET.get("search", "")
        search = search_validator(search)
        notification_type = request.GET.get("notification_type", None)
        order_by_scheduled_time = request.GET.get(
            "order_by_scheduled_time", None
        )
        order_by_delivered_time = request.GET.get(
            "order_by_delivered_time", None
        )

        ordered_push_notifications = order_by_function(
            push_notifications,
            [
                {
                    "scheduled_time": [
                        "order_by_scheduled_time",
                        order_by_scheduled_time,
                    ]
                },
                {
                    "delivered_time": [
                        "order_by_delivered_time",
                        order_by_delivered_time,
                    ]
                },
            ],
        )
        push_notifications = ordered_push_notifications["ordered_table"]

        inapp_notification = None
        push_notification = None
        if notification_type and notification_type != "All":
            inapp_notification = "false"
            push_notification = "false"
            if notification_type == "Push Notification":
                push_notification = "true"
            if notification_type == "In App Notification":
                inapp_notification = "true"
        filtered_data_push_notification = pagination_and_filter_func(
            page_num,
            push_notifications,
            [
                {
                    "search": search,
                    "search_array": [
                        "subject__icontains",
                        "inapp_notification__icontains",
                    ],
                },
                {"status__exact": status},
                {"inapp_notification__exact": inapp_notification},
                {"push_notification__exact": push_notification},
            ],
        )

        url_data = filter_url(
            request.user.role_id.access_content.all(), NOTIFICATION_CONST
        )

        return render(
            request,
            "notifications/notifications_list.html",
            context={
                "data": url_data,
                "push_notification_listing_data": PushNotifications.objects.filter(
                    deleted=NO
                ),
                "active_tab": "Notifications",
                "push_notification": filtered_data_push_notification[
                    "filtered_table"
                ],
                "data_count": filtered_data_push_notification["data_count"],
                "first_data_number": filtered_data_push_notification[
                    "first_record_number"
                ],
                "last_data_number": filtered_data_push_notification[
                    "last_record_number"
                ],
                "pagination_num_list": filtered_data_push_notification[
                    "number_list"
                ],
                "query_params_str": query_params_str,
                "prev_search": search,
                "prev_status": status,
                "status_list": [SCHEDULED, DELIVERED, DRAFT, FAILED],
                "prev_notification_type": notification_type,
                "prev": filtered_data_push_notification["prev_page"],
                "next": filtered_data_push_notification["next_page"],
                "update_url_param": (
                    filtered_data_push_notification["url"]
                    + (
                        (
                            f"&notification_type={notification_type}"
                            if len(filtered_data_push_notification["url"])
                            else f"?notification_type={notification_type}"
                        )
                        if notification_type
                        else ""
                    )
                    + (
                        (
                            f"&status={status}"
                            if len(filtered_data_push_notification["url"])
                            else f"?status={status}"
                        )
                        if status
                        else ""
                    )
                    + ordered_push_notifications["url"]
                ),
                "current_page": int(page_num),
                "type_of_notifications": type_of_notifications,
                "status_of_notification": status_of_notification,
                "inapp_notification": inapp_notification,
                "previous_order_by_scheduled_time": order_by_scheduled_time,
                "previous_order_by_delivered_time": order_by_delivered_time,
            },
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


def send_push_for_each(user_id_for_obj, inapp_notification_object, id):
    try:
        PushNotifications.objects.filter(id=id).update(
            status=DELIVERED,
            delivered_time=timezone.localtime(timezone.now()).replace(
                tzinfo=pytz.timezone("UTC")
            ),
        )
        if inapp_notification_object["inapp_notification"] == "true":
            push_notification_object_for_app = dict(
                PushNotifications.objects.filter(
                    id=id, inapp_notification="true"
                )
                .values(
                    "id",
                    "subject",
                    "description",
                    "image",
                    "delivered_time",
                    "screens",
                )
                .first()
            )
            push_notification_object_for_app[
                "delivered_time"
            ] = push_notification_object_for_app["delivered_time"].strftime(
                "%Y-%m-%dT%H:%M:%S"
            )
            push_notification_object_for_app["read_status"] = False
            for user_id in user_id_for_obj:
                inapp_notification_previous_object = (
                    Profile.objects.filter(user_id=user_id)
                    .values("inapp_notification_object")
                    .first()
                )
                if (
                    inapp_notification_previous_object[
                        "inapp_notification_object"
                    ]
                    == None
                ):
                    inapp_notification_new_object = array_to_string_converter(
                        [push_notification_object_for_app]
                    )
                else:
                    inapp_notification_new_object = array_to_string_converter(
                        (
                            [push_notification_object_for_app]
                            + string_to_array_converter(
                                inapp_notification_previous_object[
                                    "inapp_notification_object"
                                ]
                            )
                        )
                    )
                Profile.objects.filter(user_id=user_id).update(
                    inapp_notification_object=inapp_notification_new_object
                )
    except Exception as error:
        print(error)


def common_preference(data):
    registration_tokens = []
    user_id_for_obj = []
    if data == "Loyalty":
        registration_tokens = list(
            Profile.objects.filter(
                loyalty_preference_status=True, fcm_device_token__isnull=False
            ).values_list("fcm_device_token", flat=True)
        )
        user_id_for_obj = list(
            Profile.objects.filter(
                loyalty_preference_status=True, fcm_device_token__isnull=False
            ).values_list("user_id", flat=True)
        )
    if data == "Promotions":
        registration_tokens = list(
            Profile.objects.filter(
                promotion_preference_status=True,
                fcm_device_token__isnull=False,
            ).values_list("fcm_device_token", flat=True)
        )
        user_id_for_obj = list(
            Profile.objects.filter(
                promotion_preference_status=True,
                fcm_device_token__isnull=False,
            ).values_list("user_id", flat=True)
        )
    if data == "Default Notification Screen":
        registration_tokens = list(
            Profile.objects.filter(fcm_device_token__isnull=False).values_list(
                "fcm_device_token", flat=True
            )
        )
        user_id_for_obj = list(
            Profile.objects.filter(fcm_device_token__isnull=False).values_list(
                "user_id", flat=True
            )
        )

    return [registration_tokens, user_id_for_obj]


def common_preference_ev_user(data):
    ev_user_id = (
        ChargingSession.objects.filter(
            Q(session_status="running")
            | Q(session_status="completed")
            | Q(session_status="closed")
        )
        .values("user_id_id")
        .distinct()
    )
    if ev_user_id:
        if data == "Loyalty":
            registration_tokens = list(
                Profile.objects.filter(
                    loyalty_preference_status=True,
                    fcm_device_token__isnull=False,
                    user_id__in=ev_user_id,
                ).values_list("fcm_device_token", flat=True)
            )
            user_id_for_obj = list(
                Profile.objects.filter(
                    loyalty_preference_status=True,
                    fcm_device_token__isnull=False,
                    user_id__in=ev_user_id,
                ).values_list("user_id", flat=True)
            )
        if data == "Promotions":
            registration_tokens = list(
                Profile.objects.filter(
                    promotion_preference_status=True,
                    fcm_device_token__isnull=False,
                    user_id__in=ev_user_id,
                ).values_list("fcm_device_token", flat=True)
            )
            user_id_for_obj = list(
                Profile.objects.filter(
                    promotion_preference_status=True,
                    fcm_device_token__isnull=False,
                    user_id__in=ev_user_id,
                ).values_list("user_id", flat=True)
            )
        if data == "Default Notification Screen":
            registration_tokens = list(
                Profile.objects.filter(
                    fcm_device_token__isnull=False, user_id__in=ev_user_id
                ).values_list("fcm_device_token", flat=True)
            )
            user_id_for_obj = list(
                Profile.objects.filter(
                    fcm_device_token__isnull=False, user_id__in=ev_user_id
                ).values_list("user_id", flat=True)
            )
    return [registration_tokens, user_id_for_obj]


def common_preference_for_domain(data, user_domain):
    registration_tokens = []
    user_id_for_obj = []
    if data == "Loyalty":
        registration_tokens = list(
            Profile.objects.filter(
                loyalty_preference_status=True,
                fcm_device_token__isnull=False,
                user_domain=user_domain,
            ).values_list("fcm_device_token", flat=True)
        )
        user_id_for_obj = list(
            Profile.objects.filter(
                loyalty_preference_status=True,
                fcm_device_token__isnull=False,
                user_domain=user_domain,
            ).values_list("user_id", flat=True)
        )
    if data == "Promotions":
        registration_tokens = list(
            Profile.objects.filter(
                promotion_preference_status=True,
                fcm_device_token__isnull=False,
                user_domain=user_domain,
            ).values_list("fcm_device_token", flat=True)
        )
        user_id_for_obj = list(
            Profile.objects.filter(
                promotion_preference_status=True,
                fcm_device_token__isnull=False,
                user_domain=user_domain,
            ).values_list("user_id", flat=True)
        )
    if data == "Default Notification Screen":
        registration_tokens = list(
            Profile.objects.filter(
                fcm_device_token__isnull=False, user_domain=user_domain
            ).values_list("fcm_device_token", flat=True)
        )
        user_id_for_obj = list(
            Profile.objects.filter(
                fcm_device_token__isnull=False, user_domain=user_domain
            ).values_list("user_id", flat=True)
        )

    return [registration_tokens, user_id_for_obj]


def common_preference_region(data, region):
    registration_tokens = []
    user_id_for_obj = []
    if data == "Loyalty":
        registration_tokens = list(
            Profile.objects.filter(
                loyalty_preference_status=True,
                fcm_device_token__isnull=False,
                region=region,
            ).values_list("fcm_device_token", flat=True)
        )
        user_id_for_obj = list(
            Profile.objects.filter(
                loyalty_preference_status=True,
                fcm_device_token__isnull=False,
                region=region,
            ).values_list("user_id", flat=True)
        )
    if data == "Promotions":
        registration_tokens = list(
            Profile.objects.filter(
                promotion_preference_status=True,
                fcm_device_token__isnull=False,
                region=region,
            ).values_list("fcm_device_token", flat=True)
        )
        user_id_for_obj = list(
            Profile.objects.filter(
                promotion_preference_status=True,
                fcm_device_token__isnull=False,
                region=region,
            ).values_list("user_id", flat=True)
        )
    if data == "Default Notification Screen":
        registration_tokens = list(
            Profile.objects.filter(
                fcm_device_token__isnull=False, region=region
            ).values_list("fcm_device_token", flat=True)
        )
        user_id_for_obj = list(
            Profile.objects.filter(
                fcm_device_token__isnull=False, region=region
            ).values_list("user_id", flat=True)
        )

    return [registration_tokens, user_id_for_obj]


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=NOTIFICATION_CONST)
def send_push_notification_now(request, id):
    """this function is used to send push notification now"""
    try:
        baseURL = config("DJANGO_APP_BLOB_STORAGE_URL")
        old_data = audit_data_formatter(PUSH_NOTIFICATION_CONST, id)
        inapp_notification_object = (
            PushNotifications.objects.filter(id=id).values().first()
        )

        if inapp_notification_object["assign_to"] == "All App Users":
            data = common_preference(inapp_notification_object["screens"])
            registration_tokens = data[0]
            user_id_for_obj = data[1]
            if user_id_for_obj:
                success_count = send_push(
                    inapp_notification_object["subject"],
                    inapp_notification_object["description"],
                    registration_tokens,
                    baseURL + inapp_notification_object["image"],
                    inapp_notification_object["screens"],
                    inapp_notification_object["inapp_notification"]
                )
                if success_count:
                    send_push_for_each(
                        user_id_for_obj, inapp_notification_object, id
                    )
            else:
                PushNotifications.objects.filter(id=id).update(
                    status=FAILED,
                )
        elif inapp_notification_object["assign_to"] == "EV User":
            ev_data = common_preference_ev_user(
                inapp_notification_object["screens"]
            )
            registration_tokens = ev_data[0]
            user_id_for_obj = ev_data[1]
            if user_id_for_obj:
                success_count = send_push(
                    inapp_notification_object["subject"],
                    inapp_notification_object["description"],
                    registration_tokens,
                    baseURL + inapp_notification_object["image"],
                    inapp_notification_object["screens"],
                    inapp_notification_object["inapp_notification"]
                )
                if success_count:
                    send_push_for_each(
                        user_id_for_obj, inapp_notification_object, id
                    )
            else:
                PushNotifications.objects.filter(id=id).update(
                    status=DELIVERED,
                    delivered_time=timezone.localtime(timezone.now()).replace(
                        tzinfo=pytz.timezone("UTC")
                    ),
                )

        elif inapp_notification_object["assign_to"] == "Domain Specific":
            domain = inapp_notification_object["domain"]
            domain_data = common_preference_for_domain(
                inapp_notification_object["screens"], domain
            )
            registration_tokens = domain_data[0]
            user_id_for_obj = domain_data[1]
            if user_id_for_obj:
                success_count = send_push(
                    inapp_notification_object["subject"],
                    inapp_notification_object["description"],
                    registration_tokens,
                    baseURL + inapp_notification_object["image"],
                    inapp_notification_object["screens"],
                    inapp_notification_object["inapp_notification"]
                )
                if success_count:
                    send_push_for_each(
                        user_id_for_obj, inapp_notification_object, id
                    )
            else:
                PushNotifications.objects.filter(id=id).update(
                    status=FAILED,
                )

        else:
            regions_string = inapp_notification_object["regions"]
            regions_array = list(map(str.strip, regions_string.split(",")))
            success=0
            for region in regions_array:
                region_data = common_preference_region(
                    inapp_notification_object["screens"], region
                )
                registration_tokens = region_data[0]
                user_id_for_obj = region_data[1]
                if user_id_for_obj:
                    success_count = send_push(
                        inapp_notification_object["subject"],
                        inapp_notification_object["description"],
                        registration_tokens,
                        baseURL + inapp_notification_object["image"],
                        inapp_notification_object["screens"],
                        inapp_notification_object["inapp_notification"]
                    )
                    if success_count:
                        success += 1
                        send_push_for_each(
                            user_id_for_obj, inapp_notification_object, id
                        )
            if not success:
                PushNotifications.objects.filter(id=id).update(
                    status=FAILED,
                )

        new_data = audit_data_formatter(PUSH_NOTIFICATION_CONST, id)

        if old_data != new_data:
            add_audit_data(
                request.user,
                f"{id}, {PushNotifications.objects.get(id=id).subject}",
                f"{NOTIFICATION_CONST}-{id}",
                AUDIT_UPDATE_CONSTANT,
                FCM_NOTIFICATION,
                new_data,
                old_data,
            )
        return redirect("notifications_list")
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=NOTIFICATION_CONST)
def schedule_push_notification(request, id):
    """this function updates the scheduled date for push notification"""
    try:
        if request.method == "POST":
            if (
                request.POST.get("schedule_date") == ""
                or request.POST.get("schedule_time") == ""
            ):
                return INVALID_DATE_TIME
            schedule_date_time_string = (
                request.POST.get("schedule_date")
                + " "
                + request.POST.get("schedule_time")
            )
            schedule_date_time = datetime.strptime(
                schedule_date_time_string, "%d/%m/%Y %H:%M"
            ).replace(tzinfo=pytz.timezone("UTC"))
            if schedule_date_time < timezone.localtime(timezone.now()):
                return INVALID_DATE_TIME
            old_data = audit_data_formatter(PUSH_NOTIFICATION_CONST, id)
            PushNotifications.objects.filter(id=id).update(
                scheduled_time=schedule_date_time,
                status=SCHEDULED,
                updated_by=request.user.full_name,
            )
            new_data = audit_data_formatter(PUSH_NOTIFICATION_CONST, id)
            if old_data != new_data:
                add_audit_data(
                    request.user,
                    f"{id}, {PushNotifications.objects.get(id=id).subject}",
                    f"{NOTIFICATION_CONST}-{id}",
                    AUDIT_UPDATE_CONSTANT,
                    FCM_NOTIFICATION,
                    new_data,
                    old_data,
                )
            return JsonResponse({"status": 200, "message": "success"})
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


def get_push_notification_base_configuration():
    """push notifications base configurations"""
    list_of_category = ast.literal_eval(
        filter_function_for_base_configuration(
            LIST_OF_CATEGORY, DEFAULT_LIST_OF_CATEGORY
        )
    )

    list_of_assign_to = ast.literal_eval(
        filter_function_for_base_configuration(
            LIST_OF_ASSIGN_TO, DEFAULT_LIST_OF_ASSIGN_TO
        )
    )

    list_of_screens = ast.literal_eval(
        filter_function_for_base_configuration(
            SCREEN_NAME_FOR_PUSH_NOTIFICATION, DEFAULT_LIST_OF_SCREENS
        )
    )
    return [list_of_category, list_of_assign_to, list_of_screens]


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=NOTIFICATION_CONST)
def add_new_push_notification(request):
    """this functions add new push notification"""
    try:
        (
            list_of_category,
            list_of_assign_to,
            list_of_screens,
        ) = get_push_notification_base_configuration()

        user_domain = (
            Profile.objects.filter()
            .values_list("user_domain", flat=True)
            .distinct()
        )
        station_for_filteration = Stations.objects.filter(
            deleted=NO, region__isnull=False
        )
        list_of_regions = (
            station_for_filteration.values_list("region", flat=True)
            .distinct()
            .exclude(region="")
        )

        if request.method == "POST":
            image = request.POST.get("image")
            image_image = "images/notification-logo.png"
            if image_image not in image:
                image_data = image_converter(image)
                if (
                    image_data[2] > 700
                    or image_data[3] > 1400
                    or image_data[2] < 400
                    or image_data[3] < 700
                ):
                    image = optimize_image(
                        image_data[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
                        request.POST.get("subject-input")
                        + randon_string_generator()
                        + "."
                        + image_data[1],
                        EV_NOTIFICATION_IMAGE,
                    )
            else:
                image = "images/notification-logo.png"

            inapp_notification_object = PushNotifications.objects.create(
                subject=request.POST.get("subject-input"),
                description=request.POST.get("description-input"),
                screens=request.POST.get("screens-input"),
                category=request.POST.get("category"),
                assign_to=request.POST.get("assign_to"),
                regions=request.POST.get("regions"),
                created_date=timezone.localtime(timezone.now()),
                updated_date=timezone.localtime(timezone.now()),
                updated_by=request.user.full_name,
                status=DRAFT,
                push_notification=request.POST.get("push_notification"),
                inapp_notification=request.POST.get("inapp_notification"),
                image=image,
                domain=request.POST.get("domain"),
            )
            new_data = audit_data_formatter(
                PUSH_NOTIFICATION_CONST, inapp_notification_object.id
            )
            # Maintaining log in audit trail
            add_audit_data(
                request.user,
                (
                    str(inapp_notification_object.id)
                    + ", "
                    + inapp_notification_object.subject
                ),
                f"{NOTIFICATION_CONST}-{inapp_notification_object.id}",
                AUDIT_ADD_CONSTANT,
                FCM_NOTIFICATION,
                new_data,
                None,
            )
            return JsonResponse(
                status=200, data={"id": inapp_notification_object.id}
            )

        context = {
            "data": filter_url(
                request.user.role_id.access_content.all(), NOTIFICATION_CONST
            ),
            "page_name": ADD_NEW_PUSH_NOTIFICATION,
            "list_of_category": list_of_category,
            "list_of_assign_to": list_of_assign_to,
            "key": "add url",
            "list_of_screens": list_of_screens,
            "list_of_regions": list_of_regions,
            "user_domain": user_domain,
        }

        return render(
            request, "notifications/add_push_notification_form.html", context
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=NOTIFICATION_CONST)
def view_push_notification(request, id):
    """this function deals with details of an push notification"""
    try:
        push_notification_data = PushNotifications.objects.get(id=id)
        context = {
            "data": filter_url(
                request.user.role_id.access_content.all(), NOTIFICATION_CONST
            ),
            "push_notification_data": push_notification_data,
            "get_push_notification_image": push_notification_data.get_push_notification_image(),
            "page_name": VIEW_PUSH_NOTIFICATION,
        }
        return render(
            request,
            "notifications/view_push_notification.html",
            context,
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=NOTIFICATION_CONST)
def draft_push_notification(request, id):
    """this function sets the status of Push and InApp notification as draft"""
    try:
        old_data = audit_data_formatter(PUSH_NOTIFICATION_CONST, id)
        PushNotifications.objects.filter(id=id).update(
            status=DRAFT,
            scheduled_time=None,
            updated_by=request.user.full_name,
        )
        new_data = audit_data_formatter(PUSH_NOTIFICATION_CONST, id)
        if old_data != new_data:
            add_audit_data(
                request.user,
                f"{id}, {PushNotifications.objects.get(id=id).subject}",
                f"{NOTIFICATION_CONST}-{id}",
                AUDIT_UPDATE_CONSTANT,
                FCM_NOTIFICATION,
                new_data,
                old_data,
            )
        return redirect("notifications_list")
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=NOTIFICATION_CONST)
def delete_push_notification(request, id):
    """this function is used to delete push notification"""
    try:
        push_notification = PushNotifications.objects.filter(id=id).first()
        old_data = audit_data_formatter(PUSH_NOTIFICATION_CONST, id)

        PushNotifications.objects.filter(id__exact=id).update(deleted=YES)
        add_audit_data(
            request.user,
            f"{id}, {push_notification.subject}",
            f"{NOTIFICATION_CONST}-{id}",
            AUDIT_DELETE_CONSTANT,
            FCM_NOTIFICATION,
            None,
            old_data,
        )
        return redirect("notifications_list")
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=NOTIFICATION_CONST)
def update_push_notification(request, id):
    """this function deals with updating the push notification"""
    try:
        region_list = []
        old_data = audit_data_formatter(PUSH_NOTIFICATION_CONST, id)
        baseURL_2 = config("DJANGO_APP_CDN_BASE_URL")

        # here we are getting the list of allowed file types ,
        #  template type list and user category list from Base configurations
        (
            list_of_category,
            list_of_assign_to,
            list_of_screens,
        ) = get_push_notification_base_configuration()
        user_domain = (
            Profile.objects.filter()
            .values_list("user_domain", flat=True)
            .distinct()
        )
        push_notification_data = PushNotifications.objects.get(id=id)
        if push_notification_data.regions:
            region_list = push_notification_data.regions.split(",")
        inapp_notification_status = (
            PushNotifications.objects.filter(id=id).first().inapp_notification
        )

        push_notification_status = (
            PushNotifications.objects.filter(id=id).first().push_notification
        )

        station_for_filteration = Stations.objects.filter(deleted=NO)

        list_of_regions = (
            station_for_filteration.values_list("region", flat=True)
            .distinct()
            .exclude(region="")
        )

        if request.method == "POST":
            IMAGE_image = PushNotifications.objects.filter(id=id).first().image
            if str(IMAGE_image) in request.POST.get("image") and IMAGE_image:
                push_notification_data.image = IMAGE_image
                push_notification_data.save()

            elif (
                request.POST.get("image")
                and IMAGE_image
                and IMAGE_image == "images/notification-logo.png"
            ):
                # dont remove previous image and directly save new image after optimization process
                image = request.POST.get("image")
                if baseURL_2 in request.POST.get("image"):
                    image = "images/notification-logo.png"
                    push_notification_data = get_object_or_404(
                        PushNotifications, id=id
                    )
                    push_notification_data.image = image
                    push_notification_data.save()
                else:
                    image_data = image_converter(image)
                    if (
                        image_data[2] > 700
                        or image_data[3] > 1400
                        or image_data[2] < 400
                        or image_data[3] < 700
                    ):
                        image = optimize_image(
                            image_data[
                                IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN
                            ],
                            request.POST.get("subject-input")
                            + randon_string_generator()
                            + "."
                            + image_data[1],
                            EV_NOTIFICATION_IMAGE,
                        )
                        push_notification_data = get_object_or_404(
                            PushNotifications, id=id
                        )
                        push_notification_data.image = image
                        push_notification_data.save()
            elif (
                request.POST.get("image")
                and IMAGE_image
                and IMAGE_image != "images/notification-logo.png"
            ):
                # remove previous image and save new image after optimization process
                if PushNotifications.objects.filter(id=id).first().image:
                    PushNotifications.objects.filter(
                        id=id
                    ).first().image.delete()
                    image = request.POST.get("image")
                    if image:
                        image_data = image_converter(image)
                        if (
                            image_data[2] > 700
                            or image_data[3] > 1400
                            or image_data[2] < 400
                            or image_data[3] < 700
                        ):
                            image = optimize_image(
                                image_data[
                                    IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN
                                ],
                                request.POST.get("subject-input")
                                + randon_string_generator()
                                + "."
                                + image_data[1],
                                EV_NOTIFICATION_IMAGE,
                            )
                            push_notification_data = get_object_or_404(
                                PushNotifications, id=id
                            )
                            push_notification_data.image = image
                            push_notification_data.save()

            else:
                image = "images/notification-logo.png"
                push_notification_data = get_object_or_404(
                    PushNotifications, id=id
                )
                push_notification_data.image = image
                push_notification_data.save()

            PushNotifications.objects.filter(id=id).update(
                subject=request.POST.get("subject-input"),
                description=request.POST.get("description-input"),
                screens=request.POST.get("screens-input"),
                category=request.POST.get("category"),
                assign_to=request.POST.get("assign_to"),
                regions=request.POST.get("regions", None),
                updated_date=timezone.localtime(timezone.now()),
                updated_by=request.user.full_name,
                push_notification=request.POST.get("push_notification"),
                inapp_notification=request.POST.get("inapp_notification"),
                domain=request.POST.get("domain"),
            )

            new_data = audit_data_formatter(PUSH_NOTIFICATION_CONST, id)
            if old_data != new_data:
                # maintain log in audit trail
                add_audit_data(
                    request.user,
                    f"{push_notification_data.id}, {push_notification_data.subject}",
                    f"{NOTIFICATION_CONST}-{id}",
                    AUDIT_UPDATE_CONSTANT,
                    PUSH_NOTIFICATION_CONST,
                    new_data,
                    old_data,
                )
            return JsonResponse(status=200, data={"id": id})

        context = {
            "data": filter_url(
                request.user.role_id.access_content.all(), NOTIFICATION_CONST
            ),
            "region_list": region_list,
            "push_notification_data": push_notification_data,
            "page_name": UPDATE_PUSH_NOTIFICATION,
            "list_of_category": list_of_category,
            "list_of_assign_to": list_of_assign_to,
            "get_push_notification_image": push_notification_data.get_push_notification_image(),
            "key": "update url",
            "inapp_notification_status": inapp_notification_status,
            "push_notification_status": push_notification_status,
            "list_of_screens": list_of_screens,
            "list_of_regions": list_of_regions,
            "user_domain": user_domain,
        }
        return render(
            request, "notifications/add_push_notification_form.html", context
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


def push_notification_data_collection_to_send_push_notification(
    scheduled_push_notification,
):
    """this function collect the data required to send Push and InApp notifications"""
    try:
        inapp_notification_object = (
            PushNotifications.objects.filter(id=scheduled_push_notification.id)
            .values()
            .first()
        )
        if scheduled_push_notification.assign_to == "All App Users":
            data = common_preference(inapp_notification_object["screens"])
            registration_tokens = data[0]
            user_id_for_obj = data[1]
            if user_id_for_obj:
                start_time = threading.Thread(
                    target=send_push,
                    args=[
                        scheduled_push_notification.subject,
                        scheduled_push_notification.description,
                        registration_tokens,
                        scheduled_push_notification.get_push_notification_image(),
                        scheduled_push_notification.screens,
                        scheduled_push_notification.inapp_notification,
                    ],
                    daemon=True
                )
                start_time.start()

        elif scheduled_push_notification.assign_to == "EV User":
            ev_data = common_preference_ev_user(
                inapp_notification_object["screens"]
            )
            registration_tokens = ev_data[0]
            user_id_for_obj = ev_data[1]
            if user_id_for_obj:
                start_time = threading.Thread(
                    target=send_push,
                    args=[
                        scheduled_push_notification.subject,
                        scheduled_push_notification.description,
                        registration_tokens,
                        scheduled_push_notification.get_push_notification_image(),
                        scheduled_push_notification.screens,
                        scheduled_push_notification.inapp_notification,
                    ],
                    daemon=True
                )
                start_time.start()
            else:
                PushNotifications.objects.filter(id=id).update(
                    status=DELIVERED,
                    delivered_time=timezone.localtime(timezone.now()).replace(
                        tzinfo=pytz.timezone("UTC")
                    ),
                )

        elif scheduled_push_notification.assign_to == "Domain Specific":
            domain = scheduled_push_notification.domain
            domain_data = common_preference_for_domain(
                inapp_notification_object["screens"], domain
            )
            registration_tokens = domain_data[0]
            user_id_for_obj = domain_data[1]
            if user_id_for_obj:
                start_time = threading.Thread(
                    target=send_push,
                    args=[
                        scheduled_push_notification.subject,
                        scheduled_push_notification.description,
                        registration_tokens,
                        scheduled_push_notification.get_push_notification_image(),
                        scheduled_push_notification.screens,
                        scheduled_push_notification.inapp_notification,
                    ],
                    daemon=True
                )
                start_time.start()
            else:
                PushNotifications.objects.filter(id=id).update(
                    status=DELIVERED,
                    delivered_time=timezone.localtime(timezone.now()).replace(
                        tzinfo=pytz.timezone("UTC")
                    ),
                )

        else:
            regions_string = scheduled_push_notification.regions
            regions_array = list(map(str.strip, regions_string.split(",")))
            for region in regions_array:
                region_data = common_preference_region(
                    inapp_notification_object["screens"], region
                )
                registration_tokens = region_data[0]
                user_id_for_obj = region_data[1]
                if user_id_for_obj:
                    start_time = threading.Thread(
                        target=send_push,
                        args=[
                            scheduled_push_notification.subject,
                            scheduled_push_notification.description,
                            registration_tokens,
                            scheduled_push_notification.get_push_notification_image(),
                            scheduled_push_notification.screens,
                            scheduled_push_notification.inapp_notification,
                        ],
                        daemon=True
                    )
                    start_time.start()

        PushNotifications.objects.filter(
            id=scheduled_push_notification.id
        ).update(
            status=DELIVERED,
            delivered_time=timezone.localtime(timezone.now()).replace(
                tzinfo=pytz.timezone("UTC")
            ),
        )

        push_notification_object_for_app = dict(
            PushNotifications.objects.filter(
                id=scheduled_push_notification.id, inapp_notification="true"
            )
            .values(
                "id",
                "subject",
                "description",
                "image",
                "delivered_time",
                "screens",
            )
            .first()
        )
        push_notification_object_for_app[
            "delivered_time"
        ] = push_notification_object_for_app["delivered_time"].strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
        push_notification_object_for_app["read_status"] = False
        for user_id in user_id_for_obj:
            inapp_notification_previous_object = (
                Profile.objects.filter(user_id=user_id)
                .values("inapp_notification_object")
                .first()
            )
            if (
                inapp_notification_previous_object["inapp_notification_object"]
                == None
            ):
                inapp_notification_new_object = array_to_string_converter(
                    [push_notification_object_for_app]
                )
            else:
                inapp_notification_new_object = array_to_string_converter(
                    (
                        [push_notification_object_for_app]
                        + string_to_array_converter(
                            inapp_notification_previous_object[
                                "inapp_notification_object"
                            ]
                        )
                    )
                )
            Profile.objects.filter(user_id=user_id).update(
                inapp_notification_object=inapp_notification_new_object
            )
    except Exception as error:
        print(error)


def filter_push_notifications_cron_job_function():
    """this function initiates the scheduled push notification sending
    process after geting all the valid push notifications"""
    try:
        scheduled_push_notifications = PushNotifications.objects.filter(
            deleted=NO,
            delivered_time=None,
            scheduled_time__lte=timezone.localtime(timezone.now()).replace(
                tzinfo=pytz.timezone("UTC")
            ),
        )
        if scheduled_push_notifications:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=20
            ) as executor:
                executor.map(
                    push_notification_data_collection_to_send_push_notification,
                    list(scheduled_push_notifications),
                )
    except Exception as error:
        print(error)

