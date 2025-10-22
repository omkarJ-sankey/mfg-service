"""payment urls"""
# Date - 21/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on defining url
#                        path to access particular view or API.
#   Name            - Promotions Urls
#   Modified by     - Manish Pawar
#   Modified date   - 26/06/2021


# Imports required to make urls are below
from django.urls import path

# Views and APIs used for particular action and operation
from .customerapis import (
    CustomerListApi,
    CreateCustomerApi,
    RetrieveCustomerApi,
    UpdateCustomerApi,
    DeleteCustomerApi,
)
from .cardsapi import (
    CustomersListCardsApi,
    CreateCustomerCardApi,
    RetrieveCustomerCardApi,
    RetrieveCustomerCardsApi,
    AddDefaultPaymentMethod,
    DisableCustomerApi,
    CreateCustomerCardApiV4,
)
from .paymentapis import (
    CustomerPaymentListAPI,
    RetrieveCustomerPaymentApi,
    CreateCustomerPaymentApi,
    UpdateCustomerPaymentApi,
    CancelCustomerPaymentApi,
    CompleteCustomerPaymentApi,
)
# from .locationapis import (
#     ListLocationsApi,
#     RetrieveLocationApi,
#     CreateLocationApi,
# )
# from .orderapis import (
#     CreateOrderApi,
# )
# from .transactionapis import TransactionsListAPI, RetrieveTransactionAPI

from .gift_cards import (
    AddCreditsInWallet,
    # RefundWalletPayment,
    # RefundPaymentsCheckerCronjob
)

# Assigning Views and APIs to particular url to access there functionality

urlpatterns = [
    path("api/list-customers/", CustomerListApi.as_view()),
    path("api/create-customer/", CreateCustomerApi.as_view()),
    path("api/update-customer/", UpdateCustomerApi.as_view()),
    path("api/retrieve-customer/", RetrieveCustomerApi.as_view()),
    path("api/delete-customer/", DeleteCustomerApi.as_view()),
    path("api/list-customers-cards/", CustomersListCardsApi.as_view()),
    path("api/retrieve-customer-cards/", RetrieveCustomerCardsApi.as_view()),
    path("api/add-default-payment-method/", AddDefaultPaymentMethod.as_view()),
    path("api/retrieve-customer-card/", RetrieveCustomerCardApi.as_view()),
    path("api/create-customer-card/", CreateCustomerCardApi.as_view()),
    path("api/v4/create-customer-card/", CreateCustomerCardApiV4.as_view()),
    path("api/disable-customer-card/", DisableCustomerApi.as_view()),
    path("api/list-customers-payments/", CustomerPaymentListAPI.as_view()),
    path(
        "api/retrieve-customer-payment/", RetrieveCustomerPaymentApi.as_view()
    ),
    path("api/create-customer-payment/", CreateCustomerPaymentApi.as_view()),
    path("api/update-customer-payment/", UpdateCustomerPaymentApi.as_view()),
    path("api/cancel-customer-payment/", CancelCustomerPaymentApi.as_view()),
    path(
        "api/complete-customer-payment/", CompleteCustomerPaymentApi.as_view()
    ),
    # path("api/list-locations/", ListLocationsApi.as_view()),
    # path("api/retrieve-location/", RetrieveLocationApi.as_view()),
    # path("api/create-location/", CreateLocationApi.as_view()),
    # path("api/create-order/", CreateOrderApi.as_view()),
    # path("api/list-transactions/", TransactionsListAPI.as_view()),
    # path("api/retrieve-transaction/", RetrieveTransactionAPI.as_view()),
    # wallet / gift card urls
    path("api/load-amount-in-wallet/", AddCreditsInWallet.as_view()),
    # path("api/refund-request/", RefundWalletPayment.as_view()),
    # path("api/check-refund-statuses/",
    # RefundPaymentsCheckerCronjob.as_view())
]
