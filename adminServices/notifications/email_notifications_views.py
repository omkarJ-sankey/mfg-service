#  File details-
#   Author      - Shivkumar Kumbhar
#   Description - This file is mainly focused on showing and handling Notifications
#   Name        - Notification View
#   Modified by - Shivkumar Kumbhar
#   last modified - 18/04/23

# These are all the imports that we are exporting from
# different module's from project or library.

#pylint:disable=import-error
import threading
from datetime import datetime
import pytz
import json
import ast
import concurrent.futures
from decouple import config
from cryptography.fernet import Fernet

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_http_methods


from sharedServices.common import (
    filter_url,
    order_by_function,
    pagination_and_filter_func,
    hasher,
    email_validator,
    array_to_string_converter,
    string_to_array_converter,
    filter_function_for_base_configuration,
    search_validator,
)

from sharedServices.common_audit_trail_functions import (
    add_audit_data,
    audit_data_formatter,
)
from sharedServices.email_common_functions import email_sender
from sharedServices.constants import (
    NOTIFICATION_CONST,
    COMMON_ERRORS,
    ERROR_TEMPLATE_URL,
    LIST_OF_ALLOWED_EXTENSION,
    EMAIL_NOTIFICATION_TOTAL_FILE_SIZE_LIMIT,
    ACCEPT_EXTENSION,
    GET_METHOD_ALLOWED,
    POST_METHOD_ALLOWED,
    USER_CATEGORY_LIST,
    LIST_OF_EMAIL_PREFERENCE,
    INVALID_DATE_TIME,
    YES,
    NO,
    AUDIT_ADD_CONSTANT,
    AUDIT_UPDATE_CONSTANT,
    AUDIT_DELETE_CONSTANT,
    DEFAULT_ACCEPT_EXTENSION,
    DEFAULT_EMAIL_NOTIFICATION_TOTAL_FILE_SIZE_LIMIT,
    DEFAULT_USER_CATEGORY_LIST,
    DEFAULT_LIST_OF_EMAIL_PREFERENCE,
    DEFAULT_LIST_OF_ALLOWED_EXTENSION,
    NOTIFICATION_STATUS_LIST,
    DEFAULT_NOTIFICATION_STATUS_LIST,
    REQUEST_API_TIMEOUT,
    GET_REQUEST,
)
from sharedServices.decorators import allowed_users, authenticated_user
from sharedServices.sentry_tracers import traced_request
from adminServices.configurations.app_level_constants import (
    DELIVERED,
    SCHEDULED,
    ADD_NEW_EMAIL_NOTIFICATION,
    UPDATE_EMAIL_NOTIFICATION,
    DRAFT,
    FAILED,
    EMAIL_NOTIFICATION,
    IN_PROGRESS,
    FAILED,
    UNSUBSCRIBE_EMAIL,
)
from sharedServices.model_files.notifications_module_models import (
    EmailNotifications,
    EmailAttachments,
)

from sharedServices.model_files.app_user_models import MFGUserEV, Profile
from .forms import EmailDescription

""" view starts here """


