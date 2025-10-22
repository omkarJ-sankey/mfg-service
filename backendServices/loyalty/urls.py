"""loylty api urls"""
from django.urls import path

# Views and APIs used for particular action and operation
from .apis import (
    loyalty_transaction_submission_api,
    LoyaltyDetailsAPI,
    LoyaltyFilters,
    QRCodeGeneratorAPIForLoyalty,
    LoyaltyListViewset,
    upload_loyalty_transaction_in_bulk,
    ConfirmPurchasedAPI,
    CheckUserActiveReward,
    LoyaltyRewardBurnDownCRONJobAPI,
    SendLoyaltyRewardReminderNotificationCronJob,
)

from .v4_apis import (
    LoyaltyListViewsetV4,
    LoyaltyDetailsAPIV4,
    EnableDailyLoyaltyAPI
)

# Assigning Views and APIs to particular url to access there functionality
urlpatterns = [
    path(
        "api/submit-loyalty-transaction/",
        loyalty_transaction_submission_api,
        name="loyalty_transaction_submission_api"
    ),
    path(
        "api/submit-bulk-transactions/",
        upload_loyalty_transaction_in_bulk,
        name="upload_loyalty_transaction_in_bulk"
    ),
    path("api/loyalty-filters/", LoyaltyFilters.as_view()),
    path("api/loyalty-list/", LoyaltyListViewset.as_view()),
    path("api/loyalty-details/", LoyaltyDetailsAPI.as_view()),
    path("api/generate-qr-code-api/", QRCodeGeneratorAPIForLoyalty.as_view()),
    path("api/confirm-purchase-api/", ConfirmPurchasedAPI.as_view()),
    path(
        "api/loyalty-reward-burndown-cron-job/",
        LoyaltyRewardBurnDownCRONJobAPI.as_view(),
    ),
    path(
        "api/check-user-active-reward/",
        CheckUserActiveReward.as_view(),
    ),
    path(
        "api/send-loyalty-reward-reminder-notification/",
        SendLoyaltyRewardReminderNotificationCronJob.as_view(),
    ),

    # V4 API routes
    path("api/v4/loyalty-list/", LoyaltyListViewsetV4.as_view()),
    path("api/v4/loyalty-details/", LoyaltyDetailsAPIV4.as_view()),
    path(
        "api/v4/enable-daily-loyalties/",
        EnableDailyLoyaltyAPI.as_view(),
    ),
]
