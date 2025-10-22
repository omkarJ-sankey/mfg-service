"""ev_chargingapp_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from sharedServices.common import robots_txt


schema_view = get_schema_view(
    openapi.Info(
        title="MFG EV APP Backend APIs",
        default_version='v4',
        description="API documentation for MFG EV APP backend",
        contact=openapi.Contact(email="Nitesh.k1@sankeysolutions.com"),
    ),
    public=False,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path("robots.txt", robots_txt, name="robots_txt"),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path("promotions/", include("backendServices.promotions.urls")),
    path("", include("backendServices.auths.urls")),
    path("stations/", include("backendServices.stations.urls")),
    path("trip-planner/", include("backendServices.trip_planner.urls")),
    path(
        "charging-sessions/", include("backendServices.charging_sessions.urls")
    ),
    path("history/", include("backendServices.history.urls")),
    path("payment/", include("backendServices.payment.urls")),
    path(
        "electric-vehicles/", include("backendServices.electric_vehicles.urls")
    ),
    path("loyalty/", include("backendServices.loyalty.urls")),
    path("contactless/", include("backendServices.contactless.urls")),
    path("notifications/", include("backendServices.notifications.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns = urlpatterns + static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)
