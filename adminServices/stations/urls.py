"""station urls"""
# Date - 21/06/2021

# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on defining
#                        url path to access particular view or API.
#   Name            - Stations Urls
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 09/05/2025


# Imports required to make urls are below
from django.urls import path

# Views and APIs used for particular action and operation
from .views import (
    AddStationAPIView,
    StationList,
    UploadSheetAPIView,
    ViewStation,
    station_list,
    add_station,
    view_station,
    delete_station,
    update_station,
    delete_station_image,
    map_ampeco_site_titles,
    validate_location
)
from .bulk_upload_views import progress_bar_info, upload_sheet

# Assigning Views and APIs to particular url to access there functionality
urlpatterns = [
    path("", station_list, name="station_list"),
    path("", StationList.as_view(), name="station_list"),
    # path("add-station/", add_station, name="station_add"),
    path("add-station/", AddStationAPIView.as_view(), name="station_add"),
    path("view-station/<str:station_pk>/", view_station, name="view_station"),
    path("view-station/<str:station_pk>/", ViewStation.as_view(), name="view_station"),
    path(
        "delete-station/<str:station_pk>/",
        ViewStation.as_view(),
        name="delete_station",
    ),
    path(
        "update-station/<str:station_pk>/",
        ViewStation.as_view(),
        name="update_station",
    ),
    # path("upload-sheet/", upload_sheet, name="uploadSheet"),
    path("upload-sheet/", UploadSheetAPIView.as_view(), name="uploadSheet"),
    path("progress-info/", progress_bar_info, name="progressBar"),
    path(
        "delete-station-image/<str:station_image_pk>/",
        delete_station_image,
        name="delete_station_image",
    ),
    path("map_ampeco_site_titles/", map_ampeco_site_titles, name="map_ampeco_site_titles"),
    path(
        "validate-location-mapping/",
        validate_location,
        name="validate_location",
    ),
]
