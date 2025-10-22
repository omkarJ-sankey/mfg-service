"""Electric vehicles api urls"""
# Date - 16/11/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on defining url path
#                        to access particular view or API.
#   Name            - Electric vehicle Urls
#   Modified by     - Manish Pawar
#   Modified date   - 26/06/2021


# Imports required to make urls are below
from django.urls import path


# Views and APIs used for particular action and operation
from .apis import (
    AddUserEVAPI,
    EVFiltersAPI,
    ElectricVehiclesData,
    ElectricVehiclesDetailsAPI,
    RemoveUserEVAPI,
    RequestElectricVehicleDatabaseAPI,
    UserEVListAPI,
    MakeEVDefaultAPI,
    ElectricVehiclesDetailsWithNumberPlateAPI,
)


# Assigning Views and APIs to particular url to access there functionality

urlpatterns = [
    path(
        "api/electric-vehicle-cron-job/",
        RequestElectricVehicleDatabaseAPI.as_view(),
    ),
    path("api/electric-vehicles-data/", ElectricVehiclesData.as_view()),
    path(
        "api/electric-vehicles-details/", ElectricVehiclesDetailsAPI.as_view()
    ),
    path(
        "api/get-electric-vehicles-details-by-number-plate/",
        ElectricVehiclesDetailsWithNumberPlateAPI.as_view(),
    ),
    path("api/add-user-ev/", AddUserEVAPI.as_view()),
    path("api/remove-user-ev/", RemoveUserEVAPI.as_view()),
    path("api/user-ev-list/", UserEVListAPI.as_view()),
    path("api/make-ev-default/", MakeEVDefaultAPI.as_view()),
    path("api/ev-filters/", EVFiltersAPI.as_view()),
]
