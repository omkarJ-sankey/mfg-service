"""stations APIs urls"""
# Date - 21/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on defining
#                       url path to access particular view or API.
#   Name            - Stations Urls
#   Modified by     - Manish Pawar
#   Modified date   - 21/06/2021


# Imports required to make urls are below
from rest_framework import routers
from django.urls import path, include

# Views and APIs used for particular action and operation
from .apis import (
    BookmarkStationAPI,
    IconsAPI,
    ReviewPostAPI,
    StationDetailsAPI,
    StationFinderRadiusViewSet,
    StationFinderViewSet,
    FilterDataList,
    NearestStation,
    Bookmark
)

from backendServices.stations.v4_apis import (
    StationFinderViewSetV4,
    FilterDataListV4,
    SaveUserStationFinderSelectedFilterOptions,
    GetRecentlyUsedChargingStations,
    GetDynamicTariff,
    SyncLocationCron,
    UpdateStationsCache
)


router = routers.DefaultRouter()

# Assigning Views and APIs to particular url to access there functionality
router.register(
    "station-finder-data-radius",
    StationFinderRadiusViewSet,
    "station_list-by-radius",
)

v3_urlpatterns = [
    path("api/post-review/", ReviewPostAPI.as_view()),
    path("api/filter-list/", FilterDataList.as_view()),
    path("api/bookmark-station/", BookmarkStationAPI.as_view()),
    path("api/icons/", IconsAPI.as_view()),
    path("api/station-finder-data/", StationFinderViewSet.as_view()),
    path("api/nearest-station/", NearestStation.as_view()),
    path("api/bookmark/", Bookmark.as_view()),
    path("api/station-details-data/", StationDetailsAPI.as_view()),
    path("api/", include((router.urls, "stations"), namespace="stations")),
]


v4_urlpatterns = [
    path("api/v4/station-finder-data/", StationFinderViewSetV4.as_view()),
    path("api/v4/filter-list/", FilterDataListV4.as_view()),
    path(
        "api/v4/save-or-get-station-finder-selected-filters/",
        SaveUserStationFinderSelectedFilterOptions.as_view()
    ),
    path("api/v4/add-or-remove-favourite-station/", BookmarkStationAPI.as_view()),
    path("api/v4/get-favourite-stations/", Bookmark.as_view()),
    path(
        "api/v4/get-recently-used-charging-stations/",
        GetRecentlyUsedChargingStations.as_view()
    ),
    # path(
    #     "api/v4/get-dynamic-tariff/",
    #     GetDynamicTariff.as_view()
    # ),
     path(
        "api/v4/sync-locations-cron/",
        SyncLocationCron.as_view()
    ),
    path(
        "api/v4/update-stations-cache/",
        UpdateStationsCache.as_view()
    )
]

urlpatterns = v3_urlpatterns + v4_urlpatterns + router.urls