def send_downtime_updates_via_mail(*args):
    """this function is used to send downtime updates to app users"""
    (
        email_notification_data,
        attachment_files,
    ) = args
    try:
        all_users = MFGUserEV.objects.filter(
            ~Q(user_email="") & ~Q(user_profile=None),
        )
        postcode_specific_users = []
        if (
            email_notification_data.assign_to == "Postcode Specific"
            and email_notification_data.postcode
        ):
            for user in all_users:
                if user.key:
                    decrypter = Fernet(user.key)
                    post_code = decrypter.decrypt(user.post_code).decode()
                    if (
                        str(post_code)
                        .lower()
                        .startswith(email_notification_data.postcode)
                    ):
                        postcode_specific_users.append(user)
        users = (
            all_users.filter(
                user_email__in=[
                    hasher(email)
                    for email in string_to_array_converter(
                        email_notification_data.user_list
                    )
                ]
            )
            if (
                email_notification_data.assign_to == "Specific Users"
                and email_notification_data.user_list
            )
            else postcode_specific_users
            if (
                email_notification_data.assign_to == "Postcode Specific"
                and email_notification_data.postcode
            )
            else all_users
        )
        if email_notification_data.email_preference == "Marketing Update":
            users = list(
                filter(
                    lambda user: user.user_profile.email_marketing_update_preference_status
                    is True,
                    users,
                )
            )
        elif email_notification_data.email_preference == "News Letter":
            users = list(
                filter(
                    lambda user: user.user_profile.email_news_letter_preference_status
                    is True,
                    users,
                )
            )
        elif email_notification_data.email_preference == "Promotions":
            users = list(
                filter(
                    lambda user: user.user_profile.email_promotion_preference_status
                    is True,
                    users,
                )
            )
        elif email_notification_data.email_preference == "EV Updates":
            users = list(
                filter(
                    lambda user: user.user_profile.email_ev_updates_preference_status
                    is True,
                    users,
                )
            )
        send_downtime_updates_via_mail.flag_of_first_success = False

        def send_email_notifications(user):
            """this function send downtime mail to users"""
            try:
                decrypter = Fernet(user.key)
                user_first_name = decrypter.decrypt(user.first_name).decode()
                user_email = decrypter.decrypt(user.encrypted_email).decode()
                to_emails = [
                    (
                        user_email,
                        user_first_name,
                        email_notification_data.subject,
                    )
                ]
                dynamic_data = {}

                template_id = config("DJANGO_APP_CUSTOM_EMAIL_TEMPLATE_ID")
                dynamic_data = {
                    "user_name": user_first_name,
                    "custom_body": email_notification_data.description,
                    "subject": email_notification_data.subject,
                }
                if (
                    email_sender(
                        template_id,
                        to_emails,
                        dynamic_data,
                        attachment_files,
                    )
                    and send_downtime_updates_via_mail.flag_of_first_success
                    is False
                ):
                    send_downtime_updates_via_mail.flag_of_first_success = True

            except COMMON_ERRORS as exception:
                print(exception)

        # here the number of users to whom email will be sent at a time is defined
        if len(users):
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=50
            ) as executor:
                executor.map(
                    send_email_notifications,
                    users,
                )
            if send_downtime_updates_via_mail.flag_of_first_success is True:
                # updating the dilevery status
                EmailNotifications.objects.filter(
                    id=email_notification_data.id
                ).update(
                    status=DELIVERED,
                    delivered_time=timezone.localtime(timezone.now()).replace(
                        tzinfo=pytz.timezone("UTC")
                    ),
                )
            else:
                EmailNotifications.objects.filter(
                    id=email_notification_data.id
                ).update(
                    status=FAILED,
                )
        else:
            EmailNotifications.objects.filter(
                id=email_notification_data.id
            ).update(
                status=DELIVERED,
                delivered_time=timezone.localtime(timezone.now()).replace(
                    tzinfo=pytz.timezone("UTC")
                ),
            )

    except COMMON_ERRORS as exception:
        print(exception)
    return None


