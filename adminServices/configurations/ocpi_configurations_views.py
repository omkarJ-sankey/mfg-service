"""OCPI Configurations views"""
# Date - 23/04/2025
# File details-
#   Author      - Abhinav Shivalkar
#   Description - This file is mainly focused on APIs and views related
#                   to ocpi credentials configrutions data.
#   Name        - OCPI Configurations APIs
#   Modified by - Abhinav Shivalkar

# These are all the imports that we are exporting from different
# module's from project or library.


import json
import threading
from django.http.response import JsonResponse
from django.shortcuts import render
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.conf import settings
import traceback
from rest_framework import status
from decouple import config
import uuid

# pylint:disable=import-error
from sharedServices.decorators import authenticated_user
from sharedServices.common import (
    filter_url,
    check_integer,
)
from sharedServices.common_audit_trail_functions import (
    audit_data_formatter,
    add_audit_data,
)
from sharedServices.constants import (
    CONFIGURATION_CONST,
    GET_METHOD_ALLOWED,
    POST_METHOD_ALLOWED,
    BASE_CONFIG_CONST,
    AUDIT_ADD_CONSTANT,
    COMMON_ERRORS,
    ERROR_TEMPLATE_URL,
    YES,
    NO,
    CONTENT_TYPE_HEADER_KEY,
    JSON_DATA, 
    CPO_EXISTS_MESSAGE,
    INITIATE_HANDSHAKE_ENDPOINT,
    EMSP_ENDPOINT,
    UPDATE_EMSP_TOKEN_ENDPOINT,
    EMSP_TOKEN_KEY
)

from sharedServices.model_files.config_models import (
    BaseConfigurations,
)
from sharedServices.model_files.ocpi_credentials_models import (
    OCPICredentials,
    OCPICredentialsRole
)
from .views import remove_configurations_cached_data
from .app_level_constants import (
    BASE_CONF_ADDED_SUCCESSFULLY,
    BASE_CONF_UPDATED_SUCCESSFULLY,
    UNABLE_TO_DISPLAY_DETAILS,
    BASE_CONF_ADD_ERROR,
    OCPI_CONFIGURATIONS_TEMPLATE,
    OCPI_CREDENTIALS_ADDED_SUCCESSFULLY,
    OCPI_CREDENTIALS_CREATE_ERROR,
    UPDATE_OCPI_CONFIGURATIONS_TEMPLATE,
    OCPI_CREDENTIALS_UPDATE_ERROR,
    INVALID_NAME_ERROR,
    INVALID_TOKEN_ERROR

)

from .base_configurations_views import (
    add_frequently_used_base_configurations)

from django.forms.models import model_to_dict
from datetime import datetime
from sharedServices.sentry_tracers import traced_request, traced_request_with_retries
from sharedServices.constants import (
    CONFIGURATION_CONST,
    GET_METHOD_ALLOWED,
    POST_METHOD_ALLOWED,
    BASE_CONFIG_CONST,
    AUDIT_ADD_CONSTANT,
    COMMON_ERRORS,
    ERROR_TEMPLATE_URL,
    POST_REQUEST,
    REQUEST_API_TIMEOUT,
    OCPI_CONFIG_CONST,
    AUDIT_UPDATE_CONSTANT,
    OCPI_EMSP_NAME,
    OCPI_CREDENTIALS_CACHE_KEY
)

from sharedServices.common import (
    redis_connection,
    filter_url,
    get_node_secret
)

from .ocpi_configurations_helper import register_existing_users_to_cpo


CACHE_TTL = getattr(settings, "CACHE_TTL", DEFAULT_TIMEOUT)

def return_ocpi_configurations(filter_data = None):
    """this function returns ocpi configurations list"""
    if filter_data is not None:
        ocpi_config_roles = []
        
        for ocpi_config in OCPICredentialsRole.objects.filter(credential_id = filter_data):
            config_details = {
                "id": ocpi_config.id,
                "role": ocpi_config.role,
                "business_details": ocpi_config.business_details,
                "party_id": ocpi_config.party_id,
                "country_code": ocpi_config.country_code,
            }
            ocpi_config_roles.append(config_details)

    return [
        {
            "id": ocpi_config.id,
            "name": ocpi_config.name,
            "endpoint": ocpi_config.endpoint+"/versions",
            "party_id": ocpi_config.to_role.party_id if ocpi_config.to_role is not None else 'Not Available',
            "country_code": ocpi_config.to_role.country_code if ocpi_config.to_role is not None else 'Not Available',
            "status":ocpi_config.status
        }
        for ocpi_config in OCPICredentials.objects.select_related('to_role').all()
    ]



