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
from .station_models import Stations


# Promotions models
class Promotions(models.Model):
    """promotions model"""

    status = (
        ("Active", "Active"),
        ("Inactive", "Inactive"),
    )
    available = (
        ("App Only", "App Only"),
        ("Generic", "Generic"),
        ("All", "All"),
    )
    conditions = ((YES, YES), (NO, NO))
    promotion_id = models.AutoField(primary_key=True)
    unique_code = models.CharField(max_length=200, blank=True, null=True)
    retail_barcode = models.CharField(max_length=200, blank=True, null=True)
    product = models.CharField(max_length=200, blank=True, null=True)
    promotion_title = models.CharField(max_length=200, blank=True, null=True)
    m_code = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, choices=status)
    available_for = models.CharField(
        max_length=100, blank=True, choices=available
    )
    offer_type = models.CharField(max_length=200, blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    price = models.FloatField(default=0)
    quantity = models.IntegerField(default=0)
    londis_code = models.CharField(max_length=200, blank=True, null=True)
    budgen_code = models.CharField(max_length=200, blank=True, null=True)
    shop_ids = models.CharField(max_length=1000, blank=True, null=True)
    offer_details = models.CharField(max_length=500, blank=True, null=True)
    terms_and_conditions = models.CharField(
        max_length=500, blank=True, null=True
    )
    deleted = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    image = models.ImageField(upload_to="images", blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return str(self.promotion_title)

    def get_promotion_image(self):
        """get promotion image"""
        return f"{config('DJANGO_APP_CDN_BASE_URL')}{self.image}"

    class Meta:
        """meta data"""

        indexes = [
            models.Index(
                name="promotionsindexes",
                fields=["-start_date"],
                condition=Q(status="Active"),
            )
        ]


class PromotionsAvailableOn(models.Model):
    """promotions available on station"""

    conditions = ((YES, YES), (NO, NO))
    promotion_id = models.ForeignKey(
        Promotions,
        null=True,
        on_delete=models.SET_NULL,
        related_name="station_available_promotions",
        related_query_name="station_available_promotions",
    )
    station_id = models.ForeignKey(
        Stations,
        null=True,
        on_delete=models.SET_NULL,
        related_name="station_promotions",
        related_query_name="station_promotions",
    )
    station_name = models.CharField(max_length=200, blank=True, null=True)
    operation_region = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    area = models.CharField(max_length=100, blank=True, null=True)
    deleted = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        """meta data"""

        db_table = "promotions_available_on"
        indexes = [
            models.Index(
                name="promotionstationsindexes",
                fields=["station_id", "promotion_id"],
                condition=Q(deleted=False),
            )
        ]

    def __str__(self):
        return str(self.station_name)


class PromotionImages(models.Model):
    """promotion images"""

    conditions = ((YES, YES), (NO, NO))
    promotion_id = models.ForeignKey(
        Promotions, null=True, on_delete=models.SET_NULL
    )
    image_path = models.ImageField(upload_to="images", blank=True, null=True)
    image_width = models.IntegerField(default=0)
    image_height = models.IntegerField(default=0)
    deleted = models.CharField(
        max_length=100,
        choices=conditions,
        default=NO,
        blank=True,
        null=True,
    )
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        """meta data"""

        db_table = "promotion_images"

    def __str__(self):
        return str(self.promotion_id)

    def get_promotion_image(self):
        """get promotion image"""
        return f"{config('DJANGO_APP_CDN_BASE_URL')}{self.image_path}"
