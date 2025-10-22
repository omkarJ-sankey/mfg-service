"""review urls"""
# File details-
#   Author      - Shubham Dhumal
#   Description - This file is declatre urlpatterns of reviews
#   Name        - User Management urls
#   Modified by - Shubham Dhumal
from django.urls import path
from .views import reviews, approve, disapprove

urlpatterns = [
    path("", reviews, name="reviews"),
    path("updatestatus/", approve, name="updatestatus"),
    path("decline/", disapprove, name="decline"),
]
