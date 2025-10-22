"""promotions api urls"""
# Date - 21/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on defining
#                       url path to access particular view or API.
#   Name            - Promotions Urls
#   Modified by     - Manish Pawar
#   Modified date   - 26/06/2021


# Imports required to make urls are below
from django.urls import path


# Views and APIs used for particular action and operation
from .apis import (
    PromotionDetailViewSet,
    PromotionsAPIViewset,
    PromotionFromStation,
    PromotionsFiltersAPIViewset,
)


# Assigning Views and APIs to particular url to access there functionality

urlpatterns = [
    path("api/promotions-deals/", PromotionsAPIViewset.as_view()),
    path("api/promotion-details/", PromotionDetailViewSet.as_view()),
    path("api/station-promotions/", PromotionFromStation.as_view()),
    path("api/promotions-filters/", PromotionsFiltersAPIViewset.as_view()),
]
