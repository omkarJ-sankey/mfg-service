"""Housekeeping upload backup to blob function"""

from datetime import datetime
from azure.storage.blob import BlobServiceClient
from decouple import config


def dump_backup_file_to_blob_storage(dump_file_path):
    """function to add dummy sql file to blob storage"""
    # Azure Blob Storage parameters
    azure_connection_string = config('DJANGO_APP_CONNECTION_STRING')
    container_name = 'backup'
    blob_name = f'backup-mfg-connect-{datetime.now()}.bacpac'

    # Upload the dump file to Azure Blob Storage
    blob_service_client = BlobServiceClient.from_connection_string(azure_connection_string)
    blob_client = blob_service_client.get_blob_client(container_name, blob_name)

    with open(dump_file_path, "rb") as data:
        blob_client.upload_blob(data)

    return 'Database dump saved to Azure Blob Storage.'
