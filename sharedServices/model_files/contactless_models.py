"""models"""
# Date - 21/09/2022
# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on
#                       creating database tables for
#                       all modules.
#   Name            - Contactless related models
#   Modified by     - Aditya Dhadke
#   Modified date   - 04/10/2024


# Imports required to make models are below
from django.db import models
from .app_user_models import MFGUserEV


class ContactlessReceiptEmailTracking(models.Model):
    """contactless receipt email tracking"""

    email = models.CharField(max_length=100, null=True)
    # session_id field stores 'driivzTransactionId' for
    # charging session and for 'Payter transactionId' Valeting
    session_id = models.CharField(max_length=100, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    source = models.CharField(max_length=100, default="driivz and payter")


class ContactlessSessionsDownloadedReceipts(models.Model):
    """Contactless downloaded receipts"""

    receipt_id = models.AutoField
    user_id = models.ForeignKey(
        MFGUserEV,
        null=True,
        on_delete=models.SET_NULL,
        related_name="user_charging_sessions_receipts",
        related_query_name="user_charging_sessions_receipts",
    )
    user_account_number = models.CharField(
        max_length=100, blank=True, null=True
    )
    driivz_transaction_id = models.CharField(
        max_length=100, blank=True, null=True
    )
    payter_or_rh_transaction_id = models.CharField(
        max_length=100, blank=True, null=True
    )
    session_cost = models.CharField(max_length=100, blank=True, null=True)
    session_power_consumed = models.CharField(
        max_length=100, blank=True, null=True
    )
    session_duration = models.CharField(max_length=100, blank=True, null=True)
    receipt_data = models.TextField(null=True, blank=True)
    downloaded_date = models.DateTimeField(blank=True, null=True)
    session_date = models.DateTimeField(blank=True, null=True)
    is_version_4_receipt = models.BooleanField(default=False)

    class Meta:
        """meta data"""

        db_table = "contactless_downloaded_receipts"

    def __str__(self):
        return str(self.user_account_number)


class ThirdPartyServicesData(models.Model):
    """Sorting data of payter and drivz"""

    status_conditions = (
        ("Complete", "Complete"),
        ("Inprogress", "Inprogress"),
        ("Failed", "Failed"),
    )
    data_date = models.DateTimeField(blank=True, null=True)
    source = models.CharField(max_length=100, null=True)
    data = models.TextField(null=True)
    status = models.CharField(
        max_length=100,
        choices=status_conditions,
        default="Inprogress",
        blank=True,
        null=True,
    )
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, null=True)
    details = models.TextField(null=True, blank=True)

    class Meta:
        """meta data"""

        db_table = "thirdparty_services_data"


class ReceiptHeroReceiptsData(models.Model):
    """ReceiptHero receipts"""

    request_id = models.CharField(max_length=100, null=True)
    transaction_id = models.CharField(max_length=100)
    rh_data = models.TextField(null=True)
    driivz_data = models.TextField(null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, null=True)

    class Meta:
        """meta data"""

        db_table = "receiptHero_receipts_data"

class DriivzData(models.Model):
    key = models.CharField(unique=True, max_length=75, blank=True, null=True)
    data = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'driivz_data'

class ValetingTransactionData(models.Model):
    """Valeting transaction data storage"""
    
    
    transaction_id = models.CharField(max_length=100, unique=True)
    card_number = models.CharField(max_length=50, blank=True, null=True)
    transaction_date = models.DateTimeField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    valeting_site_id = models.CharField(max_length=100)
    data = models.TextField(null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = "valeting_transaction_data"
        indexes = [
            models.Index(fields=['transaction_id', 'card_number']),
        ]

    def __str__(self):
        return str(self.transaction_id)
class AmpecoData(models.Model):
    key = models.CharField(unique=True, max_length=500, blank=True, null=True)
    data = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=50, blank=True, null=True)
    fetch_error_details = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'ampeco_data'

    def __str__(self):
        return str(self.key)