def email_data_collection_to_send_email(scheduled_email):
    """this function collect the data required to send email notifications"""

    # getting all the email attachments paths from db and extracting filename from
    # it and passing dictionary to email sending function where key is filename
    # and value is file taken from Azure blob
    attachments_paths = scheduled_email.email_attachments.filter(deleted=NO)
    dict_of_file_from_blob = {}
    for attachment_path in attachments_paths:
        # request to blob for file using the partial path in db
        file_from_blob = traced_request(
            GET_REQUEST,
            f"{config('DJANGO_APP_BLOB_STORAGE_URL')}"
            + str(attachment_path.attachment),
            timeout=REQUEST_API_TIMEOUT
        )
        if file_from_blob.status_code == 200:
            dict_of_file_from_blob.update(
                {
                    str(attachment_path.attachment).split("images/")[
                        1
                    ]: file_from_blob.content
                }
            )
    # calling the email sender function
    start_time = threading.Thread(
        target=send_downtime_updates_via_mail,
        args=[
            scheduled_email,
            dict_of_file_from_blob,
        ],
        daemon=True
    )
    start_time.start()


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=NOTIFICATION_CONST)
def email_list_func(request):
    """this functions creates list of email notifications"""
    try:
        query_params_str = ""
        for q_param in request.GET:
            if len(query_params_str) == 0:
                query_params_str = f"?{q_param}={request.GET.get(q_param)}"
            else:
                query_params_str += f"&{q_param}={request.GET.get(q_param)}"

        # Database call to promotions.
        email_notifications = EmailNotifications.objects.filter(
            deleted=NO
        ).order_by("-id")

        # Declaration of all query params that helps in filtering
        # data and pagination.
        page_num = request.GET.get("page", 1)
        status = request.GET.get("status", None)
        assign_to = request.GET.get("assign_to", None)
        search = request.GET.get("search", "")
        search = search_validator(search)
        order_by_scheduled_time = request.GET.get(
            "order_by_scheduled_time", None
        )
        order_by_delivered_time = request.GET.get(
            "order_by_delivered_time", None
        )
        ordered_email_notifications = order_by_function(
            email_notifications,
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
        email_notifications = ordered_email_notifications["ordered_table"]

        # Here pagination_and_filter_func() is the common function to provide
        # filteration and pagination.
        filtered_data_emails = pagination_and_filter_func(
            page_num,
            email_notifications,
            [
                {
                    "search": search,
                    "search_array": ["subject__icontains"],
                },
                {"status__exact": status},
                {"assign_to__exact": assign_to},
            ],
        )

        # Here filter_url() function is used to filter
        # navbar elements so that we can  render only those navbar tabs
        # to which logged in user have access.
        url_data = filter_url(
            request.user.role_id.access_content.all(), NOTIFICATION_CONST
        )
        user_category_list = ast.literal_eval(
            filter_function_for_base_configuration(
                USER_CATEGORY_LIST, DEFAULT_USER_CATEGORY_LIST
            )
            
        )
        status_list = ast.literal_eval(
            filter_function_for_base_configuration(
                NOTIFICATION_STATUS_LIST, DEFAULT_NOTIFICATION_STATUS_LIST
            ))

        # Response to the request
        return render(
            request,
            "notifications/email_list.html",
            context={
                "data": url_data,
                "email_listing_data": EmailNotifications.objects.filter(
                    deleted=NO
                ),
                "active_tab": "Email",
                "emails": filtered_data_emails["filtered_table"],
                "data_count": filtered_data_emails["data_count"],
                "first_data_number": filtered_data_emails[
                    "first_record_number"
                ],
                "last_data_number": filtered_data_emails["last_record_number"],
                "pagination_num_list": filtered_data_emails["number_list"],
                "user_category_list": user_category_list,
                "status_list": status_list,
                "query_params_str": query_params_str,
                "prev_search": search,
                "prev_status": status,
                "prev_assign_to": assign_to,
                "prev": filtered_data_emails["prev_page"],
                "next": filtered_data_emails["next_page"],
                "update_url_param": filtered_data_emails["url"]
                + ordered_email_notifications["url"],
                "current_page": int(page_num),
                "previous_order_by_scheduled_time": order_by_scheduled_time,
                "previous_order_by_delivered_time": order_by_delivered_time,
            },
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


def get_email_notification_base_configuration():
    """email notifications base configurations"""

    list_of_allowed_file_types = ast.literal_eval(
        filter_function_for_base_configuration(
            LIST_OF_ALLOWED_EXTENSION, DEFAULT_LIST_OF_ALLOWED_EXTENSION
        )
    )

    accept_extension = filter_function_for_base_configuration(
        ACCEPT_EXTENSION, DEFAULT_ACCEPT_EXTENSION
    )
    email_notification_total_file_size_limit = (
        filter_function_for_base_configuration(
            EMAIL_NOTIFICATION_TOTAL_FILE_SIZE_LIMIT,
            DEFAULT_EMAIL_NOTIFICATION_TOTAL_FILE_SIZE_LIMIT,
        )
    )

    user_category_list = ast.literal_eval(
        filter_function_for_base_configuration(
            USER_CATEGORY_LIST, DEFAULT_USER_CATEGORY_LIST
        )
    )

    list_of_email_preference = ast.literal_eval(
        filter_function_for_base_configuration(
            LIST_OF_EMAIL_PREFERENCE, DEFAULT_LIST_OF_EMAIL_PREFERENCE
        )
    )
    return [
        list_of_allowed_file_types,
        accept_extension,
        email_notification_total_file_size_limit,
        user_category_list,
        list_of_email_preference,
    ]


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=NOTIFICATION_CONST)
def add_new_email_notification(add_email_notification_request):
    """this functions add new email notification"""

    discription_form = EmailDescription
    # here we are getting the list of allowed file types ,
    # list and user category list from Base configurations
    (
        list_of_allowed_file_types,
        accept_extension,
        email_notification_total_file_size_limit,
        user_category_list,
        list_of_email_preference,
    ) = get_email_notification_base_configuration()

    custom_body = None
    attachment_files = []
    email_preference = None

    # getting data from front end

    if add_email_notification_request.method == "POST":
        email_subject = add_email_notification_request.POST.get(
            "email_subject", None
        )
        custom_body = add_email_notification_request.POST.get(
            "custom_template_body", None
        )
        email_preference = add_email_notification_request.POST.get(
            "email_preference", None
        )
        user_list = add_email_notification_request.POST.get(
            "user_email_list", None
        )
        postcode = add_email_notification_request.POST.get("postcode", None)
        if user_list:
            user_list = array_to_string_converter(json.loads(user_list))
        if add_email_notification_request.FILES.getlist("files"):
            attachment_files = add_email_notification_request.FILES.getlist(
                "files"
            )
        if (
            add_email_notification_request.POST.get("user_category")
            not in user_category_list
        ):
            return render("add_new_email_notification")
        email_notification_object = EmailNotifications.objects.create(
            assign_to=add_email_notification_request.POST.get("user_category"),
            subject=email_subject,
            description=custom_body,
            created_date=timezone.localtime(timezone.now()),
            updated_date=timezone.localtime(timezone.now()),
            updated_by=add_email_notification_request.user.full_name,
            status=DRAFT,
            email_preference=email_preference,
            user_list=user_list,
            postcode=str(postcode).lower() if postcode else postcode,
        )
        if attachment_files:
            for file in attachment_files:
                email_notification_object.email_attachments.create(
                    attachment=file, attachment_size=file.size
                )

        new_data = audit_data_formatter(
            NOTIFICATION_CONST, email_notification_object.id
        )
        # Maintaining log in audit trail
        add_audit_data(
            add_email_notification_request.user,
            (
                str(email_notification_object.id)
                + ", "
                + email_notification_object.subject
            ),
            f"{NOTIFICATION_CONST}-{email_notification_object.id}",
            AUDIT_ADD_CONSTANT,
            EMAIL_NOTIFICATION,
            new_data,
            None,
        )
        return JsonResponse(
            status=200, data={"id": str(email_notification_object.id)}
        )
    context = {
        "data": filter_url(
            add_email_notification_request.user.role_id.access_content.all(),
            NOTIFICATION_CONST,
        ),
        "discription_form": discription_form,
        "user_category_list": user_category_list,
        "list_of_email_preference": list_of_email_preference,
        "list_of_allowed_file_types": json.dumps(list_of_allowed_file_types),
        "accept_extension": accept_extension,
        "email_notification_total_file_size_limit": email_notification_total_file_size_limit,
        "page_name": ADD_NEW_EMAIL_NOTIFICATION,
    }
    return render(
        add_email_notification_request,
        "notifications/add_email_notification_form.html",
        context,
    )


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=NOTIFICATION_CONST)
def update_email_notification(request, id):
    """this function deals with updating the email notification"""

    email_notification_data = EmailNotifications.objects.get(id=id)
    # for ck-editor data
    discription_form = EmailDescription(instance=email_notification_data)

    lst_of_attachments_objects_for_update_page = (
        email_notification_data.email_attachments.filter(deleted=NO)
    )
    # getting listg of attachment urls
    lst_of_attachments_for_update_page = [
        {
            attachment.id: attachment.get_attachment(),
            "size": attachment.attachment_size,
        }
        for attachment in lst_of_attachments_objects_for_update_page
    ]

    # here we are getting the list of allowed file types ,
    (
        list_of_allowed_file_types,
        accept_extension,
        email_notification_total_file_size_limit,
        user_category_list,
        list_of_email_preference,
    ) = get_email_notification_base_configuration()
    old_data = audit_data_formatter(NOTIFICATION_CONST, id)

    if request.method == "POST":
        if request.POST.get("user_category") not in user_category_list:
            return render("update_email_notification")
        if request.POST.get("existing_file_array_with_url"):
            id_of_existing_file_array_with_url = [
                int(list(each_object)[0])
                for each_object in json.loads(
                    request.POST.get("existing_file_array_with_url")
                )
            ]
            # delete the missing file on basis of returned array from front end
            EmailAttachments.objects.filter(
                ~Q(id__in=id_of_existing_file_array_with_url),
                emailnotifications__id=email_notification_data.id,
            ).update(deleted=YES)
        user_list = request.POST.get("user_email_list", None)
        postcode = request.POST.get("postcode", None)

        if user_list:
            user_list = array_to_string_converter(json.loads(user_list))
        EmailNotifications.objects.filter(id=id).update(
            assign_to=request.POST.get("user_category"),
            subject=request.POST.get("email_subject"),
            description=request.POST.get("custom_template_body"),
            updated_date=timezone.localtime(timezone.now()),
            updated_by=request.user.full_name,
            email_preference=request.POST.get("email_preference"),
            user_list=user_list,
            postcode=str(postcode).lower() if postcode else postcode,
        )
        if request.FILES.getlist("files"):
            for file in request.FILES.getlist("files"):
                email_notification_data.email_attachments.create(
                    attachment=file, attachment_size=file.size
                )

        new_data = audit_data_formatter(NOTIFICATION_CONST, id)
        if old_data != new_data:
            # maintain log in audit trail
            add_audit_data(
                request.user,
                f"{email_notification_data.id}, {email_notification_data.subject}",
                f"{NOTIFICATION_CONST}-{id}",
                AUDIT_UPDATE_CONSTANT,
                EMAIL_NOTIFICATION,
                new_data,
                old_data,
            )

        return JsonResponse(status=200, data={"id": str(id)})

    context = {
        "data": filter_url(
            request.user.role_id.access_content.all(), NOTIFICATION_CONST
        ),
        "user_category_list": user_category_list,
        "list_of_email_preference": list_of_email_preference,
        "email_notification_data": email_notification_data,
        "discription_form": discription_form,
        "lst_of_attachments_for_update_page": json.dumps(
            lst_of_attachments_for_update_page
        ),
        "list_of_allowed_file_types": json.dumps(list_of_allowed_file_types),
        "accept_extension": accept_extension,
        "page_name": UPDATE_EMAIL_NOTIFICATION,
        "email_notification_total_file_size_limit": email_notification_total_file_size_limit,
        "users_list": json.dumps(
            string_to_array_converter(email_notification_data.user_list)
        )
        if email_notification_data.user_list
        else None,
    }
    return render(
        request, "notifications/add_email_notification_form.html", context
    )


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=NOTIFICATION_CONST)
def view_email_notification(request, id):
    """this function deals with details of an email notification"""
    try:
        email_notification_data = EmailNotifications.objects.get(id=id)
        # get all attachments associated with this email notifications
        lst_of_attachments_for_update_page = list(
            email_notification_data.email_attachments.filter(
                deleted=NO
            ).values_list("attachment", flat=True)
        )
        json_files_list = json.dumps(lst_of_attachments_for_update_page)
        status_to_restrict_navigation = [DELIVERED, IN_PROGRESS]
        context = {
            "data": filter_url(
                request.user.role_id.access_content.all(), NOTIFICATION_CONST
            ),
            "email_notification_object": email_notification_data,
            "json_files_list": json_files_list,
            "status_to_restrict_navigation": status_to_restrict_navigation,
            "user_list": (
                string_to_array_converter(email_notification_data.user_list)
                if email_notification_data.user_list
                else None
            ),
        }
        return render(
            request,
            "notifications/view_email_notification.html",
            context,
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=NOTIFICATION_CONST)
def delete_email_notification(request, id):
    """this function is used to delete an email notification"""
    email_notification = EmailNotifications.objects.filter(id=id).first()
    old_data = audit_data_formatter(NOTIFICATION_CONST, id)
    EmailAttachments.objects.filter(emailnotifications__id=id).update(
        deleted=YES
    )
    EmailNotifications.objects.filter(id__exact=id).update(deleted=YES)
    add_audit_data(
        request.user,
        f"{id}, {email_notification.subject}",
        f"{NOTIFICATION_CONST}-{id}",
        AUDIT_DELETE_CONSTANT,
        EMAIL_NOTIFICATION,
        None,
        old_data,
    )
    return redirect("email_list")


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=NOTIFICATION_CONST)
def unsubscribe_to_email_notification(request):
    try:
        if request.method == "POST":
            data = json.loads(request.body.decode("utf-8"))
            if not email_validator(data["email"]):
                return JsonResponse(
                    {
                        "response": {
                            "status": False,
                            "message": "Invalid user emailID",
                        }
                    }
                )
            hashed_email = hasher(data["email"])
            if not MFGUserEV.objects.filter(user_email=hashed_email).first():
                return JsonResponse(
                    {
                        "response": {
                            "status": False,
                            "message": "Invalid user emailID",
                        }
                    }
                )
            elif Profile.objects.filter(
                user_id__user_email=hashed_email,
                email_marketing_update_preference_status=False,
                email_news_letter_preference_status=False,
                email_promotion_preference_status=False,
                email_ev_updates_preference_status=False,
            ).first():
                return JsonResponse(
                    {
                        "response": {
                            "status": False,
                            "message": "This User is already Unsubscribed",
                        }
                    }
                )
            else:
                updated_user = Profile.objects.filter(
                    user_id__user_email=hashed_email
                )
                if updated_user:
                    updated_user.update(
                        updated_by=request.user.full_name,
                        email_marketing_update_preference_status=False,
                        email_news_letter_preference_status=False,
                        email_promotion_preference_status=False,
                        email_ev_updates_preference_status=False,
                    )
                add_audit_data(
                    request.user,
                    str(updated_user.first().user.id),
                    "Unsubscribe",
                    AUDIT_UPDATE_CONSTANT,
                    UNSUBSCRIBE_EMAIL,
                    array_to_string_converter(
                        [
                            {
                                "unsubscribe status": YES,
                                "unsubscribed users": str(
                                    updated_user.first().user.id
                                ),
                            }
                        ]
                    ),
                    None,
                )
                return JsonResponse(
                    {
                        "response": {
                            "status": True,
                            "message": "User unsubscribed successfully",
                        }
                    }
                )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=NOTIFICATION_CONST)
