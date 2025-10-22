"""Housekeeping urls"""
# File details-
#   Author      - Vismay Raul
#   Description - This file is declare urlpatterns of housekeeping
#   Name        - Housekeeping urls
#   Modified by - Vismay Raul

from django.urls import path

# pylint: disable-msg=E0611
from .apis import (
    UploadBackupFileToBlob,
    DeleteUnusedRowsFromDb
)

urlpatterns = [
    path(
        "api/backup-file-to-blob/",
        UploadBackupFileToBlob.as_view(),
    ),
    path(
        "api/delete-unused-rows-from-db/",
        DeleteUnusedRowsFromDb.as_view(),
    ),
]