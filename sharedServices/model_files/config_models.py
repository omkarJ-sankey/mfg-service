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
from django.db.models import Q
from ..constants import YES, NO


# All configrutions related to connectors store here
class ConnectorConfiguration(models.Model):
    """Connctor model"""

    connector_id = models.AutoField(primary_key=True)
    image_path = models.ImageField(upload_to="images", blank=True, null=True)
    alternate_image_path = models.ImageField(
        upload_to="images", blank=True, null=True
    )
    connector_plug_type = models.CharField(
        max_length=30, blank=True, null=True
    )
    connector_plug_type_name = models.CharField(
        max_length=30, blank=True, null=True
    )
    deleted = models.CharField(max_length=30, blank=True, null=True)
    sorting_order = models.IntegerField(default=0)
    for_app_version = models.IntegerField(default=0)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        """meta data"""

        db_table = "connector_configuration"
        indexes = [
            models.Index(
                name="connectorsindexes",
                fields=["connector_plug_type"],
                condition=Q(deleted=False),
            )
        ]

    def __str__(self):
        return str(self.connector_id)

    def get_image_path(self):
        """blob image path/location"""
        if self.image_path:
            return f"{config('DJANGO_APP_CDN_BASE_URL')}{self.image_path}"
        return "https://mfg-ev-qa.azureedge.net/media/images/CHAdeMO_9lq0n0xl6cZ0lKr.png"

    def get_alt_image_path(self):
        """blob image path/location"""
        if self.alternate_image_path:
            return f"{config('DJANGO_APP_CDN_BASE_URL')}{self.alternate_image_path}"
        return "https://mfg-ev-qa.azureedge.net/media/images/alt_CHAdeMO_nz4cHUxzGkPMXHm.png"


# All configrutions related to services store in
# this table(shops, amenities)


class ServiceConfiguration(models.Model):
    """Services models (shops)"""

    service_id = models.AutoField(primary_key=True)
    service_name = models.CharField(max_length=100, blank=True, null=True)
    image_path = models.ImageField(upload_to="images", blank=True, null=True)
    image_path_with_text = models.ImageField(
        upload_to="images", blank=True, null=True
    )
    service_type = models.CharField(max_length=30, blank=True, null=True)
    service_unique_identifier = models.IntegerField(default=0)
    deleted = models.CharField(max_length=30, blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        """meta data"""

        db_table = "service_configuration"
        indexes = [
            models.Index(
                name="servicesindexes",
                fields=["service_type", "service_name"],
                condition=Q(deleted=False),
            )
        ]

    def __str__(self):
        return str(self.service_id)

    def get_image_path(self):
        """blob image path/location"""
        return f"{config('DJANGO_APP_CDN_BASE_URL')}{self.image_path}"

    def get_image_path_with_text(self):
        """amenity image with text path/location"""
        return (
            f"{config('DJANGO_APP_CDN_BASE_URL')}{self.image_path_with_text}"
        )


class BaseConfigurations(models.Model):
    """base configuration values"""

    add_to_cache_conditions = ((YES, YES), (NO, NO))
    frequently_used_conditions = ((YES, YES), (NO, NO))
    base_configuration_id = models.AutoField(primary_key=True)
    base_configuration_key = models.CharField(
        max_length=100, blank=True, null=True
    )
    base_configuration_name = models.CharField(
        max_length=100, blank=True, null=True
    )
    base_configuration_value = models.TextField(
        blank=True, null=True
    )
    description = models.TextField(blank=True, null=True)
    base_configuration_image = models.ImageField(
        upload_to="images", blank=True, null=True
    )
    add_to_cache = models.CharField(
        max_length=100,
        choices=add_to_cache_conditions,
        default=NO,
        blank=True,
        null=True
    )
    frequently_used = models.CharField(
        max_length=100,
        choices=frequently_used_conditions,
        default=NO,
        blank=True,
        null=True
    )
    for_app_version = models.IntegerField(default=0)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        """meta data"""

        db_table = "base_configurations"
        indexes = [models.Index(fields=["base_configuration_key"])]

    def get_image(self):
        """get station image"""
        if self.base_configuration_image:
            return f"{config('DJANGO_APP_CDN_BASE_URL')}{self.base_configuration_image}"
        return "https://mfg-ev-qa.azureedge.net/media/images/Esso_____________________________________________D0ptw0WdSSBBU0w.png"


class MapMarkerConfigurations(models.Model):
    """model for map markers/brand logos"""

    map_marker_id = models.AutoField(primary_key=True)
    map_marker_key = models.CharField(max_length=100, blank=True, null=True)
    map_marker_image = models.ImageField(upload_to="images")
    small_map_marker_image = models.ImageField(upload_to="images", null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        """meta data"""

        db_table = "map_marker_configurations"
        indexes = [models.Index(fields=["map_marker_key"])]

    def get_image_path(self):
        """blob image path/location"""
        if self.map_marker_image:
            return f"{config('DJANGO_APP_CDN_BASE_URL')}{self.map_marker_image}"
        return "https://mfg-ev-qa.azureedge.net/media/images/Fuel_Site_oxmTaDjokqqnzPY.png"

    def get_small_image_path(self):
        """blob image path/location"""
        if self.small_map_marker_image:
            return f"{config('DJANGO_APP_CDN_BASE_URL')}{self.small_map_marker_image}"
        return "https://mfg-ev-qa.azureedge.net/media/images/Fuel_Site_oxmTaDjokqqnzPY.png"