def schedule_email_notification(request, id):
    """this function updates the scheduled date for email notification"""
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
            if schedule_date_time < timezone.localtime(timezone.now()).replace(
                tzinfo=pytz.timezone("UTC")
            ):
                return INVALID_DATE_TIME
            old_data = audit_data_formatter(NOTIFICATION_CONST, id)
            EmailNotifications.objects.filter(id=id).update(
                scheduled_time=schedule_date_time,
                status=SCHEDULED,
            )
            new_data = audit_data_formatter(NOTIFICATION_CONST, id)
            if old_data != new_data:
                add_audit_data(
                    request.user,
                    f"{id}, {EmailNotifications.objects.get(id=id).subject}",
                    f"{NOTIFICATION_CONST}-{id}",
                    AUDIT_UPDATE_CONSTANT,
                    EMAIL_NOTIFICATION,
                    new_data,
                    old_data,
                )
            return JsonResponse({"status": 200, "message": "success"})
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=NOTIFICATION_CONST)
def draft_email_notification(request, id):
    """this function sets the status of email notification as draft"""
    old_data = audit_data_formatter(NOTIFICATION_CONST, id)
    EmailNotifications.objects.filter(id=id).update(
        status=DRAFT, scheduled_time=None
    )
    new_data = audit_data_formatter(NOTIFICATION_CONST, id)
    if old_data != new_data:
        add_audit_data(
            request.user,
            f"{id}, {EmailNotifications.objects.get(id=id).subject}",
            f"{NOTIFICATION_CONST}-{id}",
            AUDIT_UPDATE_CONSTANT,
            EMAIL_NOTIFICATION,
            new_data,
            old_data,
        )
    return redirect("email_list")


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=NOTIFICATION_CONST)
def validate_user_email(request):
    if request.method == "POST":
        email = json.loads(request.body.decode("utf-8"))["email"]
        if (
            not email_validator(email)
            or not MFGUserEV.objects.filter(
                user_email=hasher(email)
            ).first()
        ):
            return JsonResponse(
                {
                    "status": False,
                    "message": "User with this email does not exist",
                }
            )
        return JsonResponse(
            {
                "status": True,
                "message": "Email is valid",
            }
        )


