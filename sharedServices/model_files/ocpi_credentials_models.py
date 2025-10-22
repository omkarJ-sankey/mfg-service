"""models"""
# Date - 23/04/2025
# File details-
#   Author          - Abhinav Shivalkar
#   Description     - This file is mainly focused on
#                      creating database tables for
#                      OCPI Credentials module.
#   Name            - OCPI Credentials module related models
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 23/04/2025


from decouple import config
from django.db import models
from ..constants import YES, NO
import uuid


class OCPICredentialsRole(models.Model):
    "OCPI credentials roles table"

    id = models.AutoField
    role = models.CharField(
        max_length=10, blank=True, null=True
    )
    business_details = models.CharField(
        max_length=50, blank=True, null=True
    )
    created_date = models.DateTimeField(blank=False, null=False)
    updated_date = models.DateTimeField(blank=False, null=False)
    updated_by = models.CharField(max_length=100, blank=False, null=False)
    party_id = models.CharField(
        max_length=50, blank=False, null=False
    )
    country_code = models.CharField(
        max_length=50, blank=False, null=False
    )
    credential_id = models.BigIntegerField(blank=True,null=True)

class OCPICredentials(models.Model):
    "OCPI credentials table"

    status_val = (
        ("Active", "Active"),
        ("Inactive", "Inactive"),
        ("Initiated", "Initiated"),
        ("Failed", "Failed"),
    )
    id = models.AutoField
    name = models.CharField(
        max_length=100, blank=False, null=False
    )
    endpoint = models.CharField(
        max_length=255, blank=False, null=False
    )
    token_a = models.CharField(max_length=100, blank=True, null=True)
    cpo_token = models.CharField(max_length=100, blank=True, null=True)
    emsp_token = models.CharField(max_length=100, blank=True, null=True)
    created_date = models.DateTimeField(blank=False, null=False)
    updated_date = models.DateTimeField(blank=False, null=False)
    updated_by = models.CharField(max_length=100, blank=False, null=False)
    from_role = models.ForeignKey(
        OCPICredentialsRole,
        null=True,
        on_delete=models.SET_NULL,
        related_name="ocpi_credentials_from_role",
        related_query_name="ocpi_credentials_from_role",
    )
    to_role = models.ForeignKey(
        OCPICredentialsRole,
        null=True,
        on_delete=models.SET_NULL,
        related_name="ocpi_credentials_to_role",
        related_query_name="ocpi_credentials_to_role",
    )
    # x_request_id = models.IntegerField(blank=False, null=False)
    # x_correlation_id = models.IntegerField(blank=False, null=False) 
    status = models.CharField(
        max_length=10,choices=status_val, blank=False, null=False
    )

class OCPIModuleDetails(models.Model):
    id = models.AutoField(primary_key=True)
    credential_id = models.ForeignKey(
        OCPICredentials,
        on_delete=models.CASCADE,
        related_name='credentials'
    )
    identifier = models.CharField(max_length=100)
    url = models.CharField(max_length=100)
    role = models.CharField(max_length=50)
    version = models.CharField(max_length=10, default="2.2.1")
    