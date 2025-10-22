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
from ..constants import YES, NO
from .app_user_models import MFGUserEV


class Cards(models.Model):
    """cards model"""

    conditions = ((YES, YES), (NO, NO))
    user = models.ForeignKey(
        MFGUserEV,
        on_delete=models.CASCADE,
        related_name="user_cards",
        related_query_name="user_cards",
    )
    source_id = models.CharField(max_length=100, null=True)
    customer_id = models.CharField(max_length=100, null=True)
    cardholder_name = models.CharField(max_length=1000, null=True)
    postal_code = models.CharField(max_length=100, null=True)
    locality = models.CharField(max_length=1000, null=True)
    country = models.CharField(max_length=100, null=True)
    administrative_district_level_1 = models.CharField(
        max_length=1000, null=True
    )
    address_line_1 = models.CharField(max_length=1000, null=True)
    address_line_2 = models.CharField(max_length=1000, null=True)
    card_brand = models.CharField(max_length=1000, unique=True, null=True)
    last_4 = models.IntegerField()
    exp_month = models.IntegerField()
    exp_year = models.IntegerField()
    card_id = models.CharField(max_length=100, unique=True, null=True)
    card_type = models.CharField(max_length=100, unique=True, null=True)
    version = models.IntegerField()
    prepaid_type = models.CharField(max_length=100, unique=True, null=True)
    enabled = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
