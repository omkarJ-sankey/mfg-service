# myapp/decorators.py

from functools import wraps
from rest_framework.response import Response
from django.http import JsonResponse

from rest_framework import status
from django.utils.encoding import force_str
from django.conf import settings

from sharedServices.model_files.config_models import BaseConfigurations
from sharedServices.common import redis_connection  
from decouple import config as env_config

CACHE_UPDATE_TOKEN_KEY = "CACHE_UPDATE_TOKEN_KEY"  

def get_valid_token():
    token = redis_connection.get(CACHE_UPDATE_TOKEN_KEY)
    if token:
        return force_str(token)
    
    config = BaseConfigurations.objects.filter(base_configuration_key=CACHE_UPDATE_TOKEN_KEY).first()
    if config:
        token = config.base_configuration_value
        redis_connection.set(CACHE_UPDATE_TOKEN_KEY, token)
        return token

    # Fallback to env
    
    token = env_config('DJANGO_APP_CACHE_UPDATE_TOKEN')
    redis_connection.set(CACHE_UPDATE_TOKEN_KEY, token)
    return token


def token_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Token '):
            return JsonResponse(
                {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "status": False,
                    "message": "Invalid Authorization Header",
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        token = auth_header.split(' ')[1].strip()
        valid_token = get_valid_token()

        if token != valid_token:
            return JsonResponse(
                {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "status": False,
                    "message": "Invalid Token",
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        return view_func(request, *args, **kwargs)

    return _wrapped_view
