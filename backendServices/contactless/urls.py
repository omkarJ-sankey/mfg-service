"""Contactless api urls"""
# Date - 26/08/2022


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on defining url path
#                        to access particular view or API.
#   Name            - Contactless Urls
#   Modified by     - Manish Pawar
#   Modified date   - 26/08/2022


# Imports required to make urls are below
from django.urls import path


# Views and APIs used for particular action and operation
from .apis import (
    SubmitDownloadedReceiptData,
    ListDownloadedList,
    GetReceiptSavedStatus,
)


# Assigning Views and APIs to particular url to access there functionality

urlpatterns = [
    path(
        "api/save-downloaded-receipt/",
        SubmitDownloadedReceiptData.as_view(),
    ),
    path(
        "api/downloaded-receipt-list/",
        ListDownloadedList.as_view(),
    ),
    path("api/get-saved-status/", GetReceiptSavedStatus.as_view()),
]
