"""models"""

# Date - 21/06/2021
# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on
#                       creating database tables for
#                       loyalty module.
#   Name            - Loyalty related models
#   Modified by     - Manish Pawar
#   Modified date   - 26/06/2021


# Imports required to make models are below
from decouple import config
from django.db import models
from django.db.models import Q
from .station_models import Stations
from .app_user_models import MFGUserEV
from .notifications_module_models import PushNotifications
from ..constants import (
    YES,
    NO,
    IN_PROGRESS,
    QUEUED,
    COMEPLETED,
    NEED_REVIEW,
    FAILED,
    GENERIC_OFFERS,
    LOYALTY_OFFERS,
    GUEST_USERS,
    ALL_USERS,
    REGISTERED_USERS,
)


class Loyalty(models.Model):
    """loyalty base table"""

    status = (
        ("Active", "Active"),
        ("Inactive", "Inactive"),
    )
    offer_types = (
        (GENERIC_OFFERS, GENERIC_OFFERS),
        (LOYALTY_OFFERS, LOYALTY_OFFERS),
    )
    available = (
        ("App Only", "App Only"),
        ("Generic", "Generic"),
        ("All", "All"),
    )
    redeem_types = (
        ("Count", "Count"),
        ("Amount", "Amount"),
    )
    conditions = ((YES, YES), (NO, NO))

    loyalty_visibility = (
        (GUEST_USERS,GUEST_USERS),
        (REGISTERED_USERS,REGISTERED_USERS),
        (ALL_USERS,ALL_USERS)
    )

    loyalty_id = models.AutoField(primary_key=True)
    product = models.CharField(max_length=60, null=True, blank=True)
    category = models.CharField(max_length=60, null=True, blank=True)
    loyalty_title = models.CharField(max_length=60, null=True, blank=True)
    status = models.CharField(
        max_length=60, null=True, blank=True, choices=status
    )
    offer_type = models.CharField(
        max_length=60, null=True, blank=True, choices=offer_types
    )
    valid_from_date = models.DateTimeField(blank=True, null=True)
    valid_to_date = models.DateTimeField(blank=True, null=True)

    # Value for show_occurrence_offer
    show_occurrence_offer = models.BooleanField(null=True, default=False)
    # End of daily loyalty fields

    number_of_paid_purchases = models.FloatField(default=0)
    timed_expiry = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    occurance_status = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    bar_code_std = models.CharField(max_length=100, null=True, blank=True)
    scheme_bar_code = models.CharField(max_length=100, null=True, blank=True)
    product_bar_code = models.CharField(max_length=100, null=True, blank=True)
    # redeem fields
    redeem_product_code = models.CharField(
        max_length=100, null=True, blank=True
    )
    redeem_product = models.CharField(max_length=100, null=True, blank=True)
    redeem_product_promotional_code = models.CharField(
        max_length=100, null=True, blank=True
    )
    qr_refresh_time = models.IntegerField(default=5)

    redemption_price = models.FloatField(default=0)
    is_shop_wise = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    shop_ids = models.CharField(max_length=1000, blank=True, null=True)
    deleted = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    available_for = models.CharField(
        max_length=100, blank=True, choices=available
    )
    cycle_duration = models.CharField(max_length=100, blank=True)
    redeem_type = models.CharField(
        max_length=100, null=True, blank=True, choices=redeem_types
    )
    unique_code = models.CharField(max_length=100, null=True, blank=True)
    loyalty_validity_duration = models.CharField(
        max_length=100, null=True, blank=True
    )
    offer_details = models.CharField(max_length=1100, blank=True, null=True)
    terms_and_conditions = models.CharField(
        max_length=4000, blank=True, null=True
    )
    steps_to_redeem = models.CharField(
        max_length=1100, blank=True, null=True
    )
    image = models.ImageField(upload_to="images", blank=True, null=True)
    station_loyalty_card_image = models.ImageField(
        upload_to="images", blank=True, null=True
    )

    # fields added to handle costa coffee loyalty
    loyalty_type = models.CharField(max_length=60, null=True, blank=True)
    number_of_total_issuances = models.IntegerField(blank=True, null=True)
    number_of_issued_vouchers = models.IntegerField(blank=True, null=True)
    reward_image = models.ImageField(upload_to="images", blank=True, null=True)

    reward_unlocked_notification_id = models.ForeignKey(
        PushNotifications,
        null=True,
        on_delete=models.SET_NULL,
        related_name="reward_unlocked_notifications",
        related_query_name="reward_unlocked_notifications",
    )
    reward_expiration_notification_id = models.ForeignKey(
        PushNotifications,
        null=True,
        on_delete=models.SET_NULL,
        related_name="reward_expiration_notifications",
        related_query_name="reward_expiration_notifications",
    )

    reward_activated_notification_expiry = models.IntegerField(
        default=0, null=True
    )
    reward_expiration_notification_expiry = models.IntegerField(
        default=0, null=True
    )
    expire_reward_before_x_number_of_days = models.IntegerField(
        default=0, null=True
    )

    expiry_in_days = models.IntegerField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)
    reward_expiry_notification_trigger_time = models.CharField(
        max_length=100, blank=True, null=True
    )
    loyalty_list_footer_message = models.CharField(max_length=100, blank=True, null=True)
    trigger_sites = models.JSONField(blank=True, null=True, help_text="List of station IDs for custom trigger sites")
    transaction_count_for_costa_kwh_consumption = models.FloatField(blank=True, null=True, help_text="Required kWh consumption at trigger sites for activation")
    detail_site_check = models.BooleanField(null=True, default=False)
    visibility = models.CharField(max_length=100, choices=loyalty_visibility, blank=True, null=True)
    is_car_wash = models.BooleanField(null=True, default=False)
    display_on_charging_screen = models.BooleanField(null=True, default=True)
    def __str__(self):
        return str(self.loyalty_title)

    def get_loyalty_image(self):
        """get loyalty image"""
        return f"{config('DJANGO_APP_CDN_BASE_URL')}{self.image}"

    def get_loyalty_reward_image(self):
        """get loyalty reward image"""
        return f"{config('DJANGO_APP_CDN_BASE_URL')}{self.reward_image}"

    def get_station_loyalty_card_image(self):
        """get loyalty reward image"""
        return f"{config('DJANGO_APP_CDN_BASE_URL')}{self.station_loyalty_card_image}"

    class Meta:
        """loyalty table"""

        indexes = [
            models.Index(
                name="loyaltyindexes",
                fields=["-valid_from_date"],
                condition=Q(status="Active"),
            )
        ]


