"""reconciliation urls"""
# Date - 21/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on defining url path to
#                        access particular view.
#   Name            - Reconciliation Urls
#   Modified by     - Manish Pawar
#   Modified date   - 26/06/2021


# Imports required to make urls are below
from django.urls import path
from .views import (
    add_comment_to_transaction_view,
    import_reconciliation_data,
    reconciliation_list,
    reconciliation_list_for_station,
    reconciliation_transaction_list,
    transaction_details,
)


# Assigning Views to particular url to access there functionality
urlpatterns = [
    path("", reconciliation_list, name="reconciliation_list"),
    path(
        "import-data/",
        import_reconciliation_data,
        name="import_reconciliation_data",
    ),
    path(
        "all-transactions/",
        reconciliation_transaction_list,
        name="reconciliation_transaction_list",
    ),
    path(
        "station-reconciliation/<int:station_pk>/",
        reconciliation_list_for_station,
        name="reconciliation_list_for_station",
    ),
    path(
        "transaction-details/<int:transaction_pk>/",
        transaction_details,
        name="transaction_details",
    ),
    path("make-comment/", add_comment_to_transaction_view, name="do_comment"),
]
