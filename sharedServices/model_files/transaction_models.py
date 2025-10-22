"""models"""
# Date - 21/06/2021
# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on
#                       creating database tables for
#                       all modules.
#   Name            - Authentication related models
#   Modified by     - Manish Pawar
#   Modified date   - 26/06/2021


# Imports required to make models are below
from django.db import models
from .station_models import Stations
from .app_user_models import MFGUserEV, Profile
from .admin_user_models import AdminUser
from ..constants import (
    YES,
    NO,
    WALLET_TRANSACTION_FOR_CONST,
    LOYALTY_TRANSACTION_FOR_CONST,
    LOAD_WALLET_TRANSACTION_FOR_CONST,
    ACTIVATE_WALLET_TRANSACTION_FOR_CONST,
    REDEEM_WALLET_TRANSACTION_FOR_CONST,
)

# reconciliation models


class Transactions(models.Model):
    """transactions model"""

    status = (
        ("Exact", "Exact"),
        ("Overpayment", "Overpayment"),
        ("Underpayment", "Underpayment"),
        ("-", "-"),
    )
    transactions_db_id = models.AutoField
    station_id = models.ForeignKey(
        Stations, null=True, on_delete=models.SET_NULL
    )

    order_id = models.CharField(max_length=30, blank=True, null=True)
    transaction_id = models.CharField(max_length=30, blank=True, null=True)
    payment_id = models.CharField(max_length=30, blank=True, null=True)

    gross_sales = models.FloatField(default=0)
    discounts = models.FloatField(default=0)
    net_sales = models.FloatField(default=0)
    tax = models.FloatField(default=0)
    tip = models.FloatField(default=0)
    partial_refunds = models.FloatField(default=0)
    total_collected = models.FloatField(default=0)

    card = models.FloatField(default=0)
    fees = models.FloatField(default=0)
    net_total = models.FloatField(default=0)

    payment_method = models.CharField(max_length=30, blank=True, null=True)
    pan_suffix = models.CharField(max_length=10, blank=True, null=True)
    details = models.CharField(max_length=1000, blank=True, null=True)

    customer_id = models.CharField(max_length=100, blank=True, null=True)
    transaction_status = models.CharField(
        max_length=100, blank=True, null=True
    )
    transaction_amount = models.FloatField(default=0)
    settlement_amount = models.FloatField(default=0)

    transaction_currency = models.CharField(
        max_length=10, blank=True, null=True
    )
    status = models.CharField(
        max_length=100, blank=True, choices=status, default="-"
    )

    payment_for = models.CharField(max_length=100, blank=True, null=True)
    payment_for_reference_id = models.IntegerField(blank=True, null=True)

    comments = models.CharField(max_length=100, blank=True, null=True)
    transaction_timestamp = models.DateTimeField(blank=True, null=True)
    settlement_date = models.DateTimeField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)
    payment_response = models.TextField(blank=True, null=True)
    is_ocpi_session = models.BooleanField(default=False, null=False, blank=False)

    def __str__(self):
        return str(self.transaction_id)


class TransactionsDetails(models.Model):
    """transaction details model"""

    transactions_db_id = models.AutoField
    order_id = models.CharField(max_length=30, blank=True, null=True)
    station_id = models.ForeignKey(
        Stations, null=True, on_delete=models.SET_NULL
    )

    transaction_id = models.CharField(max_length=30, blank=True, null=True)
    transaction_source = models.CharField(max_length=30, blank=True, null=True)
    receipt_number = models.CharField(max_length=30, blank=True, null=True)
    receipt_url = models.CharField(max_length=1000, blank=True, null=True)

    payment_method = models.CharField(max_length=30, blank=True, null=True)
    issuing_bank = models.CharField(max_length=30, blank=True, null=True)
    status = models.CharField(max_length=100, blank=True)
    comments = models.CharField(max_length=100, blank=True, null=True)

    transaction_timestamp = models.DateTimeField(blank=True, null=True)
    transaction_date = models.DateTimeField(blank=True, null=True)
    transaction_status = models.CharField(max_length=100, blank=True)

    transaction_amount_money_amount = models.FloatField(default=0)
    transaction_app_fee_money_amount = models.FloatField(default=0)
    transaction_approved_money_amount = models.FloatField(default=0)

    transaction_app_fee_money_currency = models.CharField(
        max_length=10, blank=True, null=True
    )
    transaction_approved_money_currency = models.CharField(
        max_length=10, blank=True, null=True
    )
    transaction_amount_money_currency = models.CharField(
        max_length=10, blank=True, null=True
    )

    processing_fee_currency = models.CharField(
        max_length=10, blank=True, null=True
    )
    processing_fee_effective_at = models.DateTimeField(blank=True, null=True)
    processing_fee_type = models.CharField(
        max_length=100, blank=True, null=True
    )

    card_id = models.ForeignKey(Profile, null=True, on_delete=models.SET_NULL)
    settlement_amount = models.FloatField(default=0)
    processing_fee_amount = models.FloatField(default=0)
    settlement_date = models.DateTimeField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=1000, blank=True, null=True)
    created_by = models.CharField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return str(self.order_id)


