"""reconciliation app level constants"""
# Date - 01/03/2022

# File details-
#   Author          - Manish Pawar
#   Description     - This file contains constants related to reconciliation.
#   Name            - Reconciliation constants
#   Modified by     - Manish Pawar
#   Modified date   - 07/02/2022

LIST_OF_FIELDS_FOR_RECONCILIATION = [
    "Date",
    "Station ID",
    "Station Name",
    "Payment Method",
    "Transaction Total",
    "Settlement Total",
    "Status",
]

LIST_OF_FIELDS_FOR_RECONCILIATION_EXPORT = [
    "Transaction ID"
] + LIST_OF_FIELDS_FOR_RECONCILIATION
