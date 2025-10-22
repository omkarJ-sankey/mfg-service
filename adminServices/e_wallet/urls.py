"""e-wallet urls"""
# File details-
#   Author      - Shubham Dhumal
#   Description - This file is declare urlpatterns of e-wallet
#   Name        - E-Wallet urls
#   Modified by - Shubham Dhumal

from django.urls import path
from .views import (
    wallet,
    assign_amount,
    list_email,
    get_receiver_data,
    wallet_details,
    withdraw_wallet_amount,
    create_gift_cards_for_old_users
)

# This are urls for Ewallet
# 1. '/' it's render page

urlpatterns = [
    path("", wallet, name="ewallet"),
    path("assign-amount", assign_amount, name="add_ewallet"),
    path("list-email", list_email, name="list_email"),
    path("receiver-data", get_receiver_data, name="get_receiver_data"),
    path(
        "details/<str:transaction_id>/",
        wallet_details,
        name="wallet_details"
    ),
    path(
        "withdraw-wallet-amount/",
        withdraw_wallet_amount,
        name="withdraw_wallet_amount"
    ),
    path(
        "create-gift-cards-for-old-users/",
        create_gift_cards_for_old_users,
        name="create_gift_cards_for_old_users"
    ),
]
