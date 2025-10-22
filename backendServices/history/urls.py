"""history app urls"""
from django.urls import path

# Views and APIs used for particular action and operation
from .apis import (
    ChargingSessionHistoryDetailAPI,
    ChargingSessionHistoryAPI,
    TripHistoryAPI,
    TripHistoryDetailAPI,
    ReceiptsListAPI,
    ReceiptDetailsAPI,
    GetReceiptGenerationStatus
)


# Assigning Views and APIs to particular url to access there functionality
urlpatterns = [
    path("api/user-trips-history/", TripHistoryAPI.as_view()),
    path("api/user-trip-history-details/", TripHistoryDetailAPI.as_view()),
    path("api/user-chargings-history/", ChargingSessionHistoryAPI.as_view()),
    path(
        "api/user-charging-history-details/",
        ChargingSessionHistoryDetailAPI.as_view(),
    ),

    # v4 APIs
    path("api/v4/receipt-list/", ReceiptsListAPI.as_view()),
    path("api/v4/receipt-details/", ReceiptDetailsAPI.as_view()),
    path("api/v4/get-receipt-generation-status/", GetReceiptGenerationStatus.as_view()),
]
