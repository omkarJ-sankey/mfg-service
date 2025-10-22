from django.db import models
from .app_user_models import MFGUserEV

class OCPITokens(models.Model):
    token_type = (
        ("AD_HOC_USER" , "AD_HOC_USER"),
        ("APP_USER" , "APP_USER"),
        ("RFID" , "RFID"),
        ("OTHER" , "OTHER")
        )

    whitelist_type = (
        ("ALWAYS" , "ALWAYS"),
        ("ALLOWED" , "ALLOWED"),
        ("ALLOWED_OFFLINE" , "ALLOWED_OFFLINE"),
        ("NEVER" , "NEVER")
    )
    id = models.AutoField(primary_key=True)
    uid = models.CharField(max_length=36)
    country_code = models.CharField(max_length=2)
    party_id = models.CharField(max_length=3)
    type = models.CharField(max_length=20, choices=token_type)
    contract_id = models.CharField(max_length=36)
    visual_number = models.CharField(max_length=64, blank=True, null=True)
    issuer = models.CharField(max_length=64)
    valid = models.BooleanField(default=True)
    whitelist = models.CharField(max_length=20, choices=whitelist_type)
    language = models.CharField(max_length=2, blank=True, null=True)  # ISO 639-1
    default_profile_type = models.CharField(max_length=20, blank=True, null=True)
    energy_contract = models.JSONField(null=True)
    last_updated = models.DateTimeField()
    group_id = models.CharField(max_length=36,null = True)
    user_id = models.ForeignKey(
        MFGUserEV,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='user'
    )
    back_offices = models.JSONField(null = True, blank = True)
    is_verified = models.BooleanField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['uid', 'type'], name='unique_uid_type')
        ]