class LoyaltyAvailableOn(models.Model):
    """loyalty , stations relations table"""

    conditions = ((YES, YES), (NO, NO))
    id = models.AutoField(primary_key=True)
    loyalty_id = models.ForeignKey(
        Loyalty,
        null=True,
        on_delete=models.SET_NULL,
        related_name="station_available_loyalties",
        related_query_name="station_available_loyalties",
    )
    station_id = models.ForeignKey(
        Stations,
        null=True,
        on_delete=models.SET_NULL,
        related_name="station_loyalties",
        related_query_name="station_loyalties",
    )
    station_name = models.CharField(max_length=200, blank=True, null=True)
    operation_region = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    area = models.CharField(max_length=100, blank=True, null=True)
    deleted = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        """loaylty available on table"""

        db_table = "loyalties_available_on"
        indexes = [
            models.Index(
                name="loyaltystationsindexes",
                fields=["station_id", "loyalty_id"],
                condition=Q(deleted=NO),
            )
        ]

    def __str__(self):
        return str(self.station_name)


class LoyaltyProducts(models.Model):
    """loyalty product models"""

    conditions = ((YES, YES), (NO, NO))
    status = (
        ("Active", "Active"),
        ("Inactive", "Inactive"),
    )
    id = models.AutoField(primary_key=True)
    loyalty_id = models.ForeignKey(
        Loyalty,
        null=True,
        on_delete=models.SET_NULL,
        related_name="loyalty_products",
        related_query_name="loyalty_products",
    )
    product_plu = models.CharField(max_length=100, blank=True, null=True)
    product_bar_code = models.CharField(max_length=100, blank=True, null=True)
    desc = models.CharField(max_length=1000, blank=True, null=True)
    price = models.FloatField()
    redeem_product_promotion_price = models.FloatField(default=0)
    status = models.CharField(
        max_length=60, null=True, blank=True, choices=status
    )
    deleted = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return str(self.id)


