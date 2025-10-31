"""models"""
# Date - 21/06/2021
# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on
#                       creating database tables for
#                       third party user models module.
#   Name            - Third party user  models
#   Modified by     - Manish Pawar
#   Modified date   - 26/06/2021


# Imports required to make models are below
from django.db import models
from .app_user_models import MFGUserEV


class ThirdPartyCredentials(models.Model):
    """third party credentials"""

    disable_status = (
        ("Yes", "Yes"),
        ("No", "No"),
    )
    third_party_user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=500, blank=True, null=True)
    owner = models.CharField(max_length=500, blank=True, null=True)
    token = models.CharField(max_length=1000, blank=True, null=True)
    refresh_token = models.CharField(max_length=1000, blank=True, null=True)
    disabled = models.CharField(
        max_length=60,
        null=True,
        default="No",
        blank=True,
        choices=disable_status,
    )
    user_id = models.ForeignKey(
        MFGUserEV, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return str(self.third_party_user_id)
