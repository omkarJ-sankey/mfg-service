"""custom auth function"""
from django.contrib.auth.backends import ModelBackend

from .model_files.app_user_models import MFGUserEV


class CustomerBackend(ModelBackend):
    """customer uth class"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """custom auth function"""
        email = kwargs["email"]
        try:
            customer = MFGUserEV.objects.get(user_email=email)
            if customer:
                return customer
        except Exception as snip_no_exist:
            raise TypeError("No matching query found") from snip_no_exist
        return None
