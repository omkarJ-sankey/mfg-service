"""promotions app level constants"""
# Date - 01/03/2022

# File details-
#   Author          - Manish Pawar
#   Description     - This file contains constants related to promotions.
#   Name            - Promotions constants
#   Modified by     - Manish Pawar
#   Modified date   - 01/03/2022
UNQUIE_CODE = "Unique/Barcode"
LIST_OF_FILDS_FOR_PROMOTIONS = [
    "Product",
    UNQUIE_CODE,
    "Start date",
    "End date",
    "M Code",
    "Retail code",
    "Promotion title",
    "Available for",
    "Offer type",
    "Status(Active/Inactive)",
    "Product price",
    "Quantity",
    "Offer details",
    "Terms and condition",
]

LIST_OF_ITERATION_FILDS_FOR_PROMOTIONS = [
    "Product",
    UNQUIE_CODE,
    "M Code",
    "Start date",
    "End date",
    "Retail code",
    "Promotion title",
    "Available for",
    "Offer type",
    "Londis code",
    "Budgens code",
    "Product price",
    "Quantity",
    "Offer details",
    "Terms and condition",
    "Status(Active/Inactive)",
    "Promotion image 1(33.5:14)",
    "Promotion image 2 (16:23.6)",
]

LIST_CONTAINING_ID = ["ID"]

LIST_OF_ITERATION_FILDS_FOR_PROMOTIONS_EXPORT = (
    LIST_CONTAINING_ID + LIST_OF_ITERATION_FILDS_FOR_PROMOTIONS
)

LIST_OF_FILDS_FOR_PROMOTIONS_ASSIGN = [UNQUIE_CODE, "Shop"]
LIST_OF_ITERATION_FILDS_FOR_PROMOTIONS_ASSIGN = [
    "Station ID",
    UNQUIE_CODE,
    "Shop",
    "Operation region",
    "Regions",
    "Area",
]

LIST_OF_ITERATION_FILDS_FOR_PROMOTIONS_ASSIGN_EXPORT = (
    LIST_CONTAINING_ID + LIST_OF_ITERATION_FILDS_FOR_PROMOTIONS_ASSIGN
)

FILETERED_PROMOTIONS = 0
FILETERED_DATA = 1
URL_DATA = 2

EMPTY_OFFER_TYPE_LIST = ["Trade up"]
