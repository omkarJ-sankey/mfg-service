"""promotions urls"""
# Date - 21/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on defining url path to
#                     access particular view or API.
#   Name            - Promotions Urls
#   Modified by     - Manish Pawar
#   Modified date   - 26/06/202promotion_pk

# Imports required to make urls are below
from django.urls import path

# Views and APIs used for particular action and operation
from .views import (
    add_promotions,
    promotions_list,
    change_status_view,
    edit_promotions,
    delete_promotions,
    view_promotions,
    checkbox_data_for_add_promotions,
    RemoveCachedOnPromotionExpiry
)
from .bulk_upload_views import upload_sheet_promotions, progress_bar_info

# Assigning Views and APIs to particular url to access there functionality

urlpatterns = [
    path("", promotions_list, name="promotions_list"),
    path("add-promotions/", add_promotions, name="add_promotions"),
    path(
        "view-promotions/<int:promotion_pk>/",
        view_promotions,
        name="view_promotions",
    ),
    path(
        "edit-promotions/<int:promotion_pk>/",
        edit_promotions,
        name="edit_promotions",
    ),
    path("change-status-view/", change_status_view, name="change_status_view"),
    path(
        "delete-promotions/<int:promotion_pk>/",
        delete_promotions,
        name="delete_promotions",
    ),
    path(
        "check-box-selection-url/",
        checkbox_data_for_add_promotions,
        name="checkbox_data_for_add_promotions",
    ),
    path(
        "uploadSheet/", upload_sheet_promotions, name="uploadSheet_promotions"
    ),
    path("progress-info/", progress_bar_info, name="promotion_progress_bar"),
    path(
        "api/remove-cache-on-promotion-expiry/",
        RemoveCachedOnPromotionExpiry.as_view(),
        name="RemoveCachedOnPromotionExpiry"
    ),
]
