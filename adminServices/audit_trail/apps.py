"""audit trail app"""
from django.apps import AppConfig


class AuditTrailConfig(AppConfig):
    """audit trail app"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "adminServices.audit_trail"
