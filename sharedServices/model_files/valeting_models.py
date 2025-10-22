from django.db import models
from sharedServices.model_files.station_models import Stations

class ValetingMachine(models.Model):
    """Valeting machine model"""
    
    machine_id = models.BigIntegerField(unique=True)
    station_id = models.ForeignKey(
        Stations,
        null=True,
        on_delete=models.SET_NULL,
    )
    machine_name = models.CharField(
        max_length=255, blank=True, null=True
    )
    machine_number = models.CharField(
        max_length=255, blank=True, null=True
    )
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(
        max_length=100, blank=True, null=True
    )
    deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "valeting_machine"

    def __str__(self):
        return str(self.machine_id)