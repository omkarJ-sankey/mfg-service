from django.db import models
from django.utils import timezone
from .ocpi_sessions_models import OCPISessions
from .ocpi_tokens_models import OCPITokens
from .ocpi_locations_models import OCPIConnector,OCPILocation,OCPIEVSE


class OCPICommands(models.Model):
    COMMAND_CHOICES = [
        ("UNLOCK_CONNECTOR", "UNLOCK_CONNECTOR"),
        ("RESERVE_NOW", "RESERVE_NOW"),
        ("START_SESSION", "START_SESSION"),
        ("STOP_SESSION", "STOP_SESSION"),
        ("CANCEL_RESERVATION", "CANCEL_RESERVATION"),
    ]

    id = models.AutoField(primary_key=True)
    command = models.CharField(max_length=50, choices=COMMAND_CHOICES)
    # session = models.ForeignKey(
    #     Session,
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    # )
    # reservation_id = models.CharField(max_length=36, null=True,blank=True)#will be used in reservations
    # location_id = models.ForeignKey(
    #     Location,
    #     on_delete=models.SET_NULL,
    #     null=True,
    # )
    # evse_id = models.ForeignKey(
    #     EVSE,
    #     on_delete=models.SET_NULL,
    #     null=True,
    # )
    # token = models.ForeignKey(
    #     OCPITokens,
    #     on_delete=models.SET_NULL,
    #     null=True
    # )
    # connector = models.ForeignKey(
    #     Connector,
    #     on_delete=models.SET_NULL,
    #     null=True,
    # )
    # authorization_reference = models.CharField(max_length=36, null=True,blank=True)
    # response_url = models.URLField()
    request_payload = models.JSONField(null=True,blank=True)
    response_payload = models.JSONField(null=True,blank=True)
    command_exec_payload = models.JSONField(null=True,blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    session_id = models.ForeignKey(
        OCPISessions,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.command} - {self.id}"

# class CommandResponse(models.Model):
#     RESULT_CHOICES = [
#         ("ACCEPTED", "ACCEPTED"),
#         ("CANCELED_RESERVATION", "CANCELED_RESERVATION"),
#         ("EVSE_OCCUPIED", "EVSE_OCCUPIED"),
#         ("EVSE_INOPERATIVE", "EVSE_INOPERATIVE"),
#         ("FAILED", "FAILED"),
#         ("NOT_SUPPORTED", "NOT_SUPPORTED"),
#         ("REJECTED", "REJECTED"),
#         ("TIMEOUT", "TIMEOUT"),
#         ("UNKNOWN_RESERVATION", "UNKNOWN_RESERVATION"),
#     ]

#     id = models.AutoField(primary_key=True)
#     command_request = models.ForeignKey(
#         CommandRequest,
#         on_delete=models.CASCADE,
#         related_name="response"
#     )
#     result = models.CharField(max_length=20, choices=RESULT_CHOICES)
#     message = models.JSONField(null=True, blank=True)
#     response_payload = models.JSONField( null=True, blank=True)
#     timestamp = models.DateTimeField(default=timezone.now)
