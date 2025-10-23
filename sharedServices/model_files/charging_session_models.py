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
from django.core.validators import MaxValueValidator, MinValueValidator
from ..constants import YES, NO
from .station_models import Stations, ChargePoint, StationConnector
from .app_user_models import MFGUserEV
from .admin_user_models import AdminUser
from .ocpi_sessions_models import OCPISessions 


# dashboard models


class ChargingSession(models.Model):
    """charging sessions model"""

    status = (
        ("start", "start"),
        ("running", "running"),
        ("rejected", "rejected"),
        ("stopped", "stopped"),
        ("closed", "closed"),
        ("completed", "completed"),
    )
    pay_status = (
        ("paid", "paid"),
        ("unpaid", "unpaid"),
        ("refunded", "refunded")
    )
    mail_sent_status = (
        ("pending", "pending"),
        ("sent", "sent"),
    )
    conditions = ((YES, YES), (NO, NO))
    payment_source_conditions = (("Admin", "Admin"), ("App", "App"))
    payment_types = (
        ("Combined", "Combined"),
        ("Partial", "Partial"),
        ("non wallet", "non wallet"),
    )
    session_id = models.AutoField(primary_key=True)
    start_time = models.DateTimeField(null=True, blank=True)
    station_id = models.ForeignKey(
        Stations,
        null=True,
        on_delete=models.SET_NULL,
        related_name="station_charging_sessions",
        related_query_name="station_charging_sessions",
    )
    chargepoint_id = models.ForeignKey(
        ChargePoint,
        null=True,
        on_delete=models.SET_NULL,
        related_name="charging_sessions_chargepoints",
        related_query_name="charging_sessions_chargepoints",
    )
    connector_id = models.ForeignKey(
        StationConnector,
        null=True,
        on_delete=models.SET_NULL,
        related_name="charging_sessions_connectors",
        related_query_name="charging_sessions_connectors",
    )
    user_id = models.ForeignKey(
        MFGUserEV,
        null=True,
        on_delete=models.SET_NULL,
        related_name="user_charging_sessions",
        related_query_name="user_charging_sessions",
    )
    user_account_number = models.IntegerField(null=True, blank=True)
    user_card_number = models.CharField(
        max_length=500, null=True, blank=True
    )
    emp_session_id = models.CharField(
        max_length=500, unique=True, null=True, blank=True
    )
    charging_session_id = models.CharField(
        max_length=500, unique=True, null=True, blank=True
    )
    charging_authorization_status = models.CharField(
        max_length=500, null=True, blank=True
    )
    session_status = models.CharField(
        max_length=100, blank=True, choices=status
    )
    payment_id = models.CharField(max_length=1000, unique=False, null=True)
    paid_status = models.CharField(
        max_length=100, blank=True, default="unpaid", choices=pay_status
    )
    payment_method = models.CharField(max_length=100, unique=False, null=True)
    payment_response = models.TextField(null=True, blank=True)
    charging_data = models.TextField(null=True, blank=True)
    user_mail = models.BinaryField(blank=True, null=True)
    mail_status = models.CharField(
        max_length=100, blank=True, default="pending", choices=mail_sent_status
    )
    total_cost = models.CharField(max_length=100, blank=True, null=True)
    feedback = models.CharField(max_length=500, null=True, blank=True)
    rating = models.IntegerField(
        default=0, validators=[MaxValueValidator(5), MinValueValidator(1)]
    )
    back_office = models.CharField(max_length=30, null=True, blank=True)
    is_reviewed = models.CharField(
        max_length=100,
        choices=payment_source_conditions,
        default="App",
        blank=True,
        null=True,
    )
    is_force_stopped = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    is_refund_initiated = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    end_time = models.DateTimeField(null=True, blank=True)
    payment_completed_at = models.DateTimeField(null=True, blank=True)
    preauth_status = models.CharField(max_length=100, unique=False, null=True)
    preauth_collected_by = models.CharField(
        max_length=100, unique=False, null=True
    )
    session_tariff = models.CharField(max_length=30, blank=True, null=True)
    payment_type = models.CharField(max_length=100, unique=False, null=True)
    deducted_voucher_amount = models.CharField(
        max_length=20, null=True, blank=True
    )

    def __str__(self):
        return str(self.emp_session_id)

    class Meta:
        """meta data"""

        indexes = [
            models.Index(
                name="chargingsessionidindexes", fields=["emp_session_id"]
            ),
            models.Index(
                name="chargingsessionendtimeindexes", fields=["end_time"]
            ),
        ]


