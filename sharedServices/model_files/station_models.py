"""models"""
# Date - 21/06/2021
# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on
#                       creating database tables for
#                       all modules.
#   Name            - Authentication related models
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 25/06/2025


# Imports required to make models are below
from decouple import config
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.db.models import Q
from django.core.validators import MaxValueValidator, MinValueValidator
from ..constants import YES, NO
from .config_models import ServiceConfiguration
from .app_user_models import MFGUserEV

# station configuration


def validate_min_length(stri):
    """min length validator"""
    if len(stri) < 4:
        raise ValidationError(
            _("%(value)s is  short please enter atleast 5 characters"),
            params={"value": stri},
        )


class Stations(models.Model):
    """Station model"""

    conditions = ((YES, YES), (NO, NO))
    station_dbid = models.AutoField
    station_id = models.CharField(
        max_length=15,
        unique=True,
        validators=[validate_min_length],
        default="",
    )
    station_name = models.CharField(
        max_length=200, validators=[validate_min_length], default=""
    )
    station_address1 = models.CharField(
        max_length=500, validators=[validate_min_length], default=""
    )
    station_address2 = models.CharField(
        max_length=500, validators=[validate_min_length], default=""
    )
    station_address3 = models.CharField(
        max_length=500, validators=[validate_min_length], default=""
    )
    town = models.CharField(
        max_length=100, validators=[validate_min_length], default=""
    )
    post_code = models.CharField(
        max_length=50, validators=[validate_min_length], default=""
    )
    country = models.CharField(
        max_length=100, validators=[validate_min_length], default=""
    )
    brand = models.CharField(
        max_length=100, validators=[validate_min_length], default=""
    )
    owner = models.CharField(
        max_length=100, validators=[validate_min_length], default=""
    )
    latitude = models.FloatField(default=0)
    longitude = models.FloatField(default=0)
    email = models.CharField(
        max_length=100, validators=[validate_min_length], default=""
    )
    phone = models.CharField(
        max_length=30, validators=[validate_min_length], default=""
    )
    status = models.CharField(
        max_length=30, validators=[validate_min_length], default=""
    )
    station_type = models.CharField(
        max_length=30, validators=[validate_min_length], default=""
    )
    site_title = models.CharField(
        max_length=120, validators=[validate_min_length], default=""
    )
    # driivz_display_name is added to show the site names in contactless receipt
    driivz_display_name = models.CharField(
        max_length=120, null=True, blank=True
    )
    operation_region = models.CharField(
        max_length=100, validators=[validate_min_length], default=""
    )
    region = models.CharField(
        max_length=100, validators=[validate_min_length], default=""
    )
    regional_manager = models.CharField(
        max_length=120, validators=[validate_min_length], default=""
    )
    area = models.CharField(
        max_length=100, validators=[validate_min_length], default=""
    )
    area_regional_manager = models.CharField(
        max_length=120, validators=[validate_min_length], default=""
    )
    deleted = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    is_mfg = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    is_ev = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    available_promotion = models.TextField(default="[]")
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(
        max_length=100, validators=[validate_min_length], default=""
    )
    site_id = models.CharField(max_length=30, null=True, blank=True)
    valeting = models.CharField(max_length=30, null=True, blank=True,default=NO)
    payment_terminal = models.CharField(max_length=120, null=True, blank=True)
    receipt_hero_site_name = models.CharField(max_length=100, null=True, blank=True)
    ev_station_status = models.CharField(max_length=100, null=True, blank=True)
    overstay_fee = models.FloatField(default=0, null=True)
    parking_details = models.CharField(max_length=1000, null=True, blank=True)
    valeting_site_id = models.CharField(max_length=30, null=True, blank=True)
    ocpi_locations = models.JSONField(null = True, blank = True)
    ampeco_site_id = models.CharField(max_length=30, null=True, blank=True)
    ampeco_site_title = models.CharField(max_length=100, null=True, blank=True)
    ocpi_location_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return str(self.station_id)

    def get_full_address(self):
        """get station address"""
        address = ""
        if (
            len(self.station_address1) > 0
            and self.station_address1
            and self.station_address1 != "nan"
        ):
            address += str(self.station_address1)

        if (
            len(self.station_address2) > 0
            and self.station_address2
            and self.station_address2 != "nan"
        ):
            if len(address) > 0:
                address += f", {self.station_address2}"
            else:
                address += str(self.station_address2)

        if (
            len(self.station_address3) > 0
            and self.station_address3
            and self.station_address3 != "nan"
        ):
            if len(address) > 0:
                address += f", {self.station_address3}"
            else:
                address += str(self.station_address3)
        if len(self.town) > 0 and self.town and self.town != "nan":
            if len(address) > 0:
                address += f", {self.town}"
            else:
                address += str(self.town)
        if (
            len(self.post_code) > 0
            and self.post_code
            and self.post_code != "nan"
        ):
            if len(address) > 0:
                address += f", {self.post_code}"
            else:
                address += str(self.post_code)
        return address

    class Meta:
        """meta data"""

        indexes = [
            models.Index(
                name="stationsindex",
                fields=["latitude", "longitude"],
                condition=Q(status="Active"),
            )
        ]


