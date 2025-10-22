"""trip planner urls"""
# Date - 21/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on defining url path
#                       to access particular view or API.
#   Name            - Trip planner Urls
#   Modified by     - Manish Pawar
#   Modified date   - 21/06/2021


# Imports required to make urls are below
from rest_framework import routers
from django.urls import path

# Views and APIs used for particular action and operation
from .apis import (
    AddTrip,
    AddTripToFavouritesAPI,
    DeleteTrip,
    FavouriteTripsViewset,
    FilterListForTripPlanner,
    GetTripData,
    PlannedTripsViewset,
    TripPlannerStations,
)


router = routers.DefaultRouter()
# Assigning Views and APIs to particular url to access there functionality
urlpatterns = [
    path("api/add-trip/", AddTrip.as_view()),
    path("api/delete-trip/", DeleteTrip.as_view()),
    path("api/fetch-saved-trip/", GetTripData.as_view()),
    path("api/planned-trips/", PlannedTripsViewset.as_view()),
    path("api/favourite-trips/", FavouriteTripsViewset.as_view()),
    path("api/filters/", FilterListForTripPlanner.as_view()),
    path("api/add-trip-to-favourite/", AddTripToFavouritesAPI.as_view()),
    path("api/stations/", TripPlannerStations.as_view()),
]

urlpatterns = urlpatterns + router.urls
