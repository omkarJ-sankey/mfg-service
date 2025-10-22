"""models"""
# Date - 28/04/2025
# File details-
#   Author          - Abhinav Shivalkar
#   Description     - This file is mainly focused on
#                      creating database tables for
#                      OCPI tariffs module.
#   Name            - OCPI tariff module related models
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 05/05/2025
 
from django.db import models


class Tariffs(models.Model):

    tariff_type = (
        ("AD_HOC_PAYMENT", "AD_HOC_PAYMENT"),
        ("PROFILE_CHEAP", "PROFILE_CHEAP"),
        ("PROFILE_FAST", "PROFILE_FAST"),
        ("PROFILE_GREEN", "PROFILE_GREEN"),
        ("REGULAR", "REGULAR"),
    )
    id = models.AutoField(primary_key=True)
    tariff_id = models.CharField(max_length=36)
    country_code = models.CharField(max_length=2)
    party_id = models.CharField(max_length=10)
    currency = models.CharField(max_length=10)
    type = models.CharField(max_length=20,choices=tariff_type, blank=False, null=True)
    tariff_alt_url = models.CharField(max_length=512, blank=True, null=True)
    tariff_alt_text = models.TextField(blank=True, null=True)
    min_price_incl_vat = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    max_price_incl_vat = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    min_price_excl_vat = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    max_price_excl_vat = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    start_date_time = models.DateTimeField(blank=True, null=True)
    end_date_time = models.DateTimeField(blank=True, null=True)
    energy_mix = models.TextField(blank=True, null=True)
    last_updated = models.DateTimeField()

    class Meta:
        # unique_together = ('country_code', 'party_id', 'tariff_id')
        constraints = [
            models.UniqueConstraint(fields=['country_code', 'party_id','tariff_id'], name='unique_tariff_id_party_id_country_code')
        ]

    
class TariffElements(models.Model):
    id = models.AutoField(primary_key=True)
    tariff_id = models.ForeignKey(
        Tariffs, 
        null=False,
        on_delete=models.CASCADE,
        related_name="tariff_element",
        related_query_name="tariff_element")
    class Meta:
        db_table = 'sharedServices_tariffelements'
        # unique_together = ('tariff_id',)
        # constraints = [
        #     models.UniqueConstraint(fields=['tariff_id',], name='unique_tariff_id')
        # ]



class TariffRestrictions(models.Model):
    id = models.AutoField(primary_key=True)
    element_id = models.ForeignKey(
        TariffElements,
        null=False,
        on_delete=models.CASCADE,
        related_name="tariff_restriction",
        related_query_name="tariff_restriction")
    start_time = models.CharField(max_length=5,blank=True, null=True)
    end_time = models.CharField(max_length=5,blank=True, null=True)
    start_date = models.CharField(max_length=10,blank=True, null=True)
    end_date = models.CharField(max_length=10,blank=True, null=True)
    min_kwh = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    max_kwh = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    min_current = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    max_current = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    min_power = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    max_power = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    min_duration = models.IntegerField(blank=True, null=True)
    max_duration = models.IntegerField(blank=True, null=True)
    reservation = models.BooleanField(blank=True, null=True)
    reservation_expiry = models.BooleanField(blank=True, null=True)
    day_of_week = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        # unique_together = ('element_id', 'day_of_week')
        constraints = [
            models.UniqueConstraint(fields=['element_id', 'day_of_week'], name='unique_day_of_week_element_id')
        ]


class TariffComponents(models.Model):
    component_type = (
        ("ENERGY", "ENERGY"),
        ("FLAT", "FLAT"),
        ("PARKING_TIME", "PARKING_TIME"),
        ("TIME", "TIME")
    )
    id = models.AutoField(primary_key=True)
    element_id = models.ForeignKey(
        TariffElements, 
        null=False,
        on_delete=models.CASCADE,
        related_name="tariff_component",
        related_query_name="tariff_component")
    type = models.CharField(max_length=20,choices=component_type, blank=False, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    vat = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    step_size = models.IntegerField(blank=True, null=True)
    class Meta:
        # unique_together = ('element_id', 'type')
        constraints = [
            models.UniqueConstraint(fields=['element_id', 'type'], name='unique_type_element_id')
        ]