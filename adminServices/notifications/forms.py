# Date - 20/11/2022
# File details-
#   Author          - Shivkumar kumbhar
#   Description     - This file is mainly focused on
#                      creating form for custom email body
#   Name            - notifications module related models
#   Modified by     - Shivkumar kumbhar
#   Modified date   - 26/12/2022
from django.forms import ModelForm
from sharedServices.model_files.notifications_module_models import (
    EmailNotifications,
)


class EmailDescription(ModelForm):
    """This class mainly deals with custom email body (description using ck editor)"""

    class Meta:
        model = EmailNotifications
        fields = ["description"]
