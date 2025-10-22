"""models"""
# Date - 20/11/2022
# File details-
#   Author          - Shivkumar kumbhar
#   Description     - This file is mainly focused on
#                      creating database tables for
#                      notification module.
#   Name            - notifications module related models
#   Modified by     - Shivkumar kumbhar
#   Modified date   - 26/12/2022


# Imports required to make models are below
from decouple import config
from django.db import models
from ..constants import YES, NO
from django_ckeditor_5.fields import CKEditor5Field


class EmailAttachments(models.Model):
    "email attachment table"

    conditions = ((YES, YES), (NO, NO))

    attachment_id = models.AutoField
    attachment = models.FileField(upload_to="images", blank=True, null=True)
    attachment_size = models.IntegerField(blank=True, null=True)
    deleted = models.CharField(
        max_length=10, choices=conditions, default=NO, blank=True, null=True
    )

    def __str__(self):
        return str(self.attachment_id)

    def get_attachment(self):
        """get station image"""
        return f"{config('DJANGO_APP_CDN_BASE_URL')}{self.attachment}"


class EmailNotifications(models.Model):
    """notifications base table"""

    conditions = ((YES, YES), (NO, NO))

    assign_to = (
        ("All App Users", "All App Users"),
        ("Only Subscribed Users", "Only Subscribed Users"),
    )
    status = (
        ("Delivered", "Delivered"),
        ("Scheduled", "Scheduled"),
    )
    template = (
        ("Pre-release", "Pre-release"),
        ("Post-release", "Post-release"),
        ("Custom", "Custom"),
    )
    assign_to = models.CharField(
        max_length=60, null=True, blank=True, choices=assign_to
    )
    subject = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(null=True, blank=True)
    template = models.CharField(
        max_length=60, null=True, blank=True, choices=template
    )
    scheduled_time = models.DateTimeField(blank=True, null=True)
    delivered_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=60, null=True, blank=True, choices=status
    )
    description = CKEditor5Field(null=True, blank=True)
    email_attachments = models.ManyToManyField(EmailAttachments)
    deleted = models.CharField(
        max_length=10, choices=conditions, default=NO, blank=True, null=True
    )
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)
    email_preference = models.CharField(max_length=60, null=True, blank=True)
    user_list = models.TextField(null=True, blank=True)
    postcode = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return str(self.subject)


DEFAULT = "img/logo-black.png"


class PushNotifications(models.Model):
    """Push notifications base table"""

    status = (
        ("Delivered", "Delivered"),
        ("Scheduled", "Scheduled"),
    )
    conditions = ((YES, YES), (NO, NO))

    assign_to = models.TextField(null=True, blank=True)
    notification_for = models.CharField(max_length=60, null=True, blank=True)
    regions = models.CharField(max_length=255, null=True, blank=True)
    subject = models.CharField(max_length=255, null=True, blank=True)
    description = CKEditor5Field(null=True, blank=True)
    screens = models.CharField(max_length=255, null=True, blank=True)
    category = models.CharField(max_length=60, null=True, blank=True)
    push_notification = models.CharField(max_length=60, null=True, blank=True)
    inapp_notification = models.CharField(max_length=60, null=True, blank=True)
    image = models.ImageField(null=True, blank=True, default=DEFAULT)
    scheduled_time = models.DateTimeField(blank=True, null=True)
    delivered_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=60, null=True, blank=True)
    deleted = models.CharField(
        max_length=10, choices=conditions, default=NO, blank=True, null=True
    )
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)
    domain = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return str(self.subject)

    def get_push_notification_image(self):
        """get push_notification image"""
        return f"{config('DJANGO_APP_CDN_BASE_URL')}{self.image}"

    def set_image_to_default(self):
        if self.image:
            return self.image
        return DEFAULT
