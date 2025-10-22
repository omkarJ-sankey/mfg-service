"""App users urls"""
# Date - 22/05/2024
# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on defining url path
#                       to access particular view.
#   Name            - App users Urls
#   Modified by     - Manish Pawar
#   Modified date   - 22/05/2024
# Imports required to make urls are below
from django.urls import path
from .views import block_app_users

# Assigning Views to particular url to access there functionality
urlpatterns = [
    path("block-app-users/", block_app_users, name="block_app_users"),
]
