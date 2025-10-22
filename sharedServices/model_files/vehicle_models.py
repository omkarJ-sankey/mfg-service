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

from .app_user_models import MFGUserEV

class ElectricVehicleDatabase(models.Model):
    """Electric vehicle data"""

    ev_types = (("bev", "bev"), ("phev", "phev"))
    id = models.AutoField
    vehicle_id = models.CharField(max_length=70, null=True, blank=True)
    misc_body = models.CharField(max_length=150, null=True, blank=True)
    vehicle_make = models.CharField(max_length=150, null=True, blank=True)
    vehicle_model = models.CharField(max_length=150, null=True, blank=True)
    vehicle_model_version = models.CharField(
        max_length=150, null=True, blank=True
    )
    range_real = models.CharField(max_length=150, null=True, blank=True)
    battery_capacity_useable = models.CharField(
        max_length=150, null=True, blank=True
    )
    charge_plug = models.CharField(max_length=150, null=True, blank=True)
    fastcharge_plug = models.CharField(max_length=150, null=True, blank=True)
    fastcharge_chargespeed = models.CharField(
        max_length=150, null=True, blank=True
    )
    max_charge_speed = models.CharField(max_length=150, null=True, blank=True)
    ev_type = models.CharField(
        max_length=100, choices=ev_types, blank=True, null=True
    )
    ev_image = models.ImageField(upload_to="images", blank=True, null=True)
    ev_thumbnail_image = models.ImageField(
        upload_to="images/thumbnail/", blank=True, null=True
    )
    electric_vehicle_object = models.TextField()

    def __str__(self):
        return str(self.misc_body)

    def get_ev_image(self):
        """blob image path/location"""
        return f"{config('DJANGO_APP_CDN_BASE_URL')}{self.ev_image}"

    class Meta:
        """meta data"""

        indexes = [
            models.Index(
                name="electricvehicledatabaseindexes", fields=["vehicle_id"]
            ),
            models.Index(
                name="electricvehicleevtypeindexes", fields=["ev_type"]
            ),
        ]


class UserEVs(models.Model):
    """User EV vehicles data"""

    id = models.AutoField
    user_id = models.ForeignKey(
        MFGUserEV,
        null=True,
        on_delete=models.SET_NULL,
        related_name="ev_users",
        related_query_name="ev_users",
    )
    vehicle_id = models.ForeignKey(
        ElectricVehicleDatabase,
        null=True,
        on_delete=models.SET_NULL,
        related_name="user_evs",
        related_query_name="user_evs",
    )
    default = models.BooleanField(null=True, default=False)
    vehicle_registration_number = models.CharField(max_length=150, null=True, blank=True)
    vehicle_nickname = models.CharField(max_length=150, null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.vehicle_id.misc_body)
