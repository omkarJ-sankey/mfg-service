"""models"""
# Date - 23/04/2025
# File details-
#   Author          - Abhinav Shivalkar
#   Description     - This file is mainly focused on
#                      creating database tables for
#                      OCPI CDR module.
#   Name            - OCPI Credentials module related models
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 25/06/2025

from django.db import models
from .ocpi_sessions_models import OCPISessions


class OCPIChargeDetailRecords(models.Model):
    "OCPI credentials roles table"

    auth_method = (
        ("AUTH_REQUEST","AUTH_REQUEST"),
        ("COMMAND","COMMAND"),
        ("WHITELIST","WHITELIST"),
    )

    id = models.AutoField(primary_key=True)
    party_id = models.CharField(
        max_length=3, blank=False, null=False
    )
    country_code = models.CharField(
        max_length=2, blank=False, null=False
    )
    cdr_id = models.CharField(
        max_length=39, blank=False, null=False
    )
    start_date_time = models.DateTimeField(blank=False, null=False)
    end_date_time = models.DateTimeField(blank=False, null=False)
    session_id = models.CharField(
        max_length=36, blank=True, null=True
    )
    cdr_token = models.TextField(blank=False, null=False)
    auth_method = models.CharField(max_length=20,choices=auth_method,blank=False, null=False)
    authorization_reference = models.CharField(
        max_length=36, blank=True, null=True
    )
    cdr_location = models.TextField()
    meter_id = models.CharField(
        max_length=255, blank=True, null=True
    )
    currency = models.CharField(max_length=3)
    tariffs = models.TextField(null=True,blank=True)
    charging_periods = models.TextField(null=False,blank=False)
    signed_data = models.JSONField(null=True,blank=True)
    total_cost = models.TextField(blank=False,null=False)
    total_fixed_cost = models.TextField(null=True,blank=True)
    total_energy = models.DecimalField(max_digits=12, decimal_places=4,blank=False, null=False)
    total_energy_cost = models.TextField(null=True,blank=True)
    total_time = models.DecimalField(max_digits=12, decimal_places=4,blank=True, null=True)
    total_time_cost = models.JSONField(null=True, blank=True)
    total_parking_time = models.DecimalField(max_digits=12, decimal_places=4,blank=True, null=True)
    total_parking_cost = models.TextField(null=True,blank=True)
    total_reservation_cost = models.TextField(null=True,blank=True)
    remark = models.CharField(
        max_length=255, blank=True, null=True
    )
    invoice_reference_id = models.CharField(
        max_length=39, blank=True, null=True
    )
    credit = models.BooleanField(null=True,blank=True)
    credit_reference_id = models.CharField(
        max_length=39, blank=True, null=True
    )
    home_charging_compensation = models.BooleanField(null=True,blank=True)
    last_updated = models.DateTimeField(blank=False, null=False)
    charging_session_id = models.ForeignKey(
        OCPISessions,
        null=True,
        on_delete=models.SET_NULL,
        related_name="cdr_session",
        related_query_name="cdr_session",)
    created_date = models.DateTimeField(blank=False, null=False,auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['cdr_id', 'country_code', 'party_id'], name='unique_cdr_id_country_code_party_id')
        ]



