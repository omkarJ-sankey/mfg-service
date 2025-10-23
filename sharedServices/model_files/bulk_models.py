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


class BulkUploadProgress(models.Model):
    """Bulk upload progress bar indicator table"""

    id = models.AutoField(primary_key=True)
    uploaded_for = models.CharField(max_length=100, null=True, blank=True)
    total_rows_count = models.CharField(max_length=1000, blank=True, null=True)
    uploaded_rows_count = models.CharField(
        max_length=100, null=True, blank=True
    )
    uploading_status = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return str(self.id)


class BulkUploadErrorMessages(models.Model):
    """Bulk upload errorstable"""

    conditions = ((YES, YES), (NO, NO))
    id = models.AutoField(primary_key=True)
    uploaded_for = models.CharField(max_length=100, null=True, blank=True)
    errors = models.TextField()
    ready_to_export = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    created_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return str(self.id)