class StationWorkingHours(models.Model):
    """station working hours model"""

    conditions = ((YES, YES), (NO, NO))
    station_working_hours_id = models.AutoField
    station_id = models.ForeignKey(
        Stations,
        null=True,
        on_delete=models.SET_NULL,
        related_name="working_hours_details",
        related_query_name="working_hours_details",
    )
    monday_friday = models.CharField(
        max_length=30, validators=[validate_min_length], default=""
    )
    saturday = models.CharField(
        max_length=30, validators=[validate_min_length], default=""
    )
    sunday = models.CharField(
        max_length=30, validators=[validate_min_length], default=""
    )
    deleted = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(
        max_length=100, validators=[validate_min_length], default=""
    )

    class Meta:
        """meta data"""

        db_table = "station_working_hours"


class ChargePoint(models.Model):
    """chargepoint model"""

    conditions = ((YES, YES), (NO, NO))
    charge_point_id = models.AutoField
    station_id = models.ForeignKey(
        Stations,
        null=True,
        on_delete=models.SET_NULL,
        related_name="charge_points",
        related_query_name="charge_points",
    )
    charger_point_id = models.CharField(
        max_length=15, validators=[validate_min_length], default=""
    )
    charger_point_name = models.CharField(
        max_length=30, validators=[validate_min_length], default=""
    )
    charger_point_status = models.CharField(
        max_length=30, validators=[validate_min_length], default=""
    )
    back_office = models.CharField(
        max_length=30, validators=[validate_min_length], default=""
    )
    device_id = models.CharField(max_length=15, blank=True, null=True)
    payter_terminal_id = models.CharField(
        max_length=100, blank=True, null=True
    )
    worldline_terminal_id = models.CharField(
        max_length=100, blank=True, null=True
    )
    deleted = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    ev_charge_point_status = models.CharField(max_length=100, null=True, blank=True)
    manufacturer = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(
        max_length=100, validators=[validate_min_length], default=""
    ) 
    ampeco_charge_point_id = models.CharField(max_length=30, null=True, blank=True)
    ampeco_charge_point_name = models.CharField(max_length=100, null=True, blank=True) 

    class Meta:
        """meta data"""

        db_table = "charge_point"
        indexes = [
            models.Index(
                name="chargepointindexes",
                fields=["station_id"],
                condition=Q(charger_point_status="Active"),
            )
        ]

    def __str__(self):
        return str(self.charger_point_id)


class StationConnector(models.Model):
    """Station connectors models"""

    conditions = ((YES, YES), (NO, NO))
    station_connector_id = models.AutoField
    station_id = models.ForeignKey(
        Stations,
        null=True,
        on_delete=models.SET_NULL,
        related_name="station_connectors",
        related_query_name="station_connectors",
    )
    charge_point_id = models.ForeignKey(
        ChargePoint,
        null=True,
        on_delete=models.SET_NULL,
        related_name="connectors_list",
        related_query_name="connectors_list",
    )
    connector_id = models.CharField(
        max_length=15, validators=[validate_min_length], default=""
    )
    connector_name = models.CharField(
        max_length=30, validators=[validate_min_length], default=""
    )
    connector_type = models.CharField(
        max_length=30, validators=[validate_min_length], default=""
    )
    connector_sorting_order = models.CharField(
        max_length=30, validators=[validate_min_length], default=""
    )
    status = models.CharField(
        max_length=30, validators=[validate_min_length], default=""
    )
    current_status = models.CharField(
        max_length=30,
        validators=[validate_min_length],
        default="Not available",
    )
    plug_type_name = models.CharField(
        max_length=30, validators=[validate_min_length], default=""
    )
    max_charge_rate = models.CharField(
        max_length=30, validators=[validate_min_length], default=""
    )
    tariff_amount = models.FloatField(
        default=0, validators=[MaxValueValidator(999), MinValueValidator(0)]
    )
    tariff_ids = models.CharField(
        max_length=1000, null=True,blank=True
    )
    tariff_currency = models.CharField(
        max_length=30, validators=[validate_min_length], default=""
    )
    deleted = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(
        max_length=100, validators=[validate_min_length], default=""
    )
    back_office = models.CharField(
        max_length=100, blank=True, null=True
    )
    connector_evse_uid = models.CharField(max_length=36, null=True, blank = True)

    class Meta:
        """meta data"""

        db_table = "station_connector"
        indexes = [
            models.Index(
                name="stationconnectorindexes",
                fields=["station_id", "charge_point_id"],
                condition=Q(status="Active"),
            )
        ]

    def __str__(self):
        return str(self.station_id)

