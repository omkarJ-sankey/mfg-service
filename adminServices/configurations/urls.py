"""configurations urls"""
# File details-
#   Author      - Manish Pawar
#   Description - This file is declare urlpatterns of configurations
#   Name        - configurations urls
#   Modified by - Abhinav Shivalkar

from django.urls import path
from .views import (
    connectors,
    aminities,
    shops,
    delete_connector,
    delete_amenity,
    delete_shop,
    update_connector,
    update_amenity,
    update_shop,
    check_service_id_availability,
    check_connector_sorting_order_availability,
    email_notifications,
    unsubscribe_user_from_emails
)
from .base_configurations_views import (
    map_markers_view,
    base_configurations_view,
    default_images_view,
    update_default_images_view,
    update_base_configuration_view,
    update_marker_view
)
from .ocpi_configurations_views import (
    ocpi_configurations_view,
    update_ocpi_configuration_details
)
urlpatterns = [
    path("connectors/", connectors, name="connectors"),
    path("connectors/update/", update_connector, name="update_connector"),
    path(
        "delete-connector/<int:connector_id>/",
        delete_connector,
        name="deleteConnector",
    ),
    # Amenities Routes
    path("amenities/", aminities, name="amenities"),
    path("aminities/update/", update_amenity, name="update_amenity"),
    path(
        "delete-amenities/<int:amenity_id>/",
        delete_amenity,
        name="deleteAmenities",
    ),
    # Shops Routes
    path("shops/", shops, name="shops"),
    path("shops/?type=all", shops, name="shops"),
    path("shops/update/", update_shop, name="update_shop"),
    path("delete-shops/<int:shop_id>/", delete_shop, name="deleteShops"),
    # add markers
    path("add-markers/", map_markers_view, name="addMarkers"),
    path(
        "update-markers/",
        update_marker_view,
        name="updateMarkers",
    ),

    path(
        "ocpi-configurations/",
        ocpi_configurations_view,
        name="addOCPIConfigurations",
    ),
    path(
        "update-ocpi-configurations/<str:credentials_id>/",
        update_ocpi_configuration_details,
        name="updateOCPIConfigurations",
        ),
    # add baseconfigurations
    path(
        "add-base-configurations/",
        base_configurations_view,
        name="addBaseConfigurations",
    ),
    path(
        "update-base-configurations/",
        update_base_configuration_view,
        name="updateBaseConfigurations",
    ),
    # add and list default images
    path(
        "add-default-images/",
        default_images_view,
        name="addDefaultImages",
    ),
    path(
        "update-default-images/",
        update_default_images_view,
        name="updateDefaultImages",
    ),
    path(
        "check-service-id-availability/",
        check_service_id_availability,
        name="check_service_id_availability",
    ),
    path(
        "check-connector-sorting-order-availability/",
        check_connector_sorting_order_availability,
        name="check_connector-sorting-order_availability",
    ),
    path(
        "email-notifications/",
        email_notifications,
        name="email_notifications",
    ),
    path(
        "unsubscribe-user-from-emails/<str:user_email>/",
        unsubscribe_user_from_emails,
        name="unsubscribe_user_from_emails",
    ),
]