class ThreeDSTriggerLogs(models.Model):
    """user 3DS trigger logs"""

    three_ds_trigger_cycle_status = (
        ("Triggered", "Triggered"),
        ("Running", "Running"),
        ("Completed", "Completed")
    )
    user_id = models.ForeignKey(
        MFGUserEV,
        on_delete=models.CASCADE,
        related_name="user_3ds_trigger_logs",
        related_query_name="user_3ds_trigger_logs",
    )
    reason_for_3ds = models.CharField(max_length=100, blank=True, null=True)
    reason_for_3ds_kwh = models.CharField(max_length=100, blank=True, null=True)
    reason_for_3ds_days = models.CharField(max_length=100, blank=True, null=True)
    reason_for_3ds_transactions = models.CharField(max_length=100, blank=True, null=True)
    configuration_set_by_admin_for_3ds = models.CharField(
        max_length=100, blank=True, null=True
    )
    configuration_set_by_admin_for_3ds_kwh = models.CharField(
        max_length=100, blank=True, null=True
    )
    configuration_set_by_admin_for_3ds_days = models.CharField(
        max_length=100, blank=True, null=True
    )
    configuration_set_by_admin_for_3ds_transactions = models.CharField(
        max_length=100, blank=True, null=True
    )
    remaining_3ds_check_transaction = models.IntegerField(
        default=0, null=True
    )
    status = models.CharField(
        max_length=100,
        choices=three_ds_trigger_cycle_status,
        default="Triggered",
        blank=True,
        null=True
    )
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return str(self.user_id)


class ThreeDSCheckLogs(models.Model):
    """user 3DS check logs"""

    three_ds_check_status = (
        ("Successful", "Successful"),
        ("Failed", "Failed"),
    )

    three_ds_trigger_log_id = models.ForeignKey(
        ThreeDSTriggerLogs,
        on_delete=models.CASCADE,
        null=True,
    )
    session_id = models.ForeignKey(
        ChargingSession,
        on_delete=models.CASCADE,
        related_name="user_3ds_check_logs",
        related_query_name="user_3ds_check_logs",
        null=True
    )
    status = models.CharField(
        max_length=100,
        choices=three_ds_check_status,
        default="Successful",
        blank=True,
        null=True
    )
    created_date = models.DateTimeField(blank=True, null=True)
    ocpi_session_id = models.ForeignKey(
        OCPISessions,
        on_delete=models.CASCADE,
        related_name="user_3ds_check_logs_ocpi",
        related_query_name="user_3ds_check_logs_ocpi",
        null=True
    )

    def __str__(self):
        return str(self.session_id)


class SessionTransactionStatusTracker(models.Model):
    """charging sessions status tracking model"""

    statuses = (
        ("Successful", "Successful"),
        ("Failed", "Failed"),
    )

    transaction_id = models.AutoField(primary_key=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    comment = models.CharField(max_length=1000, null=True, blank=True)
    status = models.CharField(
        max_length=100,
        choices=statuses,
        default="Successful",
        blank=True,
        null=True,
    )
    created_date = models.DateTimeField(blank=True, null=True)
    added_by = models.ForeignKey(
        AdminUser, null=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return str(self.session_id)


class SwarcoDynamicData(models.Model):
    """swarco dynamic data model"""

    id = models.AutoField(primary_key=True)
    chargepoint_name = models.CharField(max_length=600, blank=True, null=True)
    chargepoint_status = models.CharField(max_length=60, null=True, blank=True)

    def __str__(self):
        return str(self.id)


class PaidPaymentLogs(models.Model):
    """This table stores the paid payment logs"""

    user = models.ForeignKey(MFGUserEV, null=True, on_delete=models.SET_NULL)
    charging_session = models.ForeignKey(
        ChargingSession, null=True, on_delete=models.SET_NULL
    )
    charging_session_ocpi = models.ForeignKey(
        OCPISessions, null=True, on_delete=models.SET_NULL
    )
    payment_id = models.CharField(max_length=1000, null=True)
    paid_due_amount = models.CharField(max_length=100, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
