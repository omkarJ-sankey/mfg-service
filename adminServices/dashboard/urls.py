"""dashboard urls"""
# File details-
#   Author      - Shubham Dhumal
#   Description - This file is declatre urlpatterns of dashboard
#   Name        - Dashboard urls
#   Modified by - Shubham Dhumal

from django.urls import path
from .views import form_dashboard

urlpatterns = [
    path("", form_dashboard, name="dashboard"),
]