class ValetingTerminals(models.Model):
    """bokmarks model"""

    status = (
        ("Active", "Active"),
        ("Inactive", "Inactive"),
    )
    conditions=((YES,YES),(NO,NO))
    status = models.CharField(
        max_length=30, validators=[validate_min_length], default=""
    )
    valeting_terminals_id=models.AutoField
    payter_serial_number=models.CharField(
        max_length=100, blank=True, null=True
    )
    station_id = models.ForeignKey(
        Stations,
        null=True,
        on_delete=models.SET_NULL,
    )
    amenities=models.CharField(
        max_length=1000, blank=True, null=True
    )
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(
        max_length=100, validators=[validate_min_length],blank=True, null=True
    )
    deleted = models.CharField(
        max_length=100, choices=conditions, default=NO,
    )
    def __str__(self):
        return str(self.payter_serial_number)

class StationImages(models.Model):
    """Station images"""

    conditions_stations = ((YES, YES), (NO, NO))
    image_id = models.AutoField
    station_id = models.ForeignKey(
        Stations,
        null=True,
        on_delete=models.SET_NULL,
        related_name="image_url_list",
        related_query_name="image_url_list",
    )
    image = models.ImageField(upload_to="images")
    image_width = models.IntegerField(default=0)
    image_height = models.IntegerField(default=0)
    deleted = models.CharField(
        max_length=100,
        choices=conditions_stations,
        default=NO,
        blank=True,
        null=True,
    )
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(
        max_length=100, validators=[validate_min_length], default=""
    )

    class Meta:
        """meta data"""

        db_table = "station_images"
        indexes = [
            models.Index(
                name="stationimagesindexes",
                fields=["station_id"],
                condition=Q(deleted=False),
            )
        ]

    def __str__(self):
        return str(self.station_id)

    def get_image(self):
        """get station image"""
        return f"{config('DJANGO_APP_CDN_BASE_URL')}{self.image}"


class StationServices(models.Model):
    """Station services model"""

    days = (
        ("monday", "monday"),
        ("tuesday", "tuesday"),
        ("wednesday", "wednesday"),
        ("thursday", "thursday"),
        ("friday", "friday"),
        ("saturday", "saturday"),
        ("sunday", "sunday"),
    )
    conditions = ((YES, YES), (NO, NO))
    service_id = models.ForeignKey(
        ServiceConfiguration, null=True, on_delete=models.SET_NULL
    )
    station_id = models.ForeignKey(
        Stations,
        null=True,
        on_delete=models.SET_NULL,
        related_name="services_list",
        related_query_name="services_list",
    )
    service_name = models.CharField(
        max_length=30, validators=[validate_min_length], default=""
    )
    start_time = models.CharField(
        max_length=30, validators=[validate_min_length], default=""
    )
    end_time = models.CharField(
        max_length=30, validators=[validate_min_length], default=""
    )
    availability_days = models.CharField(
        max_length=100, blank=False, choices=days
    )
    deleted = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(
        max_length=100, validators=[validate_min_length], default=""
    )

    class Meta:
        """meta data"""

        db_table = "station_services"
        indexes = [
            models.Index(
                name="stationservicesindexes",
                fields=["station_id", "service_name", "service_id"],
                condition=Q(deleted=False),
            )
        ]

    def __str__(self):
        return str(self.service_name)


# This model is used to store bookmarked (v3 and below) and favourite (v4) stations
class Bookmarks(models.Model):
    """bokmarks model"""

    status = (
        ("bookmarked", "bookmarked"),
        ("bookmarked-removed", "bookmarked-removed"),
    )
    bookmark_id = models.AutoField
    user_id = models.ForeignKey(
        MFGUserEV, null=True, on_delete=models.SET_NULL
    )
    bookmarked_station_id = models.ForeignKey(
        Stations,
        null=True,
        on_delete=models.SET_NULL,
        related_name="user_bookmarks",
        related_query_name="user_bookmarks",
    )

    bookmark_status = models.CharField(
        max_length=100, blank=True, choices=status
    )
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return str(self.user_id)
