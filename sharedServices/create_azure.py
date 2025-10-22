"""azure blob configurations"""
from storages.backends.azure_storage import AzureStorage
from decouple import config
import requests
from msal import ConfidentialClientApplication
from .sentry_tracers import traced_request
from .constants import (
    REQUEST_API_TIMEOUT,
    CDN_SUCCESS_MESSAGE,
    CDN_FAIL_MESSAGE_STRING,
    CDN_ERROR_MESSAGE_STRING,
    POST_REQUEST,
)

class AzureMediaStorage(AzureStorage):
    """media storage configurations"""

    account_name = config("DJANGO_APP_AZURE_APP_NAME")
    account_key = config("DJANGO_APP_AZURE_APP_KEY")
    azure_container = "media"
    expiration_secs = None
    cache_control = "public, max-age=31622400"
    # get created time override

    def get_created_time(self, name):
        pass

    # get accessed time override
    def get_accessed_time(self, name):
        pass

    # get path override
    def path(self, name):
        pass


class AzureStaticStorage(AzureStorage):
    """static storage configurations"""

    account_name = config("DJANGO_APP_AZURE_APP_NAME")
    account_key = config("DJANGO_APP_AZURE_APP_KEY")
    azure_container = "static"
    expiration_secs = None
    cache_control = "public, max-age=31622400"
    # get created time override

    def get_created_time(self, name):
        pass

    # get accessed time override
    def get_accessed_time(self, name):
        pass

    # get path override
    def path(self, name):
        pass


def purge_cdn_cache():
    """purge function for removing data from the cdn that is to be updated"""

    confidential_client_application = ConfidentialClientApplication(
        client_id=config("DJANGO_APP_API_AD_CLIENT_ID"),
        client_credential=config("DJANGO_APP_API_AD_CLIENT_SECRET"),
        authority=config("DJANGO_APP_API_AD_AUTHORITY_URL")
    )
    cdn_access_key= confidential_client_application.acquire_token_silent(scopes=[config("DJANGO_APP_API_AD_SCOPE")], account=None)
    if not cdn_access_key:
        cdn_access_key = confidential_client_application.acquire_token_for_client(scopes=[config("DJANGO_APP_API_AD_SCOPE")])
    
    # Specify the content to be purged (e.g., individual URL or wildcard pattern)
    # Example: purging all content under the '/static/' path
    content_to_purge = [
        '/stations/api/station-finder-data/',
        '/stations/api/v4/station-finder-data/'
    ]

    headers = {
        "Content-Type": "application/json",
        'Authorization': f'Bearer {cdn_access_key["access_token"]}',
    }
    purge_request_data = {
        'contentPaths': content_to_purge,
    }

    try:
        response = traced_request(
            POST_REQUEST,
            (
                config("DJANGO_APP_API_CDN_URL")
                +"subscriptions/"
                + config("DJANGO_APP_API_AD_SUBSCRIPTION_ID")
                + "/resourceGroups/"
                + config("DJANGO_APP_API_AD_RESOURCE_GROUP_NAME")
                + "/providers/Microsoft.Cdn/profiles/"
                + config("DJANGO_APP_API_AD_PROFILE_NAME")
                + "/afdEndpoints/"
                + config("DJANGO_APP_API_AD_ENDPOINT_NAME")
                + "/purge?api-version=2023-05-01"
            ),
            headers=headers,
            json=purge_request_data,
            timeout=REQUEST_API_TIMEOUT,
        )

        # Check the response status code to verify the success of the purge request
        if response.status_code == 202:
            print(CDN_SUCCESS_MESSAGE)
        else:
            print(f'{CDN_FAIL_MESSAGE_STRING} {response.status_code}*******')
            print(response.text)

    except requests.exceptions.RequestException as error:
        print(f'{CDN_ERROR_MESSAGE_STRING} {error}')