def serialize_model(instance):
    if instance is not None:
        data = model_to_dict(instance)
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data
    return None


def add_to_cache_ocpi_configurations(value,old_name = None):
    """this function is used to add ocpi config to cache"""

    key = OCPI_CREDENTIALS_CACHE_KEY
    key_data = {}
    # redis_connection.delete(key)
    data = redis_connection.get(key)
    def update_cache(data_json,value):
        if isinstance(value, tuple):
            value = value[0]

        if isinstance(value, str):
            try:
                value = json.loads(value)
                
                # from_id = value['from_role']
                to_id = value['to_role']
                
                from_role_data = OCPICredentials.objects.filter(name = "MFG")
                from_role_obj = OCPICredentialsRole.objects.filter(business_details = "MFG").first()
                value['from_role'] = serialize_model(from_role_obj)
                
                
                to_role_data = OCPICredentialsRole.objects.filter(id=to_id)
                to_role_obj = OCPICredentialsRole.objects.filter(id = to_id).first()
                value['to_role'] = serialize_model(to_role_obj)

            except json.JSONDecodeError as e:
                traceback.print_exc()
                print(f"Error parsing JSON: {e}")
        if isinstance(value, dict) and 'name' in value:
            data_json[value['name'].upper()] = value
            print("Successfully added to data_json with key:", value['name'].upper(),
                value['from_role'])
        else:
            print("Error: 'value' is not a valid dict or missing 'name'")
        return data_json
        
    if data is not None and data.decode() != {}:
        data_json = json.loads(data.decode())

        if isinstance(data_json, tuple):
            data_json = data_json[0]
        
        
        if isinstance(value,list):
            value = json.loads(value[0])
        if old_name is not None:
            if old_name.upper() in data_json:#hasattr(data_json,old_name.upper()):
                key_data = data_json[old_name.upper()]
                data_json.pop(old_name.upper())
        data_json = update_cache(data_json,value)
    else:
        data_json = {}
        back_offices = OCPICredentials.objects.filter(status = "Active")
        for back_office in back_offices:
            back_office_data = json.dumps(serialize_model(back_office))
            data_json = update_cache(data_json,back_office_data)

    # if add_operation:
    redis_connection.set(key, json.dumps(data_json))  




