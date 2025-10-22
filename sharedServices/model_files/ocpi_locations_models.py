from django.db import models
from django.utils import timezone

from .station_models import (Stations,ChargePoint,StationConnector)

class OCPILocation(models.Model):
    parking_type = (
        ("ALONG_MOTORWAY", "ALONG_MOTORWAY"),
        ("PARKING_GARAGE", "PARKING_GARAGE"),
        ("PARKING_LOT", "PARKING_LOT"),
        ("ON_DRIVEWAY", "ON_DRIVEWAY"),
        ("ON_STREET", "ON_STREET"),
        ("UNDERGROUND_GARAGE", "UNDERGROUND_GARAGE"),
    )
    id = models.AutoField(primary_key=True)
    location_id = models.CharField(max_length=36)
    country_code = models.CharField(max_length=2)
    party_id = models.CharField(max_length=3)
    publish = models.BooleanField()
    publish_allowed_to = models.JSONField(null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=45)
    city = models.CharField(max_length=45)
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    state = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=3)
    coordinates = models.JSONField(max_length=50)
    related_locations = models.JSONField(null=True, blank=True)
    parking_type = models.CharField(max_length=255, choices=parking_type, null=True, blank=True)
    time_zone = models.CharField(max_length=255)
    opening_times = models.JSONField(null=True, blank=True)
    charging_when_closed = models.BooleanField(null=True, blank=True)
    directions = models.JSONField(null=True, blank=True)
    operator = models.JSONField(null=True, blank=True)
    suboperator = models.JSONField(null=True, blank=True)
    owner = models.JSONField(null=True, blank=True)
    facilities = models.CharField(max_length=1000,null=True, blank=True)
    images = models.JSONField(null=True, blank=True)
    energy_mix = models.JSONField(null=True, blank=True)
    last_updated = models.DateTimeField()
    station_mapping_id = models.ForeignKey(
        Stations,
        related_name='stations',
        on_delete=models.CASCADE,
        null=True
    )
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['country_code', 'party_id','location_id'], name='unique_location_id_party_id_country_code')
        ]
    def __str__(self):
        return f"{self.id}"
    
    def get_full_address(self):
        """get station address"""
        address = ""
        if (
            self.address
            and self.address != "nan"
            and self.address is not None
            and len(self.address) > 0
        ):
            address += str(self.address)

        if (
            self.city
            and self.city != "nan"
            and self.city is not None
            and len(self.city) > 0
        ):
            address += f", {self.city}"
        
        if (
            self.state
            and self.state != "nan" 
            and self.state is not None
            and len(self.state) > 0 
            ):
            if len(address) > 0:
                address += f", {self.state}"
            else:
                address += str(self.state)

        if (
            self.country 
            and self.country != "nan" 
            and self.country is not None
            and len(self.country) > 0 
            ):
            if len(address) > 0:
                address += f", {self.country}"
            else:
                address += str(self.country)
        
        if (
            self.postal_code
            and self.postal_code != "nan"
            and self.postal_code is not None
            and len(self.postal_code) > 0
        ):
            if len(address) > 0:
                address += f", {self.postal_code}"
            else:
                address += str(self.postal_code)
        return address



class OCPIEVSE(models.Model):
    location_id = models.ForeignKey(OCPILocation, on_delete=models.CASCADE, related_name='ocpi_locations')
    uid = models.CharField(max_length=36)
    id = models.AutoField(primary_key=True)
    evse_id = models.CharField(max_length=48, null= True,blank=True)
    status = models.CharField(max_length=50)
    status_schedule = models.JSONField(null=True, blank=True)
    capabilities = models.JSONField(null=True, blank=True)
    floor_level = models.CharField(max_length=4, null=True, blank=True)
    coordinates = models.CharField(max_length=255, null=True, blank=True)
    physical_reference = models.CharField(max_length=16, null=True, blank=True)
    directions = models.JSONField(null=True, blank=True)
    parking_restrictions = models.JSONField(null=True, blank=True)
    images = models.JSONField(null=True, blank=True)
    last_updated = models.DateTimeField()
    chargepoint_mapping_id = models.ForeignKey(
        ChargePoint,
        related_name='chargepoints',
        on_delete=models.CASCADE,
        null=True
    )
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['location_id', 'uid'], name='unique_location_id_uid')
        ]
    def __str__(self):
        return f"{self.id}"


class OCPIConnector(models.Model):
    evse_id = models.ForeignKey(OCPIEVSE, on_delete=models.CASCADE, related_name='ocpi_evses')
    id = models.AutoField(primary_key=True)
    connector_id = models.CharField(max_length=36)
    standard = models.CharField(max_length=50)
    format = models.CharField(max_length=50)
    power_type = models.CharField(max_length=50)
    max_voltage = models.IntegerField()
    max_amperage = models.IntegerField()
    max_electric_power = models.IntegerField(null=True, blank=True)
    tariff_ids = models.JSONField(null=True, blank=True)
    terms_conditions = models.URLField(max_length=255, null=True, blank=True)
    last_updated = models.DateTimeField()
    connector_mapping_id = models.ForeignKey(
        StationConnector,
        related_name='station_connectors',
        related_query_name = 'station_connectors',
        on_delete=models.CASCADE,
        null=True
    )
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['evse_id', 'connector_id'], name='unique_evse_id_connector_id')
        ]
    def __str__(self):
        return f"{self.id}"