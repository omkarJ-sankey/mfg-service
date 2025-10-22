"""session transactions urls"""
# Date - 11/01/2022

# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on defining
#                       url path to access particular view or API.
#   Name            - Session Transactions Urls
#   Modified by     - Anuj More
#   Modified date   - 10/01/2023


# Imports required to make urls are below
from django.urls import path

# Views and APIs used for particular action and operation
from .views import (
    session_transactions_list,
    view_session_transaction_details,
    mark_as_reviewed,
    collect_pre_auth,
    hold_payment_list,
    hold_payment_details,
)

# Assigning Views and APIs to particular url to access there functionality
urlpatterns = [
    path("", session_transactions_list, name="session_transactions_list"),
    path(
        "session-details/<int:session_pk>/",
        view_session_transaction_details,
        name="view_session_transaction_details",
    ),
    path("mark-as-reviewed/", mark_as_reviewed, name="mark_as_reviewed"),
    path("collect-pre-auth/<int:session_id>/", collect_pre_auth, name="collect_pre_auth"),
    path("hold-payments-list/",hold_payment_list,name="hold_payment_list"),
    path(
        "hold-payment-details/<int:session_pk>/",
        hold_payment_details,
        name="hold_payment_details",
    ),
]