@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def ocpi_configurations_view(request):
    """list ocpi configuration view"""
    try:
        ocpi_configurations = return_ocpi_configurations()
        if request.method == "POST":
            data = json.loads(request.body)
            if (
                len(data["name"]) > 0
                and len(data["endpoint"]) > 0
                and len(data["ocpi_token"]) > 0
            ):
                can_be_added = True
                if OCPICredentials.objects.filter(
                    name=data["name"],
                    status = 'Active'
                ).first() is not None:
                    can_be_added = False
                    return JsonResponse(
                            {"status": False, "message": CPO_EXISTS_MESSAGE}
                        )
                if can_be_added:
                    unique_id = str(uuid.uuid4())
                    token = get_node_secret()
                    ocpi_data = {
                        "url": data["endpoint"],
                        "tokenA": data["ocpi_token"],
                        "name":data["name"].upper(),
                        "createdBy":request.user.full_name,
                        "tokenB":unique_id
                    }
                    print("request body : ",ocpi_data)
                    ocpi_details = OCPICredentials.objects.create(
                        name = data["name"].upper(),
                        endpoint = data["endpoint"].rsplit('/', 1)[0],
                        token_a = data["ocpi_token"],
                        status = "Initiated",
                        created_date=timezone.now(),
                        updated_date=timezone.now(),
                        updated_by=request.user.full_name,
                        emsp_token = unique_id
                    )
                    response_data = traced_request_with_retries(
                        POST_REQUEST,
                        EMSP_ENDPOINT+ INITIATE_HANDSHAKE_ENDPOINT,
                        headers={
                            CONTENT_TYPE_HEADER_KEY: JSON_DATA,
                            "Authorization": f"Token {token}"
                        },
                        data=json.dumps(ocpi_data),
                        timeout=REQUEST_API_TIMEOUT,
                    )
                    if response_data is None or response_data.status_code != status.HTTP_201_CREATED or json.loads(response_data.content.decode())["status_code"] != status.HTTP_200_OK :
                        print("Received Invalid response",json.loads(response_data.content.decode()))
                        OCPICredentials.objects.filter(id = ocpi_details.id).update(status = 'Failed')
                        messages.warning(request, OCPI_CREDENTIALS_CREATE_ERROR)
                        return JsonResponse(
                            {"status": 1, "message": OCPI_CREDENTIALS_CREATE_ERROR}
                        )
                        
                    full_response = json.loads(response_data.content.decode())
                                        
                    response = full_response.get('data', {})
                    print("Received Valid response ",response)
                    
                    cpo_token =  response['response_cpo']['token']
                    
                    ocpi_config=OCPICredentials.objects.filter(
                        cpo_token = cpo_token,
                        name = data["name"],
                        status = 'Active'
                    ).first()
    
                    new_data = audit_data_formatter(
                        OCPI_CONFIG_CONST, ocpi_config.id
                    )

                    add_audit_data(
                        request.user,
                        f'{data["name"].strip()}',
                        f"{OCPI_CONFIG_CONST}-{ocpi_config.id}",
                        AUDIT_ADD_CONSTANT,
                        OCPI_CONFIG_CONST,
                        new_data,
                        None,
                    )

                    key = OCPI_CREDENTIALS_CACHE_KEY
                    data = redis_connection.get(key)
                    # back_office_name = data["name"].upper()
                    # register_existing_users_to_cpo(back_office_name)
                return JsonResponse(
                    {"status": 1, "message": OCPI_CREDENTIALS_ADDED_SUCCESSFULLY}
                )
            messages.warning(request, OCPI_CREDENTIALS_CREATE_ERROR)
        
        return render(
            request,
            OCPI_CONFIGURATIONS_TEMPLATE,
            {
                "ocpi_configurations": ocpi_configurations,
                "ocpi_add_credentials_url":"{% url 'addOCPIConfigurations' %}",
                "json_data": json.dumps(ocpi_configurations),
                "pagination_count": BaseConfigurations.objects.filter(
                    base_configuration_key="Pagination_page_rows"
                )
                .first()
                .base_configuration_value
                if BaseConfigurations.objects.filter(
                    base_configuration_key="Pagination_page_rows"
                ).first()
                else 10,
                "data_count": len(ocpi_configurations),
                "data": filter_url(
                    request.user.role_id.access_content.all(),
                    CONFIGURATION_CONST,
                ),
            },
        )
    except Exception as e:
        print("Exception is : ", e)
        traceback.print_exc()
        return render(request, ERROR_TEMPLATE_URL)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def update_ocpi_configuration_details(request,credentials_id):
    """update ocpi configuration view"""
    try:
        ocpi_configurations = return_ocpi_configurations(credentials_id)
        ocpi_details = OCPICredentials.objects.filter(id = credentials_id).first()
        ocpi_config_roles = []
        # back_office_details = OCPICredentialsRole.objects.filter(id = credentials_id)
        for ocpi_config in OCPICredentialsRole.objects.filter(credential_id = credentials_id):
            config_details = {
                "id": ocpi_config.id,
                "role": ocpi_config.role,
                "business_details": ocpi_config.business_details,
                "party_id": ocpi_config.party_id,
                "country_code": ocpi_config.country_code,
            }
            ocpi_config_roles.append(config_details)
        old_name = ocpi_details.name
        prev_data = {
            "name":ocpi_details.name,
            "token":ocpi_details.emsp_token,
            "status":ocpi_details.status
        }
        # OCPICredentialsRole.objects.filter(credentials_id = credentials_id)
        if request.method == "POST":

            data = json.loads(request.body)
            ocpi_element = OCPICredentials.objects.filter(id=credentials_id).first()
            old_config_data = audit_data_formatter(
                OCPI_CONFIG_CONST, credentials_id
            )
            if "status" in data and len(data["status"])>0:
                print("updating status")
                ocpi_element.status = data['status']
                ocpi_element.update_date = timezone.now()
                ocpi_element.updated_by=request.user.full_name
                ocpi_element.save()
            
            if ("name" in data and (data["name"] is None or data["name"] == '')) :
                print("Error in updating name ")
                messages.warning(request, INVALID_NAME_ERROR)
                return render(
                    request,
                    OCPI_CONFIGURATIONS_TEMPLATE,
                    {
                        "ocpi_configurations": ocpi_configurations,
                        "ocpi_add_credentials_url":"{% url 'addOCPIConfigurations' %}",
                        "json_data": json.dumps(ocpi_configurations),
                        "pagination_count": BaseConfigurations.objects.filter(
                            base_configuration_key="Pagination_page_rows"
                        )
                        .first()
                        .base_configuration_value
                        if BaseConfigurations.objects.filter(
                            base_configuration_key="Pagination_page_rows"
                        ).first()
                        else 10,
                        "data_count": len(ocpi_configurations),
                        "data": filter_url(
                            request.user.role_id.access_content.all(),
                            CONFIGURATION_CONST,
                        ),
                    },
                )
            
            if "name" in data and len(data["name"])>0:
                print("updating name")
                ocpi_element.name = data["name"]
                ocpi_element.save()
            
            if "token" in data and data["token"] not in [None, "None", ""] and len(data["token"])>0 and data["token"] != ocpi_details.emsp_token:
                token = get_node_secret()
                print("updating token")
                ocpi_data = {
                        "url": data["endpoint"],
                        "cpoToken": data["cpo_token"],
                        "emspToken": data["token"],
                    }
                response_data = traced_request_with_retries(
                    POST_REQUEST,
                    EMSP_ENDPOINT + UPDATE_EMSP_TOKEN_ENDPOINT,
                    headers={
                        CONTENT_TYPE_HEADER_KEY: JSON_DATA,
                        "Authorization": f"Token {token}"
                    },
                    data=json.dumps(ocpi_data),
                    timeout=REQUEST_API_TIMEOUT,
                )
                if response_data is None or response_data.status_code != status.HTTP_201_CREATED or json.loads(response_data.content.decode())["status_code"] != status.HTTP_200_OK:
                # if response_data is None or response_data.status_code != status.HTTP_201_CREATED :
                    ocpi_element.save()
           
                    messages.warning(request, OCPI_CREDENTIALS_UPDATE_ERROR)
                    return render(
                        request,
                        OCPI_CONFIGURATIONS_TEMPLATE,
                        {
                            "ocpi_configurations": ocpi_configurations,
                            "ocpi_add_credentials_url":"{% url 'addOCPIConfigurations' %}",
                            "json_data": json.dumps(ocpi_configurations),
                            "pagination_count": BaseConfigurations.objects.filter(
                                base_configuration_key="Pagination_page_rows"
                            )
                            .first()
                            .base_configuration_value
                            if BaseConfigurations.objects.filter(
                                base_configuration_key="Pagination_page_rows"
                            ).first()
                            else 10,
                            "data_count": len(ocpi_configurations),
                            "data": filter_url(
                                request.user.role_id.access_content.all(),
                                CONFIGURATION_CONST,
                            ),
                        },
                    )
                ocpi_element.emsp_token = data["token"]
            ocpi_element.save()
            ocpi_config_data=json.dumps(serialize_model(ocpi_element))
            add_to_cache_ocpi_configurations(
                ocpi_config_data, old_name
            )
            updated_data = audit_data_formatter(
                OCPI_CONFIG_CONST, credentials_id
            )
            add_audit_data(
                request.user,
                f'{data["name"].strip()}',
                f"{OCPI_CONFIG_CONST}-{credentials_id}",
                AUDIT_UPDATE_CONSTANT,
                OCPI_CONFIG_CONST,
                updated_data,
                old_config_data,
            )
            
            return JsonResponse(
                {"status": 1, "message": BASE_CONF_UPDATED_SUCCESSFULLY}
            )
        
        else:
            return render(
                request,
                UPDATE_OCPI_CONFIGURATIONS_TEMPLATE,
                {
                    "ocpi_configuration": ocpi_configurations,
                    "credentials_id": credentials_id,
                    "ocpi_details":ocpi_details,
                    "prev_data":json.dumps(prev_data),
                    "json_data": json.dumps(ocpi_configurations),
                    "pagination_count": BaseConfigurations.objects.filter(
                        base_configuration_key="Pagination_page_rows"
                    )
                    .first()
                    .base_configuration_value
                    if BaseConfigurations.objects.filter(
                        base_configuration_key="Pagination_page_rows"
                    ).first()
                    else 10,
                    "ocpi_config_roles":ocpi_config_roles,
                    "data": filter_url(
                        request.user.role_id.access_content.all(),
                        CONFIGURATION_CONST,
                    ),
                },
            )
    except Exception as e:
        traceback.print_exc()
        return render(request, ERROR_TEMPLATE_URL)