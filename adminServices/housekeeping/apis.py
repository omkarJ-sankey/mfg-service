"""housekeeping module APIs"""
#  File details-
#   Author      - Vismay Raul
#   Description - This file contains APIs for Housekeeping module.
#   Name        - Housekeeping module APIs
#   Modified by - Vismay Raul

# These are all the imports that we are exporting from
# different module's from project or library.

from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from sharedServices.constants import (
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    SECRET_KEY_IN_VALID,
    SECRET_KEY_NOT_PROVIDED,
    DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET,
)
from passlib.hash import django_pbkdf2_sha256 as handler
from sharedServices.housekeeping.create_backup import dump_backup_file_to_blob_storage
from sharedServices.housekeeping.delete_functionality import delete_unused_data

class UploadBackupFileToBlob(APIView):
    """Dumps backup file from local system to the blob storage"""

    def post(self, path):
        """Dumps backup file from local system to the blob storage"""
        try:
            secret_key_azure = path.data.get("secret_key", None)
            if secret_key_azure is None:
                return SECRET_KEY_NOT_PROVIDED
            if not handler.verify(
                secret_key_azure, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
            ):
                return SECRET_KEY_IN_VALID
            
            path = str(path.query_params.get("path", None))
            if path is not None:
                stored_in_blob = dump_backup_file_to_blob_storage(path)
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": stored_in_blob,
                    }
                )
            return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Path not provided",
                    }
                )

        except COMMON_ERRORS:
            return API_ERROR_OBJECT
        

class DeleteUnusedRowsFromDb(APIView):
    """This api is used to delete the unwanted rows from the mentioned table"""

    def post(self, table_name_list):
        """delete the unwanted rows from the mentioned table"""
        try:
            secret_key_azure = table_name_list.data.get("secret_key", None)
            if secret_key_azure is None:
                return SECRET_KEY_NOT_PROVIDED
            if not handler.verify(
                secret_key_azure, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
            ):
                return SECRET_KEY_IN_VALID
            
            table_name_list = str(table_name_list.data.get("table_names", None))
            deleted_unused_data = delete_unused_data(table_name_list)
            return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": deleted_unused_data,
                    }
                )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT