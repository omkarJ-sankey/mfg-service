"""admin services urls
"""
from django.urls import path, include
from django.views.generic import RedirectView

from django.conf import settings
from django.conf.urls.static import static
from rest_framework_swagger.views import get_swagger_view
from sharedServices.common import robots_txt

schema_view = get_swagger_view(title="MFG EV connect API documentation")

urlpatterns = [
    path("robots.txt", robots_txt, name="robots_txt"),
    path('', RedirectView.as_view(url='administrator/authenticate/', permanent=True)),
    path("administrator/dashboard/", include("adminServices.dashboard.urls")),
    path("administrator", include("adminServices.dashboard.urls")),
    path("api_documentation/", schema_view),
    path("administrator/promotions/", include("adminServices.promotions.urls")),
    path("administrator/authenticate/", include("adminServices.auths.urls")),
    path("administrator/stations/", include("adminServices.stations.urls")),
    path("administrator/usermanagement/", include("adminServices.user_management.urls")),
    path("administrator/wallet/", include("adminServices.e_wallet.urls")),
    path("administrator/configurations/", include("adminServices.configurations.urls")),
    path("administrator/reviews/", include("adminServices.reviews.urls")),
    path("administrator/reconciliation/", include("adminServices.reconciliation.urls")),
    path(
        "administrator/session-transactions/",
        include("adminServices.session_transactions.urls"),
    ),
    path("administrator/offers/", include("adminServices.loyalty.urls")),
    path("contactless/", include("adminServices.contactless.urls")),
    path("administrator/contactless/", include("adminServices.contactless.administrator_urls")),
    path("administrator/housekeeping/", include("adminServices.housekeeping.urls")),
    path("administrator/audit-trail/", include("adminServices.audit_trail.urls")),
    path("administrator/notifications/", include("adminServices.notifications.urls")),
    path("notifications/", include("adminServices.notification_cronjobs.urls")),
    path("administrator/app-users/", include("adminServices.app_users.urls")),
    path("administrator/three-ds-config/", include("adminServices.three_ds_config.urls")),
    path("ckeditor5/", include('django_ckeditor_5.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
