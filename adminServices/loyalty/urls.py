"""loyalty urls"""
# Date - 03/01/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on defining url path to
#                     access particular view or API.
#   Name            - Loyalty Urls
#   Modified by     - Manish Pawar
#   Modified date   - 03/01/2021

# Imports required to make urls are below
from django.urls import path

# Views and APIs used for particular action and operation
from .views import (
    AddLoyaltiesView,
    ChangeLoyaltyStatusView,
    LoyaltyListView,
    ViewLoyaltyDetailsView,
    loyalties,
    change_loyalty_status_view,
    add_loyalties,
    edit_loyalties,
    delete_loyalties,
    view_loyalties,
)

# Assigning Views and APIs to particular url to access there functionality

urlpatterns = [
    path("", loyalties, name="loyalties_list"),
    path("loyality-list/",LoyaltyListView.as_view(), name="loyalties_list"),
    # path(
    #     "change--loyalty-status-view/",
    #     change_loyalty_status_view,
    #     name="change_loyalty_status_view",
    # ),
    path("change-loyalty-status/",ChangeLoyaltyStatusView.as_view(), name="change_layalty_status"),
    # path("add-loyalties/", add_loyalties, name="add_loyalties"),
    path("add-loyalties/", AddLoyaltiesView.as_view(), name="add_loyalties"),
    path(
        "view-loyalties/<int:loyalty_pk>/",
        view_loyalties,
        name="view_loyalties",
    ),
    path("view-loyalties/",ViewLoyaltyDetailsView.as_view(),name="view_loyalties"),
    path(
        "edit-loyalties/<int:loyalty_pk>/",
        edit_loyalties,
        name="edit_loyalties",
    ),
    path(
        "delete-loyalties/<int:loyalty_pk>/",
        delete_loyalties,
        name="delete_loyalties",
    ),
]
