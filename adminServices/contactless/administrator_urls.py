"""dashboard urls"""
# File details-
#   Author      - Shivkumar kumbhar
#   Description - This file is declare urlpatterns of dashboard
#   Name        - Dashboard urls
#   Modified by - Shivkumar kumbhar

from django.urls import path

# pylint: disable-msg=E0611
from .apis import (
    get_thirdparty_data,
)

urlpatterns = [
    path(
        "get-thirdparty-data/",
        get_thirdparty_data,
        name="get_thirdparty_data",
    ),
]
