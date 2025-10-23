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
from ..constants import NO

# Audit trail models
class AuditTrail(models.Model):
    """audit trail model"""

    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(null=False, blank=False)
    user_name = models.CharField(max_length=1000, blank=True, null=True)
    user_role = models.CharField(max_length=1000, blank=True, null=True)
    action = models.CharField(max_length=1000, blank=True, null=True)
    module = models.CharField(max_length=100, null=True, blank=True)
    module_id = models.CharField(max_length=1000, null=True, blank=True)
    data_db_id = models.CharField(max_length=100, null=True, blank=True)
    changes_reference_id = models.CharField(max_length=100, null=True, blank=True)
    new_data = models.TextField(blank=True, null=True)
    previous_data = models.TextField(blank=True, null=True)
    review_status = models.CharField(max_length=100, null=True, blank=True, default=NO)
    reviewd_by = models.CharField(max_length=1000, blank=True, null=True)
    review_date = models.DateTimeField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return str(self.id)
