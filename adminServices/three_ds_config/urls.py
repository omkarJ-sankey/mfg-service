"""3DS config urls"""
# Date - 14/12/2024

# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on defining
#                        url path to access particular view or API.
#   Name            - Stations Urls
#   Modified by     - Manish Pawar
#   Modified date   - 14/12/2024


# Imports required to make urls are below
from django.urls import path

# Views and APIs used for particular action and operation
from .views import (
    three_ds_config_for_all_app_users,
    user_specific_3ds_config,
    add_or_edit_user_specific_3ds_config,
    three_ds_logs,
    remove_user_specific_3ds_config
)

# Assigning Views and APIs to particular url to access there functionality
urlpatterns = [
    path("", three_ds_config_for_all_app_users, name="three_ds_config_for_all_app_users"),
    path("user-specific-3ds-config/", user_specific_3ds_config, name="user_specific_3ds_config"),
    path(
        "add-or-edit-user-specific-3ds-config/<str:user_id>/",
        add_or_edit_user_specific_3ds_config,
        name="add_or_edit_user_specific_3ds_config"
    ),
    path(
        "remove-user-specific-3ds-config/<str:user_id>/",
        remove_user_specific_3ds_config,
        name="remove_user_specific_3ds_config"
    ),
    path("three-ds-logs/", three_ds_logs, name="three_ds_logs"),
]
