"""App users views"""
# Date - 22/05/2024
# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on views(backend logic)
#                       related to features to manage app users
#   Name            - App users Views
#   Modified by     - Manish Pawar
#   Modified date   - 22/05/2024

# imports required to create views
import json
import secrets
from passlib.hash import django_pbkdf2_sha256 as handler

from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib import messages

# pylint:disable=import-error
from sharedServices.decorators import allowed_users, authenticated_user
from sharedServices.common import (
    filter_url,
    get_blocked_emails_and_phone_numbers,
    hasher,
    redis_connection
)
from sharedServices.common_audit_trail_functions import (
    audit_data_formatter,
    add_audit_data,
)
from sharedServices.constants import (
    BLOCK_APP_USERS_CONST,
    GET_METHOD_ALLOWED,
    POST_METHOD_ALLOWED,
    COMMON_ERRORS,
    ERROR_TEMPLATE_URL,
    NO,
    BLOCKED_USERS_EMAILS_LIST,
    BLOCKED_USERS_PHONE_LIST,
    BASE_CONFIG_CONST,
    AUDIT_ADD_CONSTANT,
    AUDIT_UPDATE_CONSTANT
)
from sharedServices.model_files.config_models import (
    BaseConfigurations
)
from sharedServices.model_files.app_user_models import (
    Profile, MFGUserEV
)
from .forms import DisplayBlockUserForm


def remove_user_phone_verification(email):
    """remove user phone verification"""
    hashed_email = hasher(email)
    MFGUserEV.objects.filter(user_email=hashed_email).update(phone_number=None,hashed_phone_number=None)
    return Profile.objects.filter(
        user__user_email=hashed_email
    ).update(
        two_factor_done=NO,
        app_access_token=None
    )


def remove_access_token_and_update_password(email):
    """remove app access token of user"""
    user_objects = MFGUserEV.objects.filter(user_email=hasher(email))
    new_pass = handler.hash(secrets.token_hex(64))
    user_objects.update(password=new_pass)
    return Profile.objects.filter(
        user=user_objects.first()
    ).update(
        app_access_token=None
    )


def add_block_user_details_in_base_configurations(
    action,
    value,
    user,
    alternate_phone=False
):
    """common function to add blocked user details in the """
    dataset = BaseConfigurations.objects.filter(
        base_configuration_key=action
    )
    if dataset.first():
        dataset_id = dataset.first().id
        old_data = audit_data_formatter(
            BASE_CONFIG_CONST, dataset_id
        )
        data_list = list(json.loads(
            dataset.first().base_configuration_value
        ))
        if value not in data_list:
            data_list.append(value)
        else:
            return False
        if alternate_phone and value != alternate_phone and alternate_phone not in data_list:
            data_list.append(alternate_phone)
        action_perfomed = dataset.update(
            base_configuration_value=json.dumps(data_list)
        )
        new_data = audit_data_formatter(
            BASE_CONFIG_CONST, dataset_id
        )
        add_audit_data(
            user,
            f'{action}',
            f'{BASE_CONFIG_CONST}-{dataset_id}',
            AUDIT_UPDATE_CONSTANT,
            BASE_CONFIG_CONST,
            new_data,
            old_data,
        )
    else:
        action_perfomed = BaseConfigurations.objects.create(
            base_configuration_key=action,
            base_configuration_value=json.dumps([value])
        )
        new_data = audit_data_formatter(
            BASE_CONFIG_CONST, action_perfomed.id
        )
        add_audit_data(
            user,
            action,
            f"{BASE_CONFIG_CONST}-{action_perfomed.id}",
            AUDIT_ADD_CONSTANT,
            BASE_CONFIG_CONST,
            new_data,
            None,
        )
    redis_connection.delete(action)
    return action_perfomed


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=BLOCK_APP_USERS_CONST)
def block_app_users(request):
    """block app users form and list view"""
    try:
        form = DisplayBlockUserForm()

        block_user_phone_number_action_selected = False
        if request.method == 'POST':
            block_user_phone_number_action_selected = (
                request.POST.get('action') == '3'
            )
            form = DisplayBlockUserForm(request.POST)
            if form.is_valid():
                formed_data = form.cleaned_data
                if formed_data['action'] == '1': 
                    action_result = remove_user_phone_verification(
                        formed_data['email']
                    )
                    if action_result:
                        messages.success(
                            request,
                            "User phone verification has been removed successfully!"
                        )
                    else:
                        messages.warning(
                            request,
                            "Account with provided email not found!"
                        )
                    form.fields['email'].required = True
                if formed_data['action'] == '2':
                    token_removed = remove_access_token_and_update_password(
                        formed_data['email']
                    )
                    if token_removed:
                        action_result = add_block_user_details_in_base_configurations(
                            BLOCKED_USERS_EMAILS_LIST,
                            formed_data['email'],
                            request.user
                        )
                        if action_result is False:
                            messages.warning(
                                request,
                                "User account is already being blocked!"
                            )
                        elif action_result:
                            messages.success(
                                request,
                                "User account has been blocked successfully!"
                            )  
                        else:
                            messages.warning(
                                request,
                                "Failed to block user account!"
                            )  
                    else:
                        messages.warning(
                            request,
                            "Account with provided email not found!"
                        ) 
                    form.fields['email'].required = True
                if formed_data['action'] == '3':
                    action_result = add_block_user_details_in_base_configurations(
                        BLOCKED_USERS_PHONE_LIST,
                        f"{formed_data['country_code']}{formed_data['phone']}",
                        request.user,
                        alternate_phone=(
                            f"{formed_data['country_code']}0{formed_data['phone']}"
                            if not formed_data['phone'].startswith("0")
                            else False
                        )
                    )
                    if action_result is False:
                        messages.warning(
                            request,
                            "User phone number is already being blocked!"
                        )
                    elif action_result:
                        messages.success(
                            request,
                            "User phone number blocked successfully!"
                        )  
                    else:
                        messages.warning(
                            request,
                            "Failed to block user phone number"
                        ) 
                    form.fields['phone'].required = True
                    form.fields['country_code'].required = True
            else:
                messages.warning(
                    request, "Please provide valid details."
                )
        else:
            form.fields['email'].required = True
        # Here filter_url() function is used to filter
        # navbar elements so that we can  render only those navbar tabs
        # to which logged in user have access.
        url_data = filter_url(
            request.user.role_id.access_content.all(), BLOCK_APP_USERS_CONST
        )
        blocked_emails, blocked_phone_numbers = get_blocked_emails_and_phone_numbers()

        context = {
            "data": url_data,
            "form": form,
            "block_user_phone_number_action_selected": block_user_phone_number_action_selected,
            "blocked_phone_numbers": blocked_phone_numbers,
            "blocked_emails": blocked_emails,
        }
        return render(
            request,
            "app_users/block_app_users.html",
            context=context,
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)