class LoyaltyOccurrences(models.Model):
    """loyalty occurrences models"""

    conditions = ((YES, YES), (NO, NO))
    id = models.AutoField(primary_key=True)
    loyalty_id = models.ForeignKey(
        Loyalty,
        null=True,
        on_delete=models.SET_NULL,
        related_name="loyalty_occurrences",
        related_query_name="loyalty_occurrences",
    )
    date = models.DateTimeField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    deleted = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return str(self.id)


class UserLoyaltyTransactions(models.Model):
    """user loyalty transactions"""

    action_codes = (
        ("Purchased", "Purchased"),
        ("Redeemed", "Redeemed"),
        ("Burned", "Burned"),
    )
    user_transaction_id = models.AutoField(primary_key=True)
    loyalty_id = models.ForeignKey(
        Loyalty,
        null=True,
        on_delete=models.SET_NULL,
        related_name="user_loyalty_transactions",
        related_query_name="user_loyalty_transactions",
    )
    user_id = models.ForeignKey(
        MFGUserEV,
        null=True,
        on_delete=models.SET_NULL,
        related_name="user_wise_loyalties",
        related_query_name="user_wise_loyalties",
    )
    number_of_transactions = models.FloatField(default=0)
    transaction_ids = models.CharField(max_length=1000, blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    action_code = models.CharField(
        max_length=60, null=True, blank=True, choices=action_codes
    )
    expired_on = models.DateTimeField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return str(self.loyalty_id)


class LoyaltyTransactions(models.Model):
    """loyalty transactions"""

    action_codes = (
        ("Purchased", "Purchased"),
        ("Redeemed", "Redeemed"),
    )
    loyalty_transaction_id = models.AutoField(primary_key=True)
    loyalty_id = models.ForeignKey(
        Loyalty,
        null=True,
        on_delete=models.SET_NULL,
        related_name="loyalty_transactions",
        related_query_name="loyalty_transactions",
    )
    user_id = models.ForeignKey(
        MFGUserEV,
        null=True,
        on_delete=models.SET_NULL,
        related_name="user_loyalties",
        related_query_name="user_loyalties",
    )
    station_id = models.ForeignKey(
        Stations,
        null=True,
        on_delete=models.SET_NULL,
        related_name="station_loyalty_transacions",
        related_query_name="station_loyalties_transactions",
    )
    qr_code = models.CharField(max_length=1000, blank=True, null=True)
    transaction_response = models.TextField(null=True, blank=True)
    transaction_time = models.DateTimeField(blank=True, null=True)
    transaction_type = models.CharField(
        max_length=60, null=True, blank=True, choices=action_codes
    )
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    count_of_transactions = models.IntegerField(default=1)

    def __str__(self):
        return str(self.loyalty_id)


class LoyaltyBulkUpload(models.Model):
    """Bulk upload errorstable"""

    statuses = (
        (IN_PROGRESS, IN_PROGRESS),
        (QUEUED, QUEUED),
        (COMEPLETED, COMEPLETED),
        (NEED_REVIEW, NEED_REVIEW),
        (FAILED, FAILED),
    )
    conditions = ((YES, YES), (NO, NO))
    id = models.AutoField(primary_key=True)
    transaction_bulk_data = models.TextField()
    transaction_data_size = models.IntegerField()
    status = models.CharField(
        max_length=100,
        choices=statuses,
        default=QUEUED,
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        MFGUserEV,
        null=True,
        on_delete=models.SET_NULL,
    )
    is_reconciled = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return str(self.id)