class TransactionsTracker(models.Model):
    """transaction details model"""

    conditions = ((YES, YES), (NO, NO))
    payment_for_types = (
        (WALLET_TRANSACTION_FOR_CONST, WALLET_TRANSACTION_FOR_CONST),
        (LOYALTY_TRANSACTION_FOR_CONST, LOYALTY_TRANSACTION_FOR_CONST),
    )
    payment_for_subtypes = (
        (LOAD_WALLET_TRANSACTION_FOR_CONST, LOAD_WALLET_TRANSACTION_FOR_CONST),
        (
            ACTIVATE_WALLET_TRANSACTION_FOR_CONST,
            ACTIVATE_WALLET_TRANSACTION_FOR_CONST,
        ),
        (
            REDEEM_WALLET_TRANSACTION_FOR_CONST,
            REDEEM_WALLET_TRANSACTION_FOR_CONST,
        ),
    )
    processed_by_types = (
        ("Admin", "Admin"),
        ("App", "App"),
    )
    transaction_statuses = (
        ("Successful", "Successful"),
        ("Unsuccessful", "Unsuccessful"),
    )
    refund_statuses = (
        ("Pending", "Pending"),
        ("Failed", "Failed"),
        ("Rejected", "Rejected"),
        ("Completed", "Completed"),
    )
    user_id = models.ForeignKey(
        MFGUserEV, null=True, on_delete=models.SET_NULL
    )
    payment_customer_id = models.CharField(
        max_length=1000, unique=False, null=True
    )
    payment_id = models.CharField(max_length=200, blank=True, null=True)
    payment_for_type = models.CharField(
        max_length=100,
        choices=payment_for_types,
        default="",
        blank=True,
        null=True,
    )
    payment_for_subtype = models.CharField(
        max_length=100,
        choices=payment_for_subtypes,
        default="",
        blank=True,
        null=True,
    )
    payment_status = models.CharField(
        max_length=100,
        choices=transaction_statuses,
        default="",
        blank=True,
        null=True,
    )
    payment_response = models.TextField(blank=True, null=True)
    payment_date = models.DateTimeField(blank=True, null=True)
    payment_reference_id = models.IntegerField(default=0)
    transaction_amount = models.IntegerField(default=0)
    reference_current_status = models.CharField(
        max_length=100,
        choices=transaction_statuses,
        default="",
        blank=True,
        null=True,
    )
    reference_response = models.TextField(blank=True, null=True)
    refund_reference_id = models.CharField(
        max_length=1000, blank=True, null=True
    )
    refund_status = models.CharField(
        max_length=100,
        choices=refund_statuses,
        default=None,
        blank=True,
        null=True,
    )
    refund_amount = models.IntegerField(default=0)
    refund_response = models.TextField(blank=True, null=True)
    refund_initiated_date = models.DateTimeField(blank=True, null=True)
    refund_completed_date = models.DateTimeField(blank=True, null=True)
    is_reviewed = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    comments = models.CharField(max_length=1000, blank=True, null=True)
    assigned_by = models.ForeignKey(
        AdminUser, null=True, on_delete=models.SET_NULL
    )
    driivz_account_number = models.CharField(
        max_length=100, null=True, blank=True
    )
    user_updated_balance = models.CharField(
        max_length=100, null=True, blank=True
    )
    processed_by = models.CharField(
        max_length=100,
        choices=processed_by_types,
        default="App",
        blank=True,
        null=True,
    )
    is_withdrawn = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    expiry_date = models.DateTimeField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return (
            f"User ID->{str(self.user_id)}, Payment ID {str(self.payment_id)}"
        )
