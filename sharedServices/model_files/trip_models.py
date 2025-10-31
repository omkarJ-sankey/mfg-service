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
from django.core.validators import MaxValueValidator, MinValueValidator
from ..constants import YES, NO
from .app_user_models import MFGUserEV

# Trip planner models
class Trips(models.Model):
    """trip's data model"""

    conditions = ((YES, YES), (NO, NO))
    trip_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(
        MFGUserEV,
        null=True,
        on_delete=models.SET_NULL,
        related_name="user_trips",
        related_query_name="user_trips",
    )
    source = models.CharField(max_length=100, blank=True, null=True)
    destination = models.CharField(max_length=100, blank=True, null=True)
    miles = models.CharField(max_length=100, blank=True, null=True)
    duration = models.CharField(max_length=100, blank=True, null=True)
    ev_range = models.IntegerField(default=0)
    ev_battery = models.IntegerField(
        default=0, validators=[MaxValueValidator(100), MinValueValidator(1)]
    )
    ev_current_battery = models.IntegerField(
        default=1, validators=[MaxValueValidator(100), MinValueValidator(1)]
    )
    add_stop_automatically = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    add_spot_place_id = models.CharField(max_length=100, blank=True, null=True)
    favourite = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    saved = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    store_id = models.CharField(max_length=600, blank=True, null=True)
    amenity_id = models.CharField(max_length=600, blank=True, null=True)
    charging_types = models.CharField(max_length=600, blank=True, null=True)
    station_distance = models.IntegerField(
        default=1, validators=[MaxValueValidator(100), MinValueValidator(1)]
    )
    fuel_station_type = models.CharField(max_length=600, blank=True, null=True)
    trip_options_filter = models.CharField(
        max_length=600, blank=True, null=True
    )
    connector_type_id = models.CharField(max_length=600, blank=True, null=True)
    trip_data = models.TextField(blank=True, null=True)
    stations_data = models.CharField(max_length=600, blank=True, null=True)
    is_electric = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    deleted = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return str(self.user_id)
