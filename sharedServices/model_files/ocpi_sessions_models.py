from django.db import models
from .ocpi_locations_models import OCPILocation,OCPIEVSE,OCPIConnector
from django.core.validators import MaxValueValidator, MinValueValidator
from ..constants import YES, NO
from .station_models import Stations, ChargePoint, StationConnector
from .app_user_models import MFGUserEV
from .admin_user_models import AdminUser


# class CdrToken(models.Model):
#     token_type = (
#         ("AD_HOC_USER" , "AD_HOC_USER"),
#         ("APP_USER" , "APP_USER"),
#         ("RFID" , "RFID"),
#         ("OTHER" , "OTHER")
#         )
#     country_code = models.CharField(max_length=2)
#     party_id = models.CharField(max_length=3)
#     id = models.AutoField(primary_key=True)
#     uid = models.CharField(max_length=36)
#     contract_id = models.ForeignKey(
#         OCPITokens,
#         on_delete=models.CASCADE
#     )
#     type=models.CharField(max_length=20,choices=token_type)


class OCPISessions(models.Model):
    pay_status = (
        ("paid", "paid"),
        ("unpaid", "unpaid"),
        ("refunded", "refunded"),
    )
    mail_sent_status = (
        ("pending", "pending"),
        ("sent", "sent"),
    )
    conditions = ((YES, YES), (NO, NO))
    payment_source_conditions = (("Admin", "Admin"), ("App", "App"))
    payment_types = (
        ("Combined", "Combined"),
        ("Partial", "Partial"),
        ("non wallet", "non wallet"),
    )
    auth_method = (
        ("AUTH_REQUEST","AUTH_REQUEST"),
        ("COMMAND","COMMAND"),
        ("WHITELIST","WHITELIST"),
    )
    
    status_types = (
        ("ACTIVE","ACTIVE"),
        ("COMPLETED","COMPLETED"),
        ("INVALID","INVALID"),
        ("PENDING","PENDING"),
        ("RESERVATION","RESERVATION"),
        ("AWAITING","AWAITING"),#session status maintained in ev-connect, not present in ocpi
    )
    status_choices = (
        ("start","start"),
        ("running","running"),
        ("rejected","rejected"),
        ("stopped","stopped"),
        ("closed","closed"),
        ("completed","completed"),
    )
    
    id = models.AutoField(primary_key=True)
    session_id = models.CharField(max_length=36,blank=True, null=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)
    kwh = models.DecimalField(max_digits=10, decimal_places=4,blank=True, null=True)
    auth_method = models.CharField(max_length=20,choices=auth_method,blank=True, null=True)
    authorization_reference = models.CharField(max_length=36,null=True,blank=True)
    cdr_token = models.TextField(blank=True, null=True)
    location_id = models.ForeignKey(
        OCPILocation,
        on_delete=models.CASCADE,
        related_name="location"
    )
    # evse_uid = models.CharField(max_length=39)  
    evse_id = models.ForeignKey(
        OCPIEVSE,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )                                
    # connector_id = models.CharField(max_length=36)  
    connector_id = models.ForeignKey(
        OCPIConnector,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    meter_id = models.CharField(max_length=255, null=True, blank=True)
    currency = models.CharField(max_length=3,blank=True, null=True)
    # total_cost = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    total_cost_incl = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    total_cost_excl = models.DecimalField(max_digits=12, decimal_places=4,blank=True, null=True)
    status = models.CharField(max_length=20,choices=status_types,blank=True, null=True)
    charging_periods = models.JSONField(blank=True, null=True)
    user_id = models.ForeignKey(
        MFGUserEV,
        null=True,
        on_delete=models.SET_NULL,
        related_name="ocpi_user_charging_sessions",
        related_query_name="ocpi_user_charging_sessions",
    )
    user_account_number = models.CharField(
        max_length=500, null=True, blank=True
    )
    # models.IntegerField(null=True, blank=True)
    user_card_number = models.CharField(
        max_length=500, null=True, blank=True
    )
    emp_session_id = models.CharField(
        max_length=500, unique=True, null=True, blank=True
    )
    charging_session_id = models.CharField(
        max_length=500, unique=True, null=True, blank=True
    )
    charging_authorization_status = models.CharField(
        max_length=500, null=True, blank=True
    )
    session_status = models.CharField(
        max_length=100, blank=True, choices=status_choices
    )
    payment_id = models.CharField(max_length=1000, unique=False, null=True)
    paid_status = models.CharField(
        max_length=100, blank=True, default="unpaid", choices=pay_status
    )
    payment_method = models.CharField(max_length=100, unique=False, null=True)
    payment_response = models.TextField(null=True, blank=True)
    charging_data = models.TextField(null=True, blank=True)
    user_mail = models.BinaryField(blank=True, null=True)
    mail_status = models.CharField(
        max_length=100, blank=True, default="pending", choices=mail_sent_status
    )
    feedback = models.CharField(max_length=500, null=True, blank=True)
    rating = models.IntegerField(
        default=0, validators=[MaxValueValidator(5), MinValueValidator(1)]
    )
    back_office = models.CharField(max_length=30, null=True, blank=True)
    is_reviewed = models.CharField(
        max_length=100,
        choices=payment_source_conditions,
        default="App",
        blank=True,
        null=True,
    )
    is_force_stopped = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    is_refund_initiated = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    end_time = models.DateTimeField(null=True, blank=True)
    payment_completed_at = models.DateTimeField(null=True, blank=True)
    preauth_status = models.CharField(max_length=100, unique=False, null=True)
    preauth_collected_by = models.CharField(
        max_length=100, unique=False, null=True
    )
    session_tariff = models.CharField(max_length=30, blank=True, null=True)
    payment_type = models.CharField(max_length=100, unique=False, null=True)
    deducted_voucher_amount = models.CharField(
        max_length=20, null=True, blank=True
    )
    country_code = models.CharField(max_length=2)
    party_id = models.CharField(max_length=3)
    last_updated = models.DateTimeField(auto_now=True)
    station_id = models.ForeignKey(
        Stations,
        null=True,
        on_delete=models.SET_NULL,
        related_name="ocpi_station_charging_sessions",
        related_query_name="ocpi_station_charging_sessions",
    )
    chargepoint_id = models.ForeignKey(
        ChargePoint,
        null=True,
        on_delete=models.SET_NULL,
        related_name="ocpi_charging_sessions_chargepoints",
        related_query_name="ocpi_charging_sessions_chargepoints",
    )
    station_connector_id = models.ForeignKey(
        StationConnector,
        null=True,
        on_delete=models.SET_NULL,
        related_name="ocpi_charging_sessions_connectors",
        related_query_name="ocpi_charging_sessions_connectors",
    )
    vat_percentage = models.DecimalField(max_digits=12, decimal_places=4, blank=False, null=False, default=20)
    is_cdr_valid = models.BooleanField(null=True)
    cdr_id = models.CharField(
        max_length=100, blank=True, null=True
    )
    class Meta:
        db_table = 'sharedServices_ocpisessions'
        # constraints = [
        #     models.UniqueConstraint(fields=['location_id', 'session_id'], name='unique_location_id_session_id')
        # ]
        indexes = [
            models.Index(
                name="ocpisessionidindexes", fields=["emp_session_id"]
            ),
            models.Index(
                name="ocpiosessionendtimeindexes", fields=["end_time"]
            ),
        ]
    def __str__(self):
        return str(self.id)

# class ChargingPeriod(models.Model):
#     dimension_types = (
#         ("CURRENT", "CURRENT"),
#         ("ENERGY", "ENERGY"),
#         ("ENERGY_EXPORT", "ENERGY_EXPORT"),
#         ("ENERGY_IMPORT", "ENERGY_IMPORT"),
#         ("MAX_CURRENT", "MAX_CURRENT"),
#         ("MIN_CURRENT", "MIN_CURRENT"),
#         ("MAX_POWER", "MAX_POWER"),
#         ("MIN_POWER", "MIN_POWER"),
#         ("PARKING_TIME", "PARKING_TIME"),
#         ("POWER", "POWER"),
#         ("RESERVATION_TIME", "RESERVATION_TIME"),
#         ("STATE_OF_CHARGE", "STATE_OF_CHARGE"),
#         ("TIME", "TIME"),
#     )
#     session_id = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="session")
#     start_datetime = models.DateTimeField()                                     
#     end_datetime = models.DateTimeField(null=True, blank=True)                  
#     dimension = models.CharField(max_length=20)                                 
#     # tariff_id = models.CharField(max_length=36, null=True, blank=True)          
#     tariff_id = models.ForeignKey(
#         Tariffs,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True
#     )
#     cdr_dimension_type = models.CharField(max_length=20,choices=dimension_types)
#     volume = models.DecimalField(max_digits=10, decimal_places=4)
#     energy = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)