def filter_email_notifications_cron_job_function():
    """this function initiates the scheduled email sending
    process after geting all the valid email notifications"""
    scheduled_emails = EmailNotifications.objects.filter(
        deleted=NO,
        delivered_time=None,
        scheduled_time__lte=timezone.localtime(timezone.now()).replace(
            tzinfo=pytz.timezone("UTC")
        ),
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(
            email_data_collection_to_send_email,
            list(scheduled_emails),
        )


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=NOTIFICATION_CONST)
def send_email_notification_now(request, id):
    """this function is used to send email notification now"""
    try:
        old_data = audit_data_formatter(NOTIFICATION_CONST, id)
        EmailNotifications.objects.filter(id__exact=id).update(
            scheduled_time=None, status=IN_PROGRESS
        )
        new_data = audit_data_formatter(NOTIFICATION_CONST, id)
        if old_data != new_data:
            add_audit_data(
                request.user,
                f"{id}, {EmailNotifications.objects.get(id=id).subject}",
                f"{NOTIFICATION_CONST}-{id}",
                AUDIT_UPDATE_CONSTANT,
                EMAIL_NOTIFICATION,
                new_data,
                old_data,
            )
        email_data_collection_to_send_email(
            EmailNotifications.objects.get(id=id)
        )
        return redirect("email_list")
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)
