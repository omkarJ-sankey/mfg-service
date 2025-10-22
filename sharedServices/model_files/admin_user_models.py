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
from decouple import config
from django.db import models
from ..constants import YES, NO


class Content(models.Model):
    """content model"""

    name = models.CharField(max_length=30, null=True)

    def __str__(self):
        return str(self.name)


class RoleAccessTypes(models.Model):
    """role access types model"""

    role_id = models.AutoField
    role_name = models.CharField(max_length=20, blank=True, null=True)
    access_content = models.ManyToManyField(Content)

    class Meta:
        """meta data"""

        db_table = "role_access_Types"

    def __str__(self):
        return str(self.role_name)


class AdminUser(models.Model):
    """admin user model"""

    conditions = ((YES, YES), (NO, NO))
    user_id = models.AutoField
    role_id = models.ForeignKey(
        RoleAccessTypes, null=True, on_delete=models.SET_NULL
    )
    phone = models.CharField(
        max_length=100, unique=False, null=True, blank=True
    )
    full_name = models.CharField(max_length=100, blank=True, null=True)
    user_name = models.CharField(
        max_length=100, unique=True, blank=True, null=True
    )
    email = models.CharField(
        max_length=100, unique=True, blank=True, null=True
    )
    profile_picture = models.ImageField(
        upload_to="images", blank=True, null=True
    )
    first_time_login = models.CharField(
        max_length=100, choices=conditions, default=YES, blank=True, null=True
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        """meta data"""

        db_table = "admin_user"

    def __str__(self):
        return str(self.full_name)

    def get_profile_picture(self):
        """get admin profile picture"""
        return (
            f"{config('DJANGO_APP_CDN_BASE_URL')}{self.profile_picture}"
            if self.profile_picture
            else ""
        )

    def get_username(self):
        """get admin user name"""
        return str(self.user_name)


class AdminAuthorization(models.Model):
    """admin user authorization details models"""

    user_id = models.ForeignKey(
        AdminUser, null=True, on_delete=models.SET_NULL
    )
    otp = models.CharField(
        max_length=100, blank=True, null=True, db_index=True
    )
    otp_type = models.CharField(
        max_length=20, blank=True, null=True, db_index=True
    )
    password = models.CharField(
        max_length=100, blank=True, null=True, db_index=True
    )
    token = models.CharField(
        max_length=1000, blank=True, null=True, db_index=True
    )
    token_secret = models.CharField(max_length=200, blank=True, null=True)
    refresh_token = models.CharField(
        max_length=1000, blank=True, null=True, db_index=True
    )
    token_expire_time = models.DateTimeField(
        null=True, blank=True, db_index=True
    )

    class Meta:
        """meta data"""

        db_table = "admin_authorization"

    def __str__(self):
        return str(self.user_id)


class LoginRecords(models.Model):
    """admin user login records"""

    status = (
        ("Active", "Active"),
        ("Inactive", "Inactive"),
    )
    user_id = models.ForeignKey(
        AdminUser, null=True, on_delete=models.SET_NULL
    )
    current_status = models.CharField(
        max_length=100, blank=True, choices=status
    )
    device_mac_address = models.CharField(
        max_length=100, blank=True, null=True
    )
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        """meta data"""

        db_table = "login_records"

    def __str__(self):
        return str(self.user_id)
