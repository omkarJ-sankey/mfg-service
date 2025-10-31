"""Audit trail urls"""
# Date - 14/07/2022
# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on defining url path
#                       to access particular view.
#   Name            - Audit trail Urls
#   Modified by     - Manish Pawar
#   Modified date   - 14/07/2022
# Imports required to make urls are below
from django.urls import path
from .views import AuditTrailDetailView, AuditTrailListView, MarkedAsReviewedView, audit_list_view, audit_detail_view, mark_as_reviewed

# Assigning Views to particular url to access there functionality
urlpatterns = [
    # path("", audit_list_view, name="audit_list"),
    path("get-audit-list/",AuditTrailListView.as_view(),name="get_audit_list"),
    # path(
    #     "audit-detail/<int:detail_row_id>/",
    #     audit_detail_view,
    #     name="audit_detail",
    # ),
    path("get-audit-details/",AuditTrailDetailView.as_view(),name="get_audit_details"),
    # path("mark-as-reviewed/", mark_as_reviewed, name="mark_as_reviewed"),
    path("mark-as-reviewed/",MarkedAsReviewedView.as_view(),name="mark_as_reviewed")
